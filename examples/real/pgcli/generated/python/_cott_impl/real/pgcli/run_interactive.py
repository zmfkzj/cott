import csv
import html
import io
import json
import os
import shlex
import socket
import subprocess
import sys
import tempfile
import time
from typing import Final, cast

import psycopg
import psycopg.errors
from psycopg.conninfo import make_conninfo
from cott_runtime import UNIT, Err, Ok, Result, Some, Unit
from real.pgcli_types import ClientError, ClientError_CatalogFailed, ClientError_EditorFailed, ClientError_FavoriteFailed, ClientError_HistoryFailed, ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_NotificationFailed, ClientError_PagerFailed, ClientError_QueryFailed, ClientError_TerminalFailed, ClientError_TransactionFailed, ConnectionPlan, FavoriteStore, HistoryPolicy, InteractiveRequest, SshSettings, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical, TransactionMode, TransactionMode_AutoCommit, TransactionMode_Manual

_TUNNEL_TIMEOUT_S: Final[float] = 15.0
_NULL_TEXT: Final[str] = "<null>"
_HELP: Final[str] = "\\q quit | \\timing toggle timing | \\T <format> set output format | \\dt list tables | \\e edit buffer | \\f <name> run favorite | \\fs <name> <sql> save favorite | \\fd <name> delete favorite | \\fl list favorites"


def _path_set(value: object) -> bool:
    return str(value) not in ("", ".")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        address = cast(tuple[object, ...], sock.getsockname())
        port = address[1]
        if not isinstance(port, int):
            raise OSError("unexpected socket address")
        return port


def _open_tunnel(ssh: SshSettings, remote_host: str, remote_port: str) -> Result[tuple[subprocess.Popen[bytes], int], ClientError]:
    try:
        local_port = _free_port()
    except OSError as exc:
        return Err(error=ClientError_QueryFailed(message=f"ssh tunnel could not reserve a port: {exc.strerror}"))
    argv = ["ssh", "-N", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ExitOnForwardFailure=yes", "-L", f"127.0.0.1:{local_port}:{remote_host}:{remote_port or '5432'}", "-p", str(ssh.port)]
    if _path_set(ssh.private_key):
        argv += ["-i", os.fspath(ssh.private_key), "-o", "IdentitiesOnly=yes"]
    target = f"{ssh.user}@{ssh.host}" if ssh.user else ssh.host
    argv += ["--", target]
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return Err(error=ClientError_QueryFailed(message=f"ssh tunnel could not start: {exc.strerror}"))
    deadline = time.monotonic() + _TUNNEL_TIMEOUT_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return Err(error=ClientError_QueryFailed(message=f"ssh tunnel exited with status {proc.returncode}"))
        try:
            with socket.create_connection(("127.0.0.1", local_port), timeout=0.5):
                return Ok(value=(proc, local_port))
        except OSError:
            time.sleep(0.1)
    proc.terminate()
    proc.wait()
    return Err(error=ClientError_QueryFailed(message="ssh tunnel timed out"))


def _connect(plan: ConnectionPlan, mode: TransactionMode, tunnel_port: int) -> Result[psycopg.Connection[tuple[object, ...]], ClientError]:
    settings = plan.settings
    params: dict[str, str] = {}
    if settings.host:
        params["host"] = settings.host
    if settings.port:
        params["port"] = settings.port
    if settings.user:
        params["user"] = settings.user
    if settings.password:
        params["password"] = settings.password
    if settings.database:
        params["dbname"] = settings.database
    if plan.tls.mode:
        params["sslmode"] = plan.tls.mode
    if _path_set(plan.tls.root_certificate):
        params["sslrootcert"] = os.fspath(plan.tls.root_certificate)
    if _path_set(plan.tls.certificate):
        params["sslcert"] = os.fspath(plan.tls.certificate)
    if _path_set(plan.tls.private_key):
        params["sslkey"] = os.fspath(plan.tls.private_key)
    if tunnel_port > 0:
        # host stays the logical server name so TLS verifies it; traffic goes through the tunnel.
        params["hostaddr"] = "127.0.0.1"
        params["port"] = str(tunnel_port)
    try:
        conninfo = make_conninfo(plan.dsn, **params)
        conn = psycopg.connect(conninfo, autocommit=isinstance(mode, TransactionMode_AutoCommit))
    except psycopg.Error as exc:
        return Err(error=ClientError_QueryFailed(message=f"connection failed (SQLSTATE {exc.sqlstate or 'none'})"))
    if not isinstance(mode, TransactionMode_AutoCommit) and not isinstance(mode, TransactionMode_Manual):
        try:
            conn.read_only = True
        except psycopg.Error as exc:
            conn.close()
            return Err(error=ClientError_TransactionFailed(message=str(exc).strip()))
    return Ok(value=conn)


def _text(value: object) -> str:
    if value is None:
        return _NULL_TEXT
    return str(value)


def _aligned(headers: list[str], rows: list[tuple[object, ...]]) -> str:
    cells = [[_text(v) for v in row] for row in rows]
    widths = [len(h) for h in headers]
    for row_cells in cells:
        for i, cell in enumerate(row_cells):
            widths[i] = max(widths[i], len(cell))
    lines = [" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)), "-+-".join("-" * w for w in widths)]
    for row_cells in cells:
        lines.append(" | ".join(c.ljust(widths[i]) for i, c in enumerate(row_cells)))
    lines.append(f"({len(rows)} row{'' if len(rows) == 1 else 's'})")
    return "\n".join(lines)


def _delimited(headers: list[str], rows: list[tuple[object, ...]], delimiter: str) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if v is None else str(v) for v in row])
    return buffer.getvalue().rstrip("\n")


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        items = cast(list[object] | tuple[object, ...], value)
        return [_json_value(v) for v in items]
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {str(k): _json_value(v) for k, v in mapping.items()}
    return str(value)


