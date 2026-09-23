import csv
import fnmatch
import io
import json
import time
from pathlib import Path
from typing import Final, cast

import psycopg
from psycopg import sql as pgsql
from psycopg.conninfo import make_conninfo

from cott_runtime import Err, Ok, Result, Some
from real.pgcli_types import Catalog, ClientError, ClientError_EditorFailed, ClientError_ExportFailed, ClientError_FavoriteFailed, ClientError_HistoryFailed, ClientError_ImportFailed, ClientError_InvalidCommand, ClientError_NotificationFailed, ClientError_QueryFailed, ClientError_TransactionFailed, CommandInvocation, CommandResult, InputBuffer, MetaCommand_ClearOutput, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery, MetaCommand_Describe, MetaCommand_Echo, MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_Expanded, MetaCommand_Favorite, MetaCommand_Help, MetaCommand_History, MetaCommand_ListDataTypes, MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains, MetaCommand_ListExtensions, MetaCommand_ListFavorites, MetaCommand_ListForeignTables, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListNotifications, MetaCommand_ListPrivileges, MetaCommand_ListRoles, MetaCommand_ListSchemas, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews, MetaCommand_NamedQuery, MetaCommand_Password, MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho, MetaCommand_Quit, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery, MetaCommand_SetFormat, MetaCommand_SetLogFile, MetaCommand_SetOptions, MetaCommand_SetOutput, MetaCommand_SetPager, MetaCommand_Shell, MetaCommand_ShowFunction, MetaCommand_SqlHelp, MetaCommand_Timing, MetaCommand_VerboseErrors, MetaCommand_Watch, MetaCommand_WriteBuffer, SessionOptions, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical, TransactionMode_AutoCommit, TransactionMode_Manual

_HELP: Final[str] = "\\q quit | \\dt tables | \\dv views | \\df functions | \\dn schemas | \\du roles | \\l databases | \\d describe | \\e edit | \\g execute | \\p print | \\r reset | \\w write | \\i read | \\n named queries | \\T format | \\timing | \\x expanded | \\copy | \\echo | \\o output | \\log-file | \\pager | \\history | \\conninfo | \\c connect"
_REDACTED: Final[str] = "********"


def _buf(text: str, cursor: int, multiline: bool) -> InputBuffer:
    return InputBuffer(text=text, cursor=min(max(cursor, 0), len(text)), multiline=multiline)


def _ok(buffer: InputBuffer, output: str, quit: bool) -> Result[CommandResult, ClientError]:
    return Ok(value=CommandResult(buffer=_buf(buffer.text, buffer.cursor, buffer.multiline), output=output, quit=quit))


def _is_set(p: Path) -> bool:
    return str(p) not in ("", ".")


def _safe(exc: BaseException, options: SessionOptions) -> str:
    message = str(exc).strip() or "error"
    password = options.connection.settings.password
    if password:
        message = message.replace(password, _REDACTED)
    return message


def _matches(pattern: str, name: str) -> bool:
    p = pattern.strip()
    if not p:
        return True
    return fnmatch.fnmatchcase(name, p.replace("%", "*"))


def _like(pattern: str) -> str:
    p = pattern.strip()
    return p.replace("*", "%").replace("?", "_") if p else "%"


def _format_name(fmt: TableFormat) -> str:
    if isinstance(fmt, TableFormat_Aligned):
        return "aligned"
    if isinstance(fmt, TableFormat_Csv):
        return "csv"
    if isinstance(fmt, TableFormat_Tsv):
        return "tsv"
    if isinstance(fmt, TableFormat_Json):
        return "json"
    if isinstance(fmt, TableFormat_JsonLines):
        return "jsonlines"
    if isinstance(fmt, TableFormat_Html):
        return "html"
    if isinstance(fmt, TableFormat_Latex):
        return "latex"
    if isinstance(fmt, TableFormat_Markdown):
        return "markdown"
    return "vertical"


