import dataclasses
import os
import pathlib
import re
import time
from collections.abc import Callable, Iterable, Iterator
from typing import Any, Final, cast

import click
import pgspecial.iocommands
import pgspecial.main
import pgspecial.namedqueries
import psycopg
import psycopg.errors
import sqlparse
from pgspecial.main import CommandNotFound

from cott_runtime import CottList, Err, Nothing, Ok, Opaque, Result, Some
from real.pgcli.connection import executor_transaction_status, reconnect_executor
from real.pgcli.connection_types import ConnectError_Failed, Executor, ReconnectRequest, TransactionStatus_Active, TransactionStatus_InTransaction
from real.pgcli.output import format_output, table_format_names
from real.pgcli.output_types import OutputSettings, ResultSet
from real.pgcli.parseutils import is_destructive
from real.pgcli.session import change_db_arguments, classify_statement, confirm_destructive_query, should_limit_rows
from real.pgcli.session_types import EvaluateError, EvaluateError_ConnectionLost, EvaluateError_Failed, EvaluateError_Interrupted, EvaluateError_NotImplemented, Evaluation, QueryOutcome, RefreshKind, RefreshKind_All, RefreshKind_Nothing, RefreshKind_Reset, RefreshKind_SearchPath, Session, SessionSettings, TerminalSize

_EXPLAIN: Final[str] = "EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) "


def _connection(state: dict[str, object]) -> psycopg.Connection[tuple[object, ...]]:
    executor = cast(Executor, state["executor"])
    return cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())


def _settings(state: dict[str, object]) -> SessionSettings:
    return cast(SessionSettings, state["settings"])


def _replace_settings(state: dict[str, object], changes: dict[str, object]) -> None:
    state["settings"] = dataclasses.replace(_settings(state), **changes)


def _split_statements(text: str) -> list[str]:
    remaining = text.strip()
    if not remaining:
        return []
    comments: list[str] = []
    while True:
        match = re.match(r"^(/\*.*?\*/|--.*?)(?:\n|$)", remaining, re.DOTALL)
        if match is None:
            break
        comments.append(match.group(0))
        remaining = remaining[match.end():].lstrip()
    raw_pieces = cast(object, sqlparse.split(remaining))
    if not isinstance(raw_pieces, list):
        raise TypeError("invalid statement list")
    pieces = [str(piece) for piece in cast(list[object], raw_pieces)]
    if comments:
        if pieces:
            pieces[0] = "".join(comments) + pieces[0]
        else:
            pieces = ["".join(comments)]
    statements: list[str] = []
    for piece in pieces:
        sql = str(cast(object, sqlparse.format(piece, strip_comments=True))).strip().rstrip(";").strip()
        if sql:
            statements.append(sql)
    return statements


def _make_result(title: str | None, rows: object, headers: list[str], status: str | None, sql: str, successful: bool, special: bool, db_error: bool) -> dict[str, object]:
    return {"title": title, "rows": rows, "headers": headers, "status": status, "sql": sql, "successful": successful, "special": special, "db_error": db_error}


def _message(message: str, sql: str, successful: bool) -> dict[str, object]:
    return _make_result(None, None, [], message, sql, successful, True, False)


def _optional_text(value: object) -> str | None:
    return None if value is None else str(value)


def _headers(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Iterable):
        raise TypeError("headers are not iterable")
    return [str(item) for item in cast(Iterable[object], value)]


def _plain_rows(value: object) -> list[tuple[object, ...]]:
    if not isinstance(value, Iterable):
        raise TypeError("rows are not iterable")
    rows: list[tuple[object, ...]] = []
    for row in cast(Iterable[object], value):
        if isinstance(row, tuple):
            rows.append(cast(tuple[object, ...], row))
        elif isinstance(row, Iterable):
            rows.append(tuple(cast(Iterable[object], row)))
        else:
            raise TypeError("row is not iterable")
    return rows


def _resolve_command(special: Any, command: str) -> str | None:
    raw = cast(object, special.commands)
    if not isinstance(raw, dict):
        raise TypeError("invalid special command registry")
    commands = cast(dict[object, object], raw)
    if command in commands:
        return command
    lower = command.lower()
    if lower in commands:
        entry: Any = commands[lower]
        if not bool(cast(object, entry.case_sensitive)):
            return lower
    return None


