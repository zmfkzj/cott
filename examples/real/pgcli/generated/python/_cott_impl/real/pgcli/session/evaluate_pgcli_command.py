import dataclasses
import os
import pathlib
import re
import time
from collections.abc import Callable, Iterator
from typing import Any, Final, cast

import click
import pgspecial.iocommands
import pgspecial.main
import pgspecial.namedqueries
import psycopg
import psycopg.errors
import sqlparse
from cott_runtime import CottList, Err, Nothing, Ok, Opaque, Result, Some

from real.pgcli.connection import executor_transaction_status, reconnect_executor
from real.pgcli.connection_types import ConnectError_Failed, Executor, ReconnectRequest, TransactionStatus_Active, TransactionStatus_InTransaction
from real.pgcli.output import format_output, table_format_names
from real.pgcli.output_types import OutputSettings, ResultSet
from real.pgcli.parseutils import is_destructive
from real.pgcli.session import change_db_arguments, classify_statement, confirm_destructive_query, should_limit_rows
from real.pgcli.session_types import EvaluateError, EvaluateError_ConnectionLost, EvaluateError_Failed, EvaluateError_Interrupted, EvaluateError_NotImplemented, Evaluation, QueryOutcome, RefreshKind, RefreshKind_All, RefreshKind_Nothing, RefreshKind_Reset, RefreshKind_SearchPath, Session, SessionSettings, TerminalSize

_OWN: Final[str] = "\\nq|\\ne|\\c|\\connect|use|USE|\\q|:q|quit|exit|\\#|\\refresh|\\i|\\o|\\log-file|\\conninfo|\\T|\\echo|\\qecho|\\v"
_EXPLAIN: Final[str] = "EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) "


def _conn(st: dict[str, Any]) -> psycopg.Connection[tuple[object, ...]]:
    executor = cast(Executor, st["executor"])
    return cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())


def _settings(st: dict[str, Any]) -> SessionSettings:
    return cast(SessionSettings, st["settings"])


def _set(st: dict[str, Any], changes: dict[str, Any]) -> None:
    st["settings"] = dataclasses.replace(_settings(st), **changes)


def _split(text: str) -> list[str]:
    sp: Any = sqlparse
    text = text.strip()
    if not text:
        return []
    comments: list[str] = []
    while True:
        m = re.match(r"^(/\*.*?\*/|--.*?)(?:\n|$)", text, re.DOTALL)
        if m is None:
            break
        comments.append(m.group(0))
        text = text[m.end():].lstrip()
    raw: Any = sp.split(text)
    pieces: list[str] = comments + [str(cast(object, p)) for p in raw]
    out: list[str] = []
    for piece in pieces:
        formatted: object = sp.format(piece, strip_comments=True)
        s = str(formatted).strip().rstrip(";").strip()
        if s:
            out.append(s)
    return out


def _make(title: object, rows: object, headers: object, status: object, sql: str, success: bool, is_special: bool) -> dict[str, Any]:
    types: list[str] = []
    rowcount = -1
    data: list[tuple[object, ...]] | None = None
    source: psycopg.Cursor[tuple[object, ...]] | None = None
    header_list: list[str] = []
    if headers is not None:
        hs: Any = headers
        header_list = [str(cast(object, h)) for h in hs]
    if isinstance(rows, psycopg.Cursor):
        cur = cast(psycopg.Cursor[tuple[object, ...]], rows)
        if cur.description is not None:
            rowcount = cur.rowcount
            for d in cur.description:
                info = cur.adapters.types.get(d.type_code)
                types.append(info.name if info is not None else "")
            source = cur
    elif rows is not None:
        rs: Any = rows
        data = []
        for r in rs:
            row: Any = r
            data.append(tuple(cast(list[object], list(row))))
        types = ["" for _ in header_list]
    return {
        "title": None if title is None else str(title),
        "rows": data,
        "headers": header_list,
        "status": None if status is None else str(status),
        "sql": sql,
        "success": success,
        "special": is_special,
        "rowcount": rowcount,
        "types": types,
        "db_error": False,
        "cursor": source,
    }