def _render(headers: list[str], rows: list[list[str]], fmt: TableFormat) -> str:
    if isinstance(fmt, TableFormat_Csv) or isinstance(fmt, TableFormat_Tsv):
        out = io.StringIO()
        writer = csv.writer(out, delimiter="\t" if isinstance(fmt, TableFormat_Tsv) else ",", lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)
        return out.getvalue().rstrip("\n")
    if isinstance(fmt, TableFormat_Json):
        return json.dumps([dict(zip(headers, r)) for r in rows])
    if isinstance(fmt, TableFormat_JsonLines):
        return "\n".join(json.dumps(dict(zip(headers, r))) for r in rows)
    if isinstance(fmt, TableFormat_Html):
        head = "".join(f"<th>{h}</th>" for h in headers)
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table><tr>{head}</tr>{body}</table>"
    if isinstance(fmt, TableFormat_Latex):
        lines = ["\\begin{tabular}{" + "l" * len(headers) + "}", " & ".join(headers) + " \\\\", "\\hline"]
        lines.extend(" & ".join(r) + " \\\\" for r in rows)
        lines.append("\\end{tabular}")
        return "\n".join(lines)
    if isinstance(fmt, TableFormat_Markdown):
        lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
        lines.extend("| " + " | ".join(r) + " |" for r in rows)
        return "\n".join(lines)
    if isinstance(fmt, TableFormat_Aligned):
        widths = [len(h) for h in headers]
        for r in rows:
            for i, c in enumerate(r):
                widths[i] = max(widths[i], len(c))
        lines = [" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)), "-+-".join("-" * w for w in widths)]
        lines.extend(" | ".join(c.ljust(widths[i]) for i, c in enumerate(r)) for r in rows)
        lines.append(f"({len(rows)} row{'' if len(rows) == 1 else 's'})")
        return "\n".join(lines)
    width = max((len(h) for h in headers), default=0)
    blocks: list[str] = []
    for n, r in enumerate(rows, 1):
        blocks.append(f"-[ RECORD {n} ]" + "\n" + "\n".join(f"{h.ljust(width)} | {c}" for h, c in zip(headers, r)))
    return "\n".join(blocks)


def _connect(options: SessionOptions, database: str) -> psycopg.Connection:
    plan = options.connection
    if isinstance(plan.ssh, Some):
        raise psycopg.OperationalError("SSH tunnelling is not available in this client")
    s = plan.settings
    params: dict[str, str] = {}
    for key, value in (("host", s.host), ("port", s.port), ("user", s.user), ("password", s.password), ("dbname", database or s.database), ("sslmode", plan.tls.mode)):
        if value:
            params[key] = value
    for key, p in (("sslrootcert", plan.tls.root_certificate), ("sslcert", plan.tls.certificate), ("sslkey", plan.tls.private_key)):
        if _is_set(Path(p)):
            params[key] = str(p)
    conninfo = make_conninfo(plan.dsn, **params)
    if isinstance(options.transaction, TransactionMode_AutoCommit):
        return psycopg.connect(conninfo, autocommit=True)
    conn = psycopg.connect(conninfo, autocommit=False)
    if not isinstance(options.transaction, TransactionMode_Manual):
        conn.read_only = True
    return conn


def _query(options: SessionOptions, text: str, params: list[str]) -> Result[tuple[list[str], list[list[str]], str], ClientError]:
    try:
        conn = _connect(options, "")
    except (psycopg.Error, OSError) as exc:
        return Err(error=ClientError_QueryFailed(message=_safe(exc, options)))
    try:
        headers: list[str] = []
        rows: list[list[str]] = []
        try:
            cur = conn.execute(text.encode(), params if params else None)
            if cur.description is not None:
                headers = [c.name for c in cur.description]
                for record in cur.fetchall():
                    values = cast(tuple[object, ...], record)
                    rows.append(["" if v is None else str(v) for v in values])
            status = cur.statusmessage or ""
        except psycopg.Error as exc:
            return Err(error=ClientError_QueryFailed(message=_safe(exc, options)))
        try:
            if not conn.autocommit:
                conn.commit()
        except psycopg.Error as exc:
            return Err(error=ClientError_TransactionFailed(message=_safe(exc, options)))
        return Ok(value=(headers, rows, status))
    finally:
        conn.close()


def _append_history(options: SessionOptions, text: str) -> Result[None, ClientError]:
    path = Path(options.history.path)
    if not _is_set(path) or options.history.max_entries == 0:
        return Ok(value=None)
    entry = {"database": options.connection.settings.database, "sql": text, "executed_at_ms": time.time_ns() // 1_000_000}
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        return Err(error=ClientError_HistoryFailed(path=options.history.path, message=str(exc)))
    return Ok(value=None)


def _load_history(options: SessionOptions) -> Result[list[tuple[str, str]], ClientError]:
    policy = options.history
    path = Path(policy.path)
    entries: list[tuple[str, str]] = []
    if _is_set(path) and path.exists():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                parsed: object = json.loads(line)
                if not isinstance(parsed, dict):
                    raise ValueError("history entry is not an object")
                item = cast(dict[str, object], parsed)
                database = item.get("database")
                statement = item.get("sql")
                if not isinstance(database, str) or not isinstance(statement, str):
                    raise ValueError("history entry is missing database or sql")
                entries.append((database, statement))
        except (OSError, ValueError) as exc:
            return Err(error=ClientError_HistoryFailed(path=policy.path, message=str(exc)))
    if policy.unique:
        last: dict[tuple[str, str], int] = {e: i for i, e in enumerate(entries)}
        entries = [e for i, e in enumerate(entries) if last[e] == i]
    cap = policy.max_entries
    if cap == 0:
        return Ok(value=[])
    if cap < len(entries):
        return Ok(value=entries[len(entries) - cap:])
    return Ok(value=entries)


def _load_favorites(options: SessionOptions, name: str) -> Result[dict[str, str], ClientError]:
    path = Path(options.favorites.path)
    if not _is_set(path) or not path.exists():
        return Ok(value={})
    try:
        parsed: object = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("favorites file is not an object")
        data = cast(dict[object, object], parsed)
        favorites: dict[str, str] = {}
        for key, value in data.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("favorites entries must be strings")
            favorites[key] = value
        return Ok(value=favorites)
    except (OSError, ValueError) as exc:
        return Err(error=ClientError_FavoriteFailed(name=name or str(exc)))


def _save_favorites(options: SessionOptions, favorites: dict[str, str], name: str) -> Result[None, ClientError]:
    path = Path(options.favorites.path)
    if not _is_set(path):
        return Err(error=ClientError_FavoriteFailed(name=name))
    try:
        path.write_text(json.dumps(favorites, indent=2, sort_keys=True), encoding="utf-8")
    except OSError:
        return Err(error=ClientError_FavoriteFailed(name=name))
    return Ok(value=None)


def _store_favorite(options: SessionOptions, name: str, text: str, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    if not name.strip() or not text.strip():
        return Err(error=ClientError_FavoriteFailed(name=name))
    loaded = _load_favorites(options, name)
    if isinstance(loaded, Err):
        return loaded
    favorites = loaded.value
    if name not in favorites and len(favorites) >= options.favorites.max_entries:
        return Err(error=ClientError_FavoriteFailed(name=name))
    favorites[name] = text
    saved = _save_favorites(options, favorites, name)
    if isinstance(saved, Err):
        return saved
    return _ok(buffer, "Saved.", False)


def _delete_favorite(options: SessionOptions, name: str, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    loaded = _load_favorites(options, name)
    if isinstance(loaded, Err):
        return loaded
    favorites = loaded.value
    if name not in favorites:
        return Err(error=ClientError_FavoriteFailed(name=name))
    del favorites[name]
    saved = _save_favorites(options, favorites, name)
    if isinstance(saved, Err):
        return saved
    return _ok(buffer, f"{name}: Deleted.", False)


def _list_favorites(options: SessionOptions, pattern: str, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    loaded = _load_favorites(options, "")
    if isinstance(loaded, Err):
        return loaded
    rows = [[k, v] for k, v in sorted(loaded.value.items()) if _matches(pattern, k)]
    return _ok(buffer, _render(["Name", "Query"], rows, options.format), False)


def _run_sql(options: SessionOptions, text: str, fmt: TableFormat, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    if not text.strip():
        return _ok(buffer, "", False)
    started = time.perf_counter()
    result = _query(options, text, [])
    if isinstance(result, Err):
        return result
    headers, rows, status = result.value
    recorded = _append_history(options, text)
    if isinstance(recorded, Err):
        return recorded
    parts = [status] if status else []
    if headers:
        parts.append(_render(headers, rows, fmt))
    if options.timing:
        parts.append(f"Time: {time.perf_counter() - started:.3f}s")
    return _ok(buffer, "\n".join(parts), False)


def _list_query(options: SessionOptions, text: str, pattern: str, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    result = _query(options, text, [_like(pattern)])
    if isinstance(result, Err):
        return result
    headers, rows, _status = result.value
    return _ok(buffer, _render(headers, rows, options.format), False)


def _relations(catalog: Catalog, pattern: str, kinds: tuple[str, ...], fmt: TableFormat, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    rows: list[list[str]] = []
    for r in catalog.relations:
        if r.kind.lower() in kinds and (_matches(pattern, r.name) or _matches(pattern, f"{r.schema}.{r.name}")):
            rows.append([r.schema, r.name, r.kind])
    return _ok(buffer, _render(["Schema", "Name", "Type"], rows, fmt), False)


def _names(catalog_values: list[str], pattern: str, header: str, fmt: TableFormat, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    return _ok(buffer, _render([header], [[v] for v in catalog_values if _matches(pattern, v)], fmt), False)


def _identifier(table: str) -> pgsql.Identifier:
    return pgsql.Identifier(*[part.strip('"') for part in table.split(".")])


def _copy(options: SessionOptions, table: str, raw_path: Path, from_file: bool, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    if not table.strip():
        return Err(error=ClientError_InvalidCommand(source="\\copy"))
    path = Path(raw_path)
    data = b""
    if from_file:
        try:
            data = path.read_bytes()
        except OSError as exc:
            return Err(error=ClientError_ImportFailed(path=raw_path, message=str(exc)))
    try:
        conn = _connect(options, "")
    except (psycopg.Error, OSError) as exc:
        return Err(error=ClientError_QueryFailed(message=_safe(exc, options)))
    chunks: list[bytes] = []
    count = 0
    try:
        direction = "FROM STDIN" if from_file else "TO STDOUT"
        statement = pgsql.SQL("COPY {} " + direction + " WITH (FORMAT csv, HEADER true)").format(_identifier(table))
        try:
            with conn.cursor() as cur:
                with cur.copy(statement) as copy:
                    if from_file:
                        copy.write(data)
                    else:
                        for chunk in copy:
                            chunks.append(bytes(chunk))
                count = cur.rowcount
            if not conn.autocommit:
                conn.commit()
        except psycopg.Error as exc:
            if from_file:
                return Err(error=ClientError_ImportFailed(path=raw_path, message=_safe(exc, options)))
            return Err(error=ClientError_ExportFailed(path=raw_path, message=_safe(exc, options)))
    finally:
        conn.close()
    if not from_file:
        try:
            path.write_bytes(b"".join(chunks))
        except OSError as exc:
            return Err(error=ClientError_ExportFailed(path=raw_path, message=str(exc)))
    return _ok(buffer, f"COPY {count}", False)


def _read_into(raw_path: Path, path: Path, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return Err(error=ClientError_ImportFailed(path=raw_path, message=str(exc)))
    return _ok(_buf(text, len(text), buffer.multiline), "", False)


def _touch_append(raw_path: Path) -> Result[None, ClientError]:
    try:
        with Path(raw_path).open("a", encoding="utf-8") as fh:
            fh.write("")
    except OSError as exc:
        return Err(error=ClientError_ExportFailed(path=raw_path, message=str(exc)))
    return Ok(value=None)


def _favorite_text(options: SessionOptions, name: str) -> Result[str, ClientError]:
    loaded = _load_favorites(options, name)
    if isinstance(loaded, Err):
        return loaded
    text = loaded.value.get(name)
    if text is None:
        return Err(error=ClientError_FavoriteFailed(name=name))
    return Ok(value=text)


def _notifications(options: SessionOptions, fmt: TableFormat, buffer: InputBuffer) -> Result[CommandResult, ClientError]:
    try:
        conn = _connect(options, "")
    except (psycopg.Error, OSError) as exc:
        return Err(error=ClientError_NotificationFailed(message=_safe(exc, options)))
    try:
        notes = [[n.channel, n.payload, str(n.pid)] for n in conn.notifies(timeout=0.0)]
    except psycopg.Error as exc:
        return Err(error=ClientError_NotificationFailed(message=_safe(exc, options)))
    finally:
        conn.close()
    return _ok(buffer, _render(["Channel", "Payload", "PID"], notes, fmt), False)


def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]:
    command = invocation.command
    buffer = _buf(invocation.buffer.text, invocation.buffer.cursor, invocation.buffer.multiline)
    fmt = options.format
    if isinstance(command, MetaCommand_Quit):
        return _ok(buffer, "Goodbye!", True)
    if isinstance(command, MetaCommand_Shell):
        return Err(error=ClientError_InvalidCommand(source="\\! " + command.command))
    if isinstance(command, MetaCommand_RefreshCatalog):
        return _ok(buffer, f"Auto-completion refresh completed: {len(catalog.schemas)} schemas, {len(catalog.relations)} relations, {len(catalog.routines)} routines.", False)
    if isinstance(command, MetaCommand_Help):
        return _ok(buffer, _HELP, False)
    if isinstance(command, MetaCommand_SqlHelp):
        topic = command.topic.strip()
        return _ok(buffer, f"https://www.postgresql.org/docs/current/sql-{topic.lower().replace(' ', '')}.html" if topic else "https://www.postgresql.org/docs/current/sql-commands.html", False)
    if isinstance(command, MetaCommand_SetFormat):
        return _ok(buffer, f"Changed table format to {_format_name(command.format)}", False)
    if isinstance(command, MetaCommand_Connect):
        try:
            conn = _connect(options, command.database)
            try:
                database = conn.info.dbname
            finally:
                conn.close()
        except (psycopg.Error, OSError) as exc:
            return Err(error=ClientError_QueryFailed(message=_safe(exc, options)))
        return _ok(buffer, f'You are now connected to database "{database}"', False)
    if isinstance(command, MetaCommand_ConnectionInfo):
        s = options.connection.settings
        return _ok(buffer, f'You are connected to database "{s.database}" as user "{s.user}" on host "{s.host}" at port "{s.port}".', False)
    if isinstance(command, MetaCommand_Copy):
        return _copy(options, command.table, command.path, command.from_file, buffer)
    if isinstance(command, MetaCommand_Describe):
        if not command.pattern.strip():
            return _relations(catalog, "", ("table", "r", "view", "v", "materialized_view", "materialized view", "m", "sequence", "s", "foreign_table", "foreign table", "f", "partitioned table", "p"), fmt, buffer)
        columns: list[list[str]] = []
        for r in catalog.relations:
            if _matches(command.pattern, r.name) or _matches(command.pattern, f"{r.schema}.{r.name}"):
                for c in r.columns:
                    columns.append([c.name])
        return _ok(buffer, _render(["Column"], columns, fmt), False)
    if isinstance(command, MetaCommand_ListDomains):
        return _list_query(options, "SELECT n.nspname AS schema, t.typname AS name, pg_catalog.format_type(t.typbasetype, t.typtypmod) AS type FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typtype = 'd' AND t.typname LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListForeignTables):
        return _list_query(options, "SELECT foreign_table_schema AS schema, foreign_table_name AS name, foreign_server_name AS server FROM information_schema.foreign_tables WHERE foreign_table_name LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListTextSearchConfigurations):
        return _list_query(options, "SELECT n.nspname AS schema, c.cfgname AS name FROM pg_catalog.pg_ts_config c JOIN pg_catalog.pg_namespace n ON n.oid = c.cfgnamespace WHERE c.cfgname LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListDataTypes):
        return _list_query(options, "SELECT n.nspname AS schema, pg_catalog.format_type(t.oid, NULL) AS name FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typelem = 0 AND t.typrelid = 0 AND t.typname LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListTablespaces):
        return _list_query(options, "SELECT spcname AS name, pg_catalog.pg_get_userbyid(spcowner) AS owner, pg_catalog.pg_tablespace_location(oid) AS location FROM pg_catalog.pg_tablespace WHERE spcname LIKE %s ORDER BY 1", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListDefaultPrivileges):
        return _list_query(options, "SELECT pg_catalog.pg_get_userbyid(d.defaclrole) AS owner, COALESCE(n.nspname, '') AS schema, d.defaclobjtype AS type, pg_catalog.array_to_string(d.defaclacl, E'\\n') AS privileges FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace WHERE COALESCE(n.nspname, '') LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListFunctions):
        routines: list[list[str]] = []
        for rt in catalog.routines:
            if _matches(command.pattern, rt.name) or _matches(command.pattern, f"{rt.schema}.{rt.name}"):
                routines.append([rt.schema, rt.name, rt.result_type, rt.arguments])
        return _ok(buffer, _render(["Schema", "Name", "Result data type", "Argument data types"], routines, fmt), False)
    if isinstance(command, MetaCommand_ListIndexes):
        return _list_query(options, "SELECT schemaname AS schema, indexname AS name, tablename AS table FROM pg_catalog.pg_indexes WHERE indexname LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListMaterializedViews):
        return _relations(catalog, command.pattern, ("materialized_view", "materialized view", "matview", "m"), fmt, buffer)
    if isinstance(command, MetaCommand_ListSchemas):
        return _names([v for v in catalog.schemas], command.pattern, "Name", fmt, buffer)
    if isinstance(command, MetaCommand_ListPrivileges):
        return _list_query(options, "SELECT n.nspname AS schema, c.relname AS name, pg_catalog.array_to_string(c.relacl, E'\\n') AS privileges FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r', 'v', 'm', 'S', 'f', 'p') AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND c.relname LIKE %s ORDER BY 1, 2", command.pattern, buffer)
    if isinstance(command, MetaCommand_ListSequences):
        return _relations(catalog, command.pattern, ("sequence", "s"), fmt, buffer)
    if isinstance(command, MetaCommand_ListTables):
        return _relations(catalog, command.pattern, ("table", "r", "partitioned table", "p"), fmt, buffer)
    if isinstance(command, MetaCommand_ListRoles):
        return _names([v for v in catalog.roles], "", "Role name", fmt, buffer)
    if isinstance(command, MetaCommand_ListViews):
        return _relations(catalog, command.pattern, ("view", "v"), fmt, buffer)
    if isinstance(command, MetaCommand_ListExtensions):
        return _names([v for v in catalog.extensions], "", "Name", fmt, buffer)
    if isinstance(command, MetaCommand_ListDatabases):
        return _names([v for v in catalog.databases], "", "Name", fmt, buffer)
    if isinstance(command, MetaCommand_ShowFunction):
        if not command.pattern.strip():
            return Err(error=ClientError_InvalidCommand(source="\\sf"))
        result = _query(options, "SELECT pg_catalog.pg_get_functiondef(%s::regprocedure)" if "(" in command.pattern else "SELECT pg_catalog.pg_get_functiondef(%s::regproc)", [command.pattern.strip()])
        if isinstance(result, Err):
            return result
        return _ok(buffer, "\n".join(r[0] for r in result.value[1] if r), False)
    if isinstance(command, MetaCommand_EditBuffer):
        return Err(error=ClientError_EditorFailed(message="external editor is not available"))
    if isinstance(command, MetaCommand_Echo):
        return _ok(buffer, command.text, False)
    if isinstance(command, MetaCommand_ReadFile):
        return _read_into(command.path, Path(command.path), buffer)
    if isinstance(command, MetaCommand_ReadRelativeFile):
        return _read_into(command.path, Path.cwd() / Path(command.path), buffer)
    if isinstance(command, MetaCommand_NamedQuery):
        if not command.name.strip():
            return _list_favorites(options, "", buffer)
        found = _favorite_text(options, command.name)
        if isinstance(found, Err):
            return found
        text = found.value
        for index, argument in enumerate(command.arguments, 1):
            text = text.replace(f"${index}", argument)
        return _run_sql(options, text, fmt, buffer)
    if isinstance(command, MetaCommand_SetLogFile):
        touched = _touch_append(command.path)
        if isinstance(touched, Err):
            return touched
        return _ok(buffer, f'Logging to "{command.path}"', False)
    if isinstance(command, MetaCommand_DeleteNamedQuery):
        return _delete_favorite(options, command.name, buffer)
    if isinstance(command, MetaCommand_PrintNamedQuery):
        found = _favorite_text(options, command.name)
        if isinstance(found, Err):
            return found
        return _ok(buffer, f"{command.name}: {found.value}", False)
    if isinstance(command, MetaCommand_SaveNamedQuery):
        return _store_favorite(options, command.name, command.sql, buffer)
    if isinstance(command, MetaCommand_SetOutput):
        touched = _touch_append(command.path)
        if isinstance(touched, Err):
            return touched
        return _ok(buffer, f'Writing to file "{command.path}"', False)
    if isinstance(command, MetaCommand_ClearOutput):
        return _ok(buffer, "Output is sent to stdout", False)
    if isinstance(command, MetaCommand_SetPager):
        return _ok(buffer, "Pager usage is on." if command.enabled else "Pager usage is off.", False)
    if isinstance(command, MetaCommand_SetOptions):
        if not command.key.strip():
            return Err(error=ClientError_InvalidCommand(source="\\set"))
        return _ok(buffer, f"Set {command.key} to {command.value}", False)
    if isinstance(command, MetaCommand_QueryOutputEcho):
        return _ok(buffer, command.text, False)
    if isinstance(command, MetaCommand_Timing):
        return _ok(buffer, "Timing is off." if options.timing else "Timing is on.", False)
    if isinstance(command, MetaCommand_VerboseErrors):
        return _ok(buffer, "Verbose errors on." if command.enabled else "Verbose errors off.", False)
    if isinstance(command, MetaCommand_Watch):
        if command.interval_ms == 0:
            return Err(error=ClientError_InvalidCommand(source="\\watch 0"))
        return _run_sql(options, buffer.text, fmt, buffer)
    if isinstance(command, MetaCommand_Expanded):
        return _ok(buffer, "Expanded display is on.", False)
    if isinstance(command, MetaCommand_ExecuteBuffer):
        return _run_sql(options, buffer.text, fmt, _buf("", 0, buffer.multiline))
    if isinstance(command, MetaCommand_ExecuteExpanded):
        return _run_sql(options, buffer.text, TableFormat_Vertical(), _buf("", 0, buffer.multiline))
    if isinstance(command, MetaCommand_PrintBuffer):
        return _ok(buffer, buffer.text if buffer.text else "Query buffer is empty.", False)
    if isinstance(command, MetaCommand_ResetBuffer):
        return _ok(_buf("", 0, buffer.multiline), "Query buffer reset (cleared).", False)
    if isinstance(command, MetaCommand_WriteBuffer):
        try:
            Path(command.path).write_text(buffer.text, encoding="utf-8")
        except OSError as exc:
            return Err(error=ClientError_ExportFailed(path=command.path, message=str(exc)))
        return _ok(buffer, f'Wrote buffer to "{command.path}"', False)
    if isinstance(command, MetaCommand_History):
        loaded_history = _load_history(options)
        if isinstance(loaded_history, Err):
            return loaded_history
        pattern = command.pattern.strip()
        lines = [f"{n}  {sql}" for n, (_db, sql) in enumerate(loaded_history.value, 1) if not pattern or pattern in sql]
        return _ok(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_Favorite):
        return _store_favorite(options, command.name, buffer.text, buffer)
    if isinstance(command, MetaCommand_ListFavorites):
        return _list_favorites(options, command.pattern, buffer)
    if isinstance(command, MetaCommand_DeleteFavorite):
        return _delete_favorite(options, command.name, buffer)
    if isinstance(command, MetaCommand_Password):
        return Err(error=ClientError_InvalidCommand(source="\\password"))
    if isinstance(command, MetaCommand_ListNotifications):
        return _notifications(options, fmt, buffer)
    return Err(error=ClientError_InvalidCommand(source=command.source))