def _reconnect(state: dict[str, object], request: ReconnectRequest) -> str | None:
    result = reconnect_executor(cast(Executor, state["executor"]), request)
    if isinstance(result, Err):
        error = result.error
        return error.message if isinstance(error, ConnectError_Failed) else str(error)
    state["executor"] = result.value
    return None


def _own_command(state: dict[str, object], key: str, pattern: str, sql: str) -> Iterator[dict[str, object]]:
    settings = _settings(state)
    executor = cast(Executor, state["executor"])
    arg = pattern.strip()
    if key == "\\nq":
        quiet = not settings.hide_named_query_text
        _replace_settings(state, {"hide_named_query_text": quiet})
        yield _message("Named query quiet mode: " + ("ON" if quiet else "OFF"), sql, True)
    elif key == "\\ne":
        if not arg:
            yield _message("Usage: \\ne <name>", sql, True)
            return
        named: Any = cast(Any, pgspecial.namedqueries.NamedQueries.instance)
        existing = cast(object, named.get(arg))
        editor = os.environ.get("PSQL_EDITOR") or os.environ.get("EDITOR") or os.environ.get("VISUAL") or None
        edited = cast(object, pgspecial.iocommands.open_external_editor(sql=existing if isinstance(existing, str) else "", editor=editor))
        if not isinstance(edited, tuple):
            raise TypeError("editor did not return a query and message")
        edit_parts = cast(tuple[object, ...], edited)
        query, message = edit_parts[0], edit_parts[1]
        if message:
            yield _message(str(message), sql, True)
        new_query = str(query).strip() if query is not None else ""
        if not new_query:
            yield _message(arg + ": empty query, not saved.", sql, True)
        elif isinstance(existing, str) and new_query == existing:
            yield _message(arg + ": no changes.", sql, True)
        else:
            named.save(arg, new_query)
            yield _message(arg + (": Saved" if isinstance(existing, str) else ": Created"), sql, True)
    elif key in ("\\c", "\\connect", "use", "USE"):
        if arg:
            arguments = list(change_db_arguments(pattern))
            request = ReconnectRequest(database=arguments[0], user=arguments[1], host=arguments[2], port=arguments[3])
        else:
            request = ReconnectRequest(database="", user="", host="", port="")
        failure = _reconnect(state, request)
        if failure is not None:
            click.secho(failure, err=True, fg="red")
            click.echo("Previous connection kept")
        executor = cast(Executor, state["executor"])
        yield _message('You are now connected to database "' + executor.dbname + '" as user "' + executor.user + '"', sql, True)
    elif key in ("\\q", ":q", "quit", "exit"):
        state["quit"] = True
    elif key in ("\\#", "\\refresh"):
        if executor.virtual_database:
            yield _message("Auto-completion refresh can't be started.", sql, True)
        else:
            state["refresh_all"] = True
            yield _message("Auto-completion refresh restarted." if settings.completion_refreshing else "Auto-completion refresh started in the background.", sql, True)
    elif key == "\\i":
        if not arg:
            yield _message("\\i: missing required argument", sql, False)
            return
        try:
            with open(os.path.expanduser(arg), encoding="utf-8") as handle:
                contents = handle.read()
        except OSError as error:
            yield _message(str(error), sql, False)
            return
        if len(settings.destructive_warning) > 0:
            status = executor_transaction_status(executor)
            valid = isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction))
            if settings.destructive_statements_require_transaction and not valid and is_destructive(contents, settings.destructive_warning):
                yield _message("Destructive statements must be run within a transaction. Command execution stopped.", sql, True)
                return
            answer = confirm_destructive_query(contents, settings.destructive_warning, settings.dsn_alias, settings.force_destructive)
            if isinstance(answer, Some) and not answer.value:
                yield _message("Wise choice. Command execution stopped.", sql, True)
                return
        yield from _run_statements(state, contents)
    elif key == "\\o":
        if not arg:
            _replace_settings(state, {"output_file": Nothing()})
            yield _message("File output disabled", sql, True)
            return
        path = os.path.abspath(os.path.expanduser(arg))
        if not os.path.isfile(path):
            try:
                open(path, "w", encoding="utf-8").close()
            except OSError as error:
                _replace_settings(state, {"output_file": Nothing()})
                yield _message(str(error) + "\nFile output disabled", sql, False)
                return
        _replace_settings(state, {"output_file": Some(value=path)})
        yield _message('Writing to file "' + path + '"', sql, True)
    elif key == "\\log-file":
        if not arg:
            _replace_settings(state, {"log_file": Nothing()})
            yield _message("Logfile capture disabled", sql, True)
            return
        path = pathlib.Path(arg).expanduser().absolute()
        try:
            open(path, "a+", encoding="utf-8").close()
        except OSError as error:
            _replace_settings(state, {"log_file": Nothing()})
            yield _message(str(error) + "\nLogfile capture disabled", sql, False)
            return
        _replace_settings(state, {"log_file": Some(value=str(path))})
        yield _message('Writing to file "' + str(path) + '"', sql, True)
    elif key == "\\conninfo":
        where = ('socket "' if executor.host.startswith("/") else 'host "') + executor.host + '"'
        yield _message('You are connected to database "' + executor.dbname + '" as user "' + executor.user + '" on ' + where + ' at port "' + executor.port + '".', sql, True)
    elif key == "\\T":
        names = table_format_names()
        if arg in names:
            _replace_settings(state, {"table_format": arg})
            yield _message("Changed table format to " + arg, sql, True)
        else:
            yield _message("Table format " + arg + " not recognized. Allowed formats:" + "".join("\n\t" + name for name in names) + "\nCurrently set to: " + settings.table_format, sql, True)
    elif key in ("\\echo", "\\qecho"):
        yield _message(pattern, sql, True)
    else:
        verbose = True if arg == "on" else False if arg == "off" else not settings.verbose_errors
        _replace_settings(state, {"verbose_errors": verbose})
        yield _message("Verbose errors on." if verbose else "off.", sql, True)