def _msg(message: str, sql: str, success: bool) -> dict[str, Any]:
    return _make(None, None, None, message, sql, success, True)


def _resolve(special: Any, command: str) -> str | None:
    cmds: Any = special.commands
    if command in cmds:
        return command
    low = command.lower()
    if low in cmds:
        entry: Any = cmds[low]
        flag: object = entry.case_sensitive
        if not bool(flag):
            return low
        return None
    if command in _OWN.split("|"):
        return command
    return None


def _reconnect(st: dict[str, Any], request: ReconnectRequest) -> str | None:
    result = reconnect_executor(cast(Executor, st["executor"]), request)
    if isinstance(result, Err):
        error = result.error
        return error.message if isinstance(error, ConnectError_Failed) else str(error)
    st["executor"] = result.value
    return None


def _own(st: dict[str, Any], key: str, pattern: str, sql: str) -> Iterator[dict[str, Any]]:
    settings = _settings(st)
    executor = cast(Executor, st["executor"])
    arg = pattern.strip()
    if key == "\\nq":
        value = not settings.hide_named_query_text
        _set(st, {"hide_named_query_text": value})
        yield _msg("Named query quiet mode: " + ("ON" if value else "OFF"), sql, True)
    elif key == "\\ne":
        if not arg:
            yield _msg("Usage: \\ne <name>", sql, True)
            return
        nq: Any = pgspecial.namedqueries.NamedQueries.instance
        existing: object = nq.get(arg)
        current = existing if isinstance(existing, str) else ""
        editor = os.environ.get("PSQL_EDITOR") or os.environ.get("EDITOR") or os.environ.get("VISUAL") or None
        io: Any = pgspecial.iocommands
        edited: Any = io.open_external_editor(sql=current, editor=editor)
        query: object = edited[0]
        message: object = edited[1]
        if message:
            yield _msg(str(message), sql, True)
        new = str(query).strip() if query is not None else ""
        if not new:
            yield _msg(arg + ": empty query, not saved.", sql, True)
        elif isinstance(existing, str) and new == existing:
            yield _msg(arg + ": no changes.", sql, True)
        else:
            nq.save(arg, new)
            yield _msg(arg + (": Saved" if isinstance(existing, str) else ": Created"), sql, True)
    elif key in ("\\c", "\\connect", "use", "USE"):
        if arg:
            args = [a for a in change_db_arguments(pattern)]
            request = ReconnectRequest(database=args[0], user=args[1], host=args[2], port=args[3])
        else:
            request = ReconnectRequest(database="", user="", host="", port="")
        error = _reconnect(st, request)
        if error is not None:
            click.secho(error, err=True, fg="red")
            click.echo("Previous connection kept")
        executor = cast(Executor, st["executor"])
        yield _msg('You are now connected to database "' + executor.dbname + '" as user "' + executor.user + '"', sql, True)
    elif key in ("\\q", ":q", "quit", "exit"):
        st["quit"] = True
    elif key in ("\\#", "\\refresh"):
        if executor.virtual_database:
            yield _msg("Auto-completion refresh can't be started.", sql, True)
        else:
            st["refresh_all"] = True
            if settings.completion_refreshing:
                yield _msg("Auto-completion refresh restarted.", sql, True)
            else:
                yield _msg("Auto-completion refresh started in the background.", sql, True)
    elif key == "\\i":
        if not arg:
            yield _msg("\\i: missing required argument", sql, False)
            return
        try:
            with open(os.path.expanduser(arg), encoding="utf-8") as handle:
                contents = handle.read()
        except OSError as error:
            yield _msg(str(error), sql, False)
            return
        warning = settings.destructive_warning
        if len([w for w in warning]) > 0:
            status = executor_transaction_status(executor)
            valid = isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction))
            if settings.destructive_statements_require_transaction and not valid and is_destructive(contents, warning):
                yield _msg("Destructive statements must be run within a transaction. Command execution stopped.", sql, True)
                return
            answer = confirm_destructive_query(contents, warning, settings.dsn_alias, settings.force_destructive)
            if isinstance(answer, Some) and not answer.value:
                yield _msg("Wise choice. Command execution stopped.", sql, True)
                return
        yield from _run(st, contents, True)
    elif key == "\\o":
        if not arg:
            _set(st, {"output_file": Nothing()})
            yield _msg("File output disabled", sql, True)
            return
        path = os.path.abspath(os.path.expanduser(arg))
        if not os.path.isfile(path):
            try:
                open(path, "w", encoding="utf-8").close()
            except OSError as error:
                _set(st, {"output_file": Nothing()})
                yield _msg(str(error) + "\nFile output disabled", sql, False)
                return
        _set(st, {"output_file": Some(value=path)})
        yield _msg('Writing to file "' + path + '"', sql, True)
    elif key == "\\log-file":
        if not arg:
            _set(st, {"log_file": Nothing()})
            yield _msg("Logfile capture disabled", sql, True)
            return
        log_path = pathlib.Path(arg).expanduser().absolute()
        try:
            open(log_path, "a+", encoding="utf-8").close()
        except OSError as error:
            _set(st, {"log_file": Nothing()})
            yield _msg(str(error) + "\nLogfile capture disabled", sql, False)
            return
        _set(st, {"log_file": Some(value=str(log_path))})
        yield _msg('Writing to file "' + str(log_path) + '"', sql, True)
    elif key == "\\conninfo":
        where = ('socket "' if executor.host.startswith("/") else 'host "') + executor.host + '"'
        yield _msg('You are connected to database "' + executor.dbname + '" as user "' + executor.user + '" on ' + where + ' at port "' + executor.port + '".', sql, True)
    elif key == "\\T":
        names = [n for n in table_format_names()]
        if arg in names:
            _set(st, {"table_format": arg})
            yield _msg("Changed table format to " + arg, sql, True)
        else:
            text = "Table format " + arg + " not recognized. Allowed formats:"
            for name in names:
                text += "\n\t" + name
            text += "\nCurrently set to: " + settings.table_format
            yield _msg(text, sql, True)
    elif key in ("\\echo", "\\qecho"):
        yield _msg(pattern, sql, True)
    else:
        if arg == "on":
            verbose = True
        elif arg == "off":
            verbose = False
        else:
            verbose = not settings.verbose_errors
        _set(st, {"verbose_errors": verbose})
        yield _msg("Verbose errors on." if verbose else "off.", sql, True)