def _latex_escape(text: str) -> str:
    out: list[str] = []
    for ch in text:
        if ch == "\\":
            out.append("\\textbackslash{}")
        elif ch in "&%$#_{}":
            out.append("\\" + ch)
        elif ch == "~":
            out.append("\\textasciitilde{}")
        elif ch == "^":
            out.append("\\textasciicircum{}")
        else:
            out.append(ch)
    return "".join(out)


def _render(fmt: TableFormat, headers: list[str], rows: list[tuple[object, ...]]) -> str:
    if isinstance(fmt, TableFormat_Aligned):
        return _aligned(headers, rows)
    if isinstance(fmt, TableFormat_Csv):
        return _delimited(headers, rows, ",")
    if isinstance(fmt, TableFormat_Tsv):
        return _delimited(headers, rows, "\t")
    if isinstance(fmt, TableFormat_Json):
        return json.dumps([{h: _json_value(v) for h, v in zip(headers, row)} for row in rows], indent=2, ensure_ascii=False)
    if isinstance(fmt, TableFormat_JsonLines):
        return "\n".join(json.dumps({h: _json_value(v) for h, v in zip(headers, row)}, ensure_ascii=False) for row in rows)
    if isinstance(fmt, TableFormat_Html):
        head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
        body = "".join("<tr>" + "".join(f"<td>{html.escape(_text(v))}</td>" for v in row) + "</tr>\n" for row in rows)
        return f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}</tbody>\n</table>"
    if isinstance(fmt, TableFormat_Latex):
        lines = ["\\begin{tabular}{" + "l" * len(headers) + "}", "\\hline", " & ".join(_latex_escape(h) for h in headers) + " \\\\", "\\hline"]
        lines += [" & ".join(_latex_escape(_text(v)) for v in row) + " \\\\" for row in rows]
        lines += ["\\hline", "\\end{tabular}"]
        return "\n".join(lines)
    if isinstance(fmt, TableFormat_Markdown):
        lines = ["| " + " | ".join(h.replace("|", "\\|") for h in headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
        lines += ["| " + " | ".join(_text(v).replace("|", "\\|").replace("\n", " ") for v in row) + " |" for row in rows]
        return "\n".join(lines)
    width = max((len(h) for h in headers), default=0)
    blocks: list[str] = []
    for index, row in enumerate(rows, start=1):
        blocks.append(f"-[ RECORD {index} ]" + "-" * 10)
        blocks += [f"{h.ljust(width)} | {_text(v)}" for h, v in zip(headers, row)]
    return "\n".join(blocks) if blocks else "(0 rows)"


def _parse_format(name: str) -> TableFormat | None:
    key = name.strip().lower().replace("-", "").replace("_", "")
    if key == "aligned":
        return TableFormat_Aligned()
    if key == "csv":
        return TableFormat_Csv()
    if key == "tsv":
        return TableFormat_Tsv()
    if key == "json":
        return TableFormat_Json()
    if key == "jsonlines":
        return TableFormat_JsonLines()
    if key == "html":
        return TableFormat_Html()
    if key == "latex":
        return TableFormat_Latex()
    if key == "markdown":
        return TableFormat_Markdown()
    if key == "vertical":
        return TableFormat_Vertical()
    return None


def _emit(text: str, pager: bool) -> Result[Unit, ClientError]:
    if not text:
        return Ok(value=UNIT)
    if pager and sys.stdout.isatty():
        try:
            command = shlex.split(os.environ.get("PAGER", "") or "less -SRXF")
            completed = subprocess.run(command, input=(text + "\n").encode(), check=False)
        except (OSError, ValueError) as exc:
            return Err(error=ClientError_PagerFailed(message=str(exc)))
        if completed.returncode != 0:
            return Err(error=ClientError_PagerFailed(message=f"pager exited with status {completed.returncode}"))
        return Ok(value=UNIT)
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except OSError as exc:
        return Err(error=ClientError_TerminalFailed(message=str(exc)))
    return Ok(value=UNIT)


def _query_error(exc: psycopg.Error) -> ClientError:
    message = str(exc).strip()
    if isinstance(exc, psycopg.errors.SyntaxError):
        return ClientError_InvalidSql(message=message)
    if isinstance(exc, (psycopg.errors.InFailedSqlTransaction, psycopg.errors.ActiveSqlTransaction, psycopg.errors.NoActiveSqlTransaction, psycopg.errors.ReadOnlySqlTransaction)):
        return ClientError_TransactionFailed(message=message)
    return ClientError_QueryFailed(message=message)


def _drain_notifications(conn: psycopg.Connection[tuple[object, ...]]) -> Result[Unit, ClientError]:
    lines: list[str] = []
    try:
        for note in conn.notifies(timeout=0.0):
            lines.append(f'Asynchronous notification "{note.channel}" with payload "{note.payload}" received from server process with PID {note.pid}.')
    except psycopg.Error as exc:
        return Err(error=ClientError_NotificationFailed(message=str(exc).strip()))
    if not lines:
        return Ok(value=UNIT)
    try:
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
    except OSError as exc:
        return Err(error=ClientError_NotificationFailed(message=str(exc)))
    return Ok(value=UNIT)


def _execute(conn: psycopg.Connection[tuple[object, ...]], sql: str, fmt: TableFormat, timing: bool, pager: bool) -> Result[Unit, ClientError]:
    started = time.monotonic()
    outputs: list[str] = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql.encode())
            while True:
                if cur.description is not None:
                    headers = [column.name for column in cur.description]
                    outputs.append(_render(fmt, headers, cur.fetchall()))
                elif cur.statusmessage:
                    outputs.append(cur.statusmessage)
                if not cur.nextset():
                    break
    except psycopg.Error as exc:
        return Err(error=_query_error(exc))
    if timing:
        outputs.append(f"Time: {(time.monotonic() - started) * 1000.0:.3f} ms")
    emitted = _emit("\n".join(outputs), pager)
    if isinstance(emitted, Err):
        return emitted
    return _drain_notifications(conn)


def _catalog(conn: psycopg.Connection[tuple[object, ...]], limit: int) -> Result[list[tuple[object, ...]], ClientError]:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT table_schema, table_name, table_type FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name LIMIT %s", (limit,))
            rows = cur.fetchall()
        if not conn.autocommit:
            conn.rollback()
    except psycopg.Error as exc:
        return Err(error=ClientError_CatalogFailed(message=str(exc).strip()))
    return Ok(value=rows)


def _normalize_history(entries: list[tuple[str, str, int]], policy: HistoryPolicy) -> list[tuple[str, str, int]]:
    if policy.max_entries == 0:
        return []
    kept = entries
    if policy.unique:
        last: dict[tuple[str, str], int] = {}
        for index, entry in enumerate(entries):
            last[(entry[0], entry[1])] = index
        kept = [entry for index, entry in enumerate(entries) if last[(entry[0], entry[1])] == index]
    if len(kept) > policy.max_entries:
        kept = kept[len(kept) - policy.max_entries:]
    return list(kept)


def _load_history(policy: HistoryPolicy) -> Result[list[tuple[str, str, int]], ClientError]:
    if not _path_set(policy.path):
        return Ok(value=[])
    entries: list[tuple[str, str, int]] = []
    try:
        with open(policy.path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                decoded = cast(object, json.loads(line))
                if not isinstance(decoded, dict):
                    return Err(error=ClientError_HistoryFailed(path=policy.path, message="malformed history entry"))
                item = cast(dict[object, object], decoded)
                if "database" not in item or "sql" not in item or "executed_at_ms" not in item:
                    return Err(error=ClientError_HistoryFailed(path=policy.path, message="malformed history entry"))
                database, sql, executed = item["database"], item["sql"], item["executed_at_ms"]
                if not isinstance(database, str) or not isinstance(sql, str) or not isinstance(executed, int) or isinstance(executed, bool):
                    return Err(error=ClientError_HistoryFailed(path=policy.path, message="malformed history entry"))
                entries.append((database, sql, executed))
    except FileNotFoundError:
        return Ok(value=[])
    except (OSError, ValueError) as exc:
        return Err(error=ClientError_HistoryFailed(path=policy.path, message=str(exc)))
    return Ok(value=_normalize_history(entries, policy))


def _atomic_write(path: object, text: str) -> str:
    target = os.path.abspath(str(path))
    folder = os.path.dirname(target)
    temp = os.path.join(folder, f".pgcli-{os.getpid()}-{time.monotonic_ns()}.tmp")
    try:
        os.makedirs(folder, exist_ok=True)
        try:
            with open(temp, "x", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(temp, target)
        except BaseException:
            if os.path.exists(temp):
                os.unlink(temp)
            raise
    except OSError as exc:
        return str(exc)
    return ""


def _save_history(entries: list[tuple[str, str, int]], policy: HistoryPolicy) -> Result[Unit, ClientError]:
    if not _path_set(policy.path):
        return Ok(value=UNIT)
    text = "".join(json.dumps({"database": d, "sql": s, "executed_at_ms": t}, ensure_ascii=False) + "\n" for d, s, t in entries)
    failure = _atomic_write(policy.path, text)
    if failure:
        return Err(error=ClientError_HistoryFailed(path=policy.path, message=failure))
    return Ok(value=UNIT)


def _load_favorites(store: FavoriteStore) -> Result[dict[str, str], ClientError]:
    if not _path_set(store.path):
        return Ok(value={})
    try:
        with open(store.path, encoding="utf-8") as handle:
            decoded = cast(object, json.load(handle))
    except FileNotFoundError:
        return Ok(value={})
    except (OSError, ValueError):
        return Err(error=ClientError_FavoriteFailed(name=""))
    if not isinstance(decoded, dict):
        return Err(error=ClientError_FavoriteFailed(name=""))
    data = cast(dict[object, object], decoded)
    favorites: dict[str, str] = {}
    for name, sql in data.items():
        if not isinstance(name, str):
            return Err(error=ClientError_FavoriteFailed(name=""))
        if not isinstance(sql, str):
            return Err(error=ClientError_FavoriteFailed(name=name))
        favorites[name] = sql
    return Ok(value=favorites)


def _save_favorites(store: FavoriteStore, favorites: dict[str, str], name: str) -> Result[Unit, ClientError]:
    if not _path_set(store.path):
        return Ok(value=UNIT)
    if _atomic_write(store.path, json.dumps(favorites, indent=2, ensure_ascii=False) + "\n"):
        return Err(error=ClientError_FavoriteFailed(name=name))
    return Ok(value=UNIT)


def _edit(initial: str) -> Result[str, ClientError]:
    editor = os.environ.get("VISUAL", "") or os.environ.get("EDITOR", "") or "vi"
    try:
        fd, temp = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(initial)
            completed = subprocess.run(shlex.split(editor) + [temp], check=False)
            if completed.returncode != 0:
                return Err(error=ClientError_EditorFailed(message=f"editor exited with status {completed.returncode}"))
            with open(temp, encoding="utf-8") as handle:
                return Ok(value=handle.read())
        finally:
            os.unlink(temp)
    except (OSError, ValueError) as exc:
        return Err(error=ClientError_EditorFailed(message=str(exc)))


def _read_statement(multiline: bool, database: str) -> Result[str | None, ClientError]:
    lines: list[str] = []
    interactive = sys.stdin.isatty()
    while True:
        prompt = f"{database}> " if not lines else "-> "
        try:
            if interactive:
                line = input(prompt)
            else:
                raw = sys.stdin.readline()
                if not raw:
                    raise EOFError
                line = raw.rstrip("\n")
        except EOFError:
            joined = "\n".join(lines).strip()
            return Ok(value=joined or None)
        except KeyboardInterrupt:
            lines = []
            sys.stdout.write("\n")
            continue
        except OSError as exc:
            return Err(error=ClientError_TerminalFailed(message=str(exc)))
        if not lines and not line.strip():
            continue
        lines.append(line)
        text = "\n".join(lines).strip()
        if not multiline or text.startswith("\\") or text.endswith(";"):
            return Ok(value=text)


def _report(error: ClientError) -> Result[Unit, ClientError]:
    try:
        sys.stderr.write(f"error: {error}\n")
        sys.stderr.flush()
    except OSError as exc:
        return Err(error=ClientError_TerminalFailed(message=str(exc)))
    return Ok(value=UNIT)


def _session(request: InteractiveRequest, conn: psycopg.Connection[tuple[object, ...]], history: list[tuple[str, str, int]], favorites: dict[str, str]) -> Result[Unit, ClientError]:
    options = request.options
    database = conn.info.dbname
    fmt: TableFormat = options.format
    timing = options.timing
    buffer = ""
    pending: list[str] = [request.initial_sql.strip()] if request.initial_sql.strip() else []
    while True:
        if pending:
            text = pending.pop(0)
        elif request.execute_once:
            return Ok(value=UNIT)
        else:
            read = _read_statement(options.multiline, database)
            if isinstance(read, Err):
                return read
            if read.value is None:
                return Ok(value=UNIT)
            text = read.value
        outcome: Result[Unit, ClientError] = Ok(value=UNIT)
        if text.startswith("\\"):
            parts = text.rstrip(";").split(maxsplit=2)
            command = parts[0]
            if command in ("\\q", "\\quit"):
                return Ok(value=UNIT)
            if command == "\\?":
                outcome = _emit(_HELP, False)
            elif command == "\\timing":
                timing = not timing
                outcome = _emit(f"Timing is {'on' if timing else 'off'}.", False)
            elif command == "\\T" and len(parts) == 2:
                parsed = _parse_format(parts[1])
                if parsed is None:
                    outcome = Err(error=ClientError_InvalidCommand(source=text))
                else:
                    fmt = parsed
            elif command == "\\dt" and len(parts) == 1:
                tables = _catalog(conn, options.catalog_limit)
                if isinstance(tables, Err):
                    outcome = tables
                else:
                    outcome = _emit(_render(fmt, ["schema", "name", "type"], tables.value), options.pager)
            elif command == "\\e":
                edited = _edit(buffer)
                if isinstance(edited, Err):
                    outcome = edited
                elif edited.value.strip():
                    pending.append(edited.value.strip())
            elif command == "\\f" and len(parts) == 2:
                if parts[1] in favorites:
                    pending.append(favorites[parts[1]])
                else:
                    outcome = Err(error=ClientError_FavoriteFailed(name=parts[1]))
            elif command == "\\fs" and len(parts) == 3:
                if parts[1] not in favorites and len(favorites) >= options.favorites.max_entries:
                    outcome = Err(error=ClientError_FavoriteFailed(name=parts[1]))
                else:
                    favorites[parts[1]] = parts[2]
                    outcome = _save_favorites(options.favorites, favorites, parts[1])
            elif command == "\\fd" and len(parts) == 2:
                if favorites.pop(parts[1], None) is None:
                    outcome = Err(error=ClientError_FavoriteFailed(name=parts[1]))
                else:
                    outcome = _save_favorites(options.favorites, favorites, parts[1])
            elif command == "\\fl" and len(parts) == 1:
                listing: list[tuple[object, ...]] = [(k, v) for k, v in sorted(favorites.items())]
                outcome = _emit(_render(fmt, ["name", "query"], listing), options.pager)
            else:
                outcome = Err(error=ClientError_InvalidCommand(source=text))
        else:
            buffer = text
            history.append((database, text, time.time_ns() // 1_000_000))
            history[:] = _normalize_history(history, options.history)
            saved = _save_history(history, options.history)
            if isinstance(saved, Err):
                return saved
            outcome = _execute(conn, text, fmt, timing, options.pager)
        if isinstance(outcome, Err):
            if request.execute_once:
                return outcome
            reported = _report(outcome.error)
            if isinstance(reported, Err):
                return reported


def run_interactive(request: InteractiveRequest) -> Result[Unit, ClientError]:
    options = request.options
    history_result = _load_history(options.history)
    if isinstance(history_result, Err):
        return history_result
    history = history_result.value
    favorites_result = _load_favorites(options.favorites)
    if isinstance(favorites_result, Err):
        return favorites_result
    favorites = favorites_result.value
    if request.execute_once and not request.initial_sql.strip():
        return Err(error=ClientError_InvalidCommand(source=request.initial_sql))

    tunnel: subprocess.Popen[bytes] | None = None
    tunnel_port = 0
    ssh = options.connection.ssh
    if isinstance(ssh, Some):
        opened = _open_tunnel(ssh.value, options.connection.settings.host or "localhost", options.connection.settings.port)
        if isinstance(opened, Err):
            return opened
        tunnel, tunnel_port = opened.value
    try:
        connected = _connect(options.connection, options.transaction, tunnel_port)
        if isinstance(connected, Err):
            return connected
        conn = connected.value
        try:
            return _session(request, conn, history, favorites)
        finally:
            conn.close()
    finally:
        if tunnel is not None:
            tunnel.terminate()
            tunnel.wait()