def _notice(title: list[str], diagnostic: psycopg.errors.Diagnostic) -> None:
    title[0] += "\n" + str(diagnostic.message_primary)
    if diagnostic.message_detail:
        title[0] += "\n" + diagnostic.message_detail


def _database_error_text(state: dict[str, object], error: psycopg.DatabaseError) -> str:
    message = str(error)
    if not _settings(state).verbose_errors:
        return message
    diagnostic = error.diag
    fields: list[tuple[str, object]] = [
        ("Severity", diagnostic.severity),
        ("Severity (non-localized)", diagnostic.severity_nonlocalized),
        ("SQLSTATE code", diagnostic.sqlstate),
        ("Message", diagnostic.message_primary),
        ("Detail", diagnostic.message_detail),
        ("Hint", diagnostic.message_hint),
        ("Position", diagnostic.statement_position),
        ("Internal position", diagnostic.internal_position),
        ("Internal query", diagnostic.internal_query),
        ("Where", diagnostic.context),
        ("Schema name", diagnostic.schema_name),
        ("Table name", diagnostic.table_name),
        ("Column name", diagnostic.column_name),
        ("Data type name", diagnostic.datatype_name),
        ("Constraint name", diagnostic.constraint_name),
        ("File", diagnostic.source_file),
        ("Line", diagnostic.source_line),
        ("Routine", diagnostic.source_function),
    ]
    return message + "\n" + "\n".join(label + ": " + str(value) for label, value in fields if value is not None)