def _notice(title: list[str], diag: psycopg.errors.Diagnostic) -> None:
    title[0] += "\n" + str(diag.message_primary)
    if diag.message_detail:
        title[0] += "\n" + diag.message_detail


def _statement(st: dict[str, Any], sql: str) -> Iterator[dict[str, Any]]:
    special: Any = st["special"]
    main: Any = pgspecial.main
    parsed: Any = main.parse_special_command(sql)
    command = str(cast(object, parsed[0]))
    pattern = str(cast(object, parsed[2]))
    key = _resolve(special, command)
    if key is not None and key in _OWN.split("|"):
        yield from _own(st, key, pattern, sql)
        return
    if key == "\\do":
        st["not_impl"] = True
        return
    conn = _conn(st)
    executor = cast(Executor, st["executor"])
    not_found: Any = main.CommandNotFound
    special_results: list[dict[str, Any]] | None
    try:
        try:
            cur: object = conn.cursor()
        except Exception:
            cur = None
        results: Any = special.execute(cur, sql)
        special_results = []
        for item in results:
            entry: Any = item
            special_results.append(_make(cast(object, entry[0]), cast(object, entry[1]), cast(object, entry[2]), cast(object, entry[3]), sql, True, True))
    except psycopg.errors.ProtocolViolation as error:
        if not executor.virtual_database:
            raise
        yield _msg(str(error), sql, False)
        _reconnect(st, ReconnectRequest(database="", user="", host="", port=""))
        return
    except Exception as error:
        if not isinstance(error, not_found):
            raise
        special_results = None
    if special_results is not None:
        yield from special_results
        return
    query = (_EXPLAIN + sql) if _settings(st).explain_mode else sql
    if executor.virtual_database and "show help" in sql.lower():
        res = conn.pgconn.exec_(query.encode("utf-8"))
        cs = res.command_status
        yield _make("", None, None, cs.decode() if cs is not None else None, sql, True, False)
        return
    title = [""]
    handler: Callable[[psycopg.errors.Diagnostic], None] = lambda diag: _notice(title, diag)
    conn.add_notice_handler(handler)
    try:
        cursor = conn.cursor()
        cursor.execute(query.encode("utf-8"))
    finally:
        conn.remove_notice_handler(handler)
    if cursor.description is not None:
        names = [d.name for d in cursor.description]
        yield _make(title[0], cursor, names, cursor.statusmessage, sql, True, False)
    else:
        yield _make(title[0], None, None, cursor.statusmessage, sql, True, False)


def _error_text(st: dict[str, Any], error: psycopg.DatabaseError) -> str:
    text = str(error)
    if not _settings(st).verbose_errors:
        return text
    d = error.diag
    fields: list[tuple[str, object]] = [
        ("Severity", d.severity), ("Severity (non-localized)", d.severity_nonlocalized), ("SQLSTATE code", d.sqlstate),
        ("Message", d.message_primary), ("Detail", d.message_detail), ("Hint", d.message_hint),
        ("Position", d.statement_position), ("Internal position", d.internal_position), ("Internal query", d.internal_query),
        ("Where", d.context), ("Schema name", d.schema_name), ("Table name", d.table_name), ("Column name", d.column_name),
        ("Data type name", d.datatype_name), ("Constraint name", d.constraint_name), ("File", d.source_file),
        ("Line", d.source_line), ("Routine", d.source_function),
    ]
    lines = [label + ": " + str(value) for label, value in fields if value is not None]
    return text + "\n" + "\n".join(lines)


def _one(st: dict[str, Any], sql: str) -> Iterator[dict[str, Any]]:
    special: Any = st["special"]
    restore = False
    if sql.endswith("\\G"):
        expanded: object = special.expanded_output
        if not bool(expanded):
            special.expanded_output = True
            restore = True
        sql = sql[:-2].strip()
    try:
        yield from _statement(st, sql)
    except psycopg.DatabaseError as error:
        if _conn(st).closed != 0:
            raise
        res = _make(None, None, None, click.style(_error_text(st, error), fg="red"), sql, False, False)
        res["db_error"] = True
        yield res
    finally:
        if restore:
            special.expanded_output = False


def _run(st: dict[str, Any], text: str, resume: bool) -> Iterator[dict[str, Any]]:
    resume = resume or _settings(st).on_error == "RESUME"
    for sql in _split(text):
        if st["quit"] or st["not_impl"]:
            return
        stop = False
        for res in _one(st, sql):
            yield res
            if res["db_error"]:
                stop = True
        if stop and not resume:
            return


def _results(st: dict[str, Any], text: str) -> Iterator[dict[str, Any]]:
    if text.strip() == "":
        yield _make(None, None, None, None, "", False, False)
        return
    yield from _run(st, text, False)