def _execute_statement(state: dict[str, object], sql: str) -> Iterator[dict[str, object]]:
    special: Any = state["special"]
    parsed = cast(object, pgspecial.main.parse_special_command(sql))
    if not isinstance(parsed, tuple):
        raise TypeError("invalid special command")
    parts = cast(tuple[object, ...], parsed)
    command = str(parts[0])
    pattern = str(parts[2])
    key = _resolve_command(special, command)
    if key in ("\\nq", "\\ne", "\\c", "\\connect", "use", "USE", "\\q", ":q", "quit", "exit", "\\#", "\\refresh", "\\i", "\\o", "\\log-file", "\\conninfo", "\\T", "\\echo", "\\qecho", "\\v"):
        yield from _own_command(state, cast(str, key), pattern, sql)
        return
    if key == "\\do":
        state["not_implemented"] = True
        return
    connection = _connection(state)
    executor = cast(Executor, state["executor"])
    try:
        try:
            special_cursor: object = connection.cursor()
        except Exception:
            special_cursor = None
        raw_results = cast(object, special.execute(special_cursor, sql))
        if not isinstance(raw_results, Iterable):
            raise TypeError("invalid special results")
        for raw in cast(Iterable[object], raw_results):
            if not isinstance(raw, tuple):
                raise TypeError("invalid special result")
            title, rows, headers, status = cast(tuple[object, ...], raw)
            yield _make_result(_optional_text(title), rows, _headers(headers), _optional_text(status), sql, True, True, False)
    except CommandNotFound:
        query = _EXPLAIN + sql if _settings(state).explain_mode else sql
    except psycopg.errors.ProtocolViolation as error:
        if not executor.virtual_database:
            raise
        _reconnect(state, ReconnectRequest(database="", user="", host="", port=""))
        yield _message(str(error), sql, False)
        return
    else:
        return
    if executor.virtual_database and "show help" in sql.lower():
        pgresult = connection.pgconn.exec_(query.encode("utf-8"))
        command_status = cast(object, pgresult.command_status)
        status_text = command_status.decode() if isinstance(command_status, bytes) else None
        yield _make_result("", None, [], status_text, sql, True, False, False)
        return
    title_cell = cast(list[str], state["notice_title"])
    title_cell[0] = ""
    handler: Callable[[psycopg.errors.Diagnostic], None] = lambda diagnostic: _notice(title_cell, diagnostic)
    connection.add_notice_handler(handler)
    try:
        cursor = connection.cursor()
        cursor.execute(query.encode("utf-8"))
    finally:
        connection.remove_notice_handler(handler)
    description = cursor.description
    if description is not None:
        yield _make_result(title_cell[0], cursor, [column.name for column in description], cursor.statusmessage, sql, True, False, False)
    else:
        yield _make_result(title_cell[0], None, [], cursor.statusmessage, sql, True, False, False)


def _one_statement(state: dict[str, object], statement: str) -> Iterator[dict[str, object]]:
    special: Any = state["special"]
    restore = False
    sql = statement
    if sql.endswith("\\G"):
        if not bool(cast(object, special.expanded_output)):
            special.expanded_output = True
            restore = True
        sql = sql[:-2].strip()
    try:
        yield from _execute_statement(state, sql)
    except psycopg.DatabaseError as error:
        if _connection(state).closed != 0:
            raise
        yield _make_result(None, None, [], click.style(_database_error_text(state, error), fg="red"), sql, False, False, True)
    finally:
        if restore:
            special.expanded_output = False


def _run_statements(state: dict[str, object], text: str) -> Iterator[dict[str, object]]:
    for sql in _split_statements(text):
        if state["quit"] or state["not_implemented"]:
            return
        failed_database = False
        for result in _one_statement(state, sql):
            yield result
            if result["db_error"]:
                failed_database = True
        if failed_database and _settings(state).on_error != "RESUME":
            return


def evaluate_pgcli_command(session: Session, text: str, screen: TerminalSize) -> Result[Evaluation, EvaluateError]:
    start = time.time()
    special: Any = cast(Any, session.special.unwrap())
    state: dict[str, object] = {"settings": session.settings, "executor": session.executor, "special": special, "notice_title": [""], "quit": False, "not_implemented": False, "refresh_all": False}
    output: list[str] = []
    item_count = 0
    successful = True
    mutated = False
    meta_changed = False
    db_changed = False
    path_changed = False
    is_special = False
    execution_time = 0.0
    total_time = 0.0
    stripped = text.strip()
    named_query = stripped.startswith("\\n ") and not stripped.startswith(("\\ns ", "\\nd "))
    try:
        if stripped:
            results = _run_statements(state, text)
        else:
            results = iter([_make_result(None, None, [], None, "", False, False, False)])
        for result in results:
            execution_time = time.time() - start
            settings = _settings(state)
            title = cast(str | None, result["title"])
            status = cast(str | None, result["status"])
            sql = cast(str, result["sql"])
            headers = cast(list[str], result["headers"])
            raw_rows = result["rows"]
            rows: list[tuple[object, ...]] | None = None
            rowcount = -1
            type_names: list[str] = []
            if isinstance(raw_rows, psycopg.Cursor):
                cursor = cast(psycopg.Cursor[tuple[object, ...]], raw_rows)
                rowcount = cursor.rowcount
                if cursor.description is not None:
                    for column in cursor.description:
                        info = cursor.adapters.types.get(column.type_code)
                        type_names.append(info.name if info is not None else "")
                else:
                    type_names = ["" for _ in headers]
                if rowcount >= 0 and should_limit_rows(sql, rowcount, settings.row_limit, settings.explain_mode):
                    limit = min(settings.row_limit, rowcount)
                    rows = cursor.fetchmany(limit)
                    status = "SELECT " + str(limit)
                    rowcount = -1
                    click.secho("The result was limited to " + str(limit) + " rows", fg="red")
                else:
                    rows = cursor.fetchall()
            elif raw_rows is not None:
                rows = _plain_rows(raw_rows)
                type_names = ["" for _ in headers]
            if settings.hide_named_query_text and named_query and result["successful"] and result["special"] and title is not None and title.startswith("> "):
                title = None
            result_set = Nothing() if rows is None else Some(value=ResultSet(columns=CottList(values=headers), type_names=CottList(values=type_names), rows=Opaque(tag="pgcli.result-rows", value=rows), rowcount=rowcount))
            expanded = bool(cast(object, special.expanded_output)) or settings.expanded_output
            auto_expand = bool(cast(object, special.auto_expand)) or settings.auto_expand
            output_settings = OutputSettings(
                table_format=settings.table_format,
                column_date_formats=settings.column_date_formats,
                max_field_width=settings.max_field_width,
                decimal_format=settings.decimal_format,
                float_format=settings.float_format,
                missing_value=settings.null_string,
                expanded=expanded,
                max_width=Some(value=screen.columns) if auto_expand else Nothing(),
                header_casing=Some(value=session.catalog) if settings.case_column_headers else Nothing(),
                style=settings.output_style,
                tuples_only=settings.tuples_only,
                query=text,
            )
            formatted = format_output(Nothing() if title is None else Some(value=title), result_set, Nothing() if status is None else Some(value=status), output_settings, settings.explain_mode)
            if isinstance(formatted, Err):
                return Err[EvaluateError](error=EvaluateError_Failed(message=formatted.error.message))
            if formatted.value.items:
                output.append(formatted.value.text)
                item_count += formatted.value.items
            total_time = time.time() - start
            if result["successful"]:
                changes = classify_statement(sql, status or "")
                mutated = mutated or changes.mutated
                meta_changed = meta_changed or changes.meta_changed
                db_changed = db_changed or changes.db_changed
                path_changed = path_changed or changes.path_changed
            else:
                successful = False
            is_special = bool(result["special"])
    except KeyboardInterrupt:
        return Err[EvaluateError](error=EvaluateError_Interrupted())
    except psycopg.OperationalError as error:
        if _connection(state).closed != 0:
            return Err[EvaluateError](error=EvaluateError_ConnectionLost(message=str(error)))
        return Err[EvaluateError](error=EvaluateError_Failed(message=str(error)))
    except Exception as error:
        return Err[EvaluateError](error=EvaluateError_Failed(message=str(error)))
    if state["not_implemented"]:
        return Err[EvaluateError](error=EvaluateError_NotImplemented())
    refresh: RefreshKind
    if db_changed:
        refresh = RefreshKind_Reset()
    elif meta_changed or state["refresh_all"]:
        refresh = RefreshKind_All()
    elif path_changed:
        refresh = RefreshKind_SearchPath()
    else:
        refresh = RefreshKind_Nothing()
    query_outcome = QueryOutcome(query=text, successful=successful, total_time=total_time, execution_time=execution_time, meta_changed=meta_changed, db_changed=db_changed, path_changed=path_changed, mutated=mutated, is_special=is_special)
    updated = dataclasses.replace(session, settings=_settings(state), executor=cast(Executor, state["executor"]), last_query=text)
    return Ok(value=Evaluation(session=updated, output="\n".join(output), items=item_count, query=query_outcome, refresh=refresh, quit=bool(state["quit"])))