def evaluate_pgcli_command(session: Session, text: str, screen: TerminalSize) -> Result[Evaluation, EvaluateError]:
    start = time.time()
    special: Any = session.special.unwrap()
    st: dict[str, Any] = {"settings": session.settings, "executor": session.executor, "special": special, "quit": False, "not_impl": False, "refresh_all": False}
    texts: list[str] = []
    items = 0
    successful = True
    mutated = meta = db = path = False
    is_special = False
    execution = 0.0
    total = 0.0
    stripped = text.strip()
    named = stripped.startswith("\\n ") and not stripped.startswith("\\ns ") and not stripped.startswith("\\nd ")
    try:
        for res in _results(st, text):
            execution = time.time() - start
            settings = _settings(st)
            rows = cast(list[tuple[object, ...]] | None, res["rows"])
            status = cast(str | None, res["status"])
            title = cast(str | None, res["title"])
            rowcount = cast(int, res["rowcount"])
            sql = cast(str, res["sql"])
            source = cast(psycopg.Cursor[tuple[object, ...]] | None, res["cursor"])
            if source is not None and rowcount >= 0 and should_limit_rows(sql, rowcount, settings.row_limit, settings.explain_mode):
                limit = min(settings.row_limit, rowcount)
                rows = [tuple(r) for r in source.fetchmany(limit)]
                status = "SELECT " + str(limit)
                rowcount = -1
                click.secho("The result was limited to " + str(limit) + " rows", fg="red")
            elif source is not None:
                rows = [tuple(r) for r in source.fetchall()]
            if settings.hide_named_query_text and named and res["success"] and res["special"] and title is not None and title.startswith("> "):
                title = None
            result_set = Nothing() if rows is None else Some(value=ResultSet(columns=CottList(values=cast(list[str], res["headers"])), type_names=CottList(values=cast(list[str], res["types"])), rows=Opaque(tag="pgcli.result-rows", value=list(rows)), rowcount=rowcount))
            sp_expanded: object = special.expanded_output
            sp_auto: object = special.auto_expand
            output_settings = OutputSettings(
                table_format=settings.table_format,
                column_date_formats=settings.column_date_formats,
                max_field_width=settings.max_field_width,
                decimal_format=settings.decimal_format,
                float_format=settings.float_format,
                missing_value=settings.null_string,
                expanded=bool(sp_expanded) or settings.expanded_output,
                max_width=Some(value=screen.columns) if bool(sp_auto) or settings.auto_expand else Nothing(),
                header_casing=Some(value=session.catalog) if settings.case_column_headers else Nothing(),
                style=settings.output_style,
                tuples_only=settings.tuples_only,
                query=text,
            )
            formatted = format_output(Nothing() if title is None else Some(value=title), result_set, Nothing() if status is None else Some(value=status), output_settings, settings.explain_mode)
            if isinstance(formatted, Err):
                return Err(error=EvaluateError_Failed(message=formatted.error.message))
            out = formatted.value
            if out.items > 0:
                texts.append(out.text)
                items += out.items
            total = time.time() - start
            if res["success"]:
                changes = classify_statement(sql, status or "")
                mutated = mutated or changes.mutated
                meta = meta or changes.meta_changed
                db = db or changes.db_changed
                path = path or changes.path_changed
            else:
                successful = False
            is_special = bool(res["special"])
    except KeyboardInterrupt:
        return Err(error=EvaluateError_Interrupted())
    except psycopg.OperationalError as error:
        if _conn(st).closed == 0:
            return Err(error=EvaluateError_Failed(message=str(error)))
        return Err(error=EvaluateError_ConnectionLost(message=str(error)))
    except Exception as error:
        return Err(error=EvaluateError_Failed(message=str(error)))
    if st["not_impl"]:
        return Err(error=EvaluateError_NotImplemented())
    refresh: RefreshKind
    if db:
        refresh = RefreshKind_Reset()
    elif meta or st["refresh_all"]:
        refresh = RefreshKind_All()
    elif path:
        refresh = RefreshKind_SearchPath()
    else:
        refresh = RefreshKind_Nothing()
    query = QueryOutcome(query=text, successful=successful, total_time=total, execution_time=execution, meta_changed=meta, db_changed=db, path_changed=path, mutated=mutated, is_special=is_special)
    new_session = dataclasses.replace(session, settings=_settings(st), executor=cast(Executor, st["executor"]), last_query=text)
    return Ok(value=Evaluation(session=new_session, output="\n".join(texts), items=items, query=query, refresh=refresh, quit=bool(st["quit"])))
