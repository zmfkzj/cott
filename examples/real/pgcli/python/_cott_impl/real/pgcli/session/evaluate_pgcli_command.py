import dataclasses
import io
import os
import pathlib
import re
import time
from collections.abc import Callable, Iterable, Iterator
from typing import Any, cast

import click
from configobj import ConfigObj
import pgspecial.iocommands
import pgspecial.main
import pgspecial.namedqueries
import psycopg
import psycopg.errors
import sqlparse
from pgspecial.main import CommandNotFound

from cott_runtime import CottContractViolation, CottList, Err, Nothing, Ok, Opaque, Result, Some, _cott_fixture_database, _cott_fixture_read, _cott_fixture_replace
from real.pgcli.connection import executor_transaction_status, reconnect_executor
from real.pgcli.connection_types import ConnectError_Failed, Executor, ReconnectRequest, TransactionStatus_Active, TransactionStatus_InTransaction
from real.pgcli.output import format_output, table_format_names
from real.pgcli.output_types import OutputSettings, ResultSet
from real.pgcli.parseutils import is_destructive
from real.pgcli.session import change_db_arguments, classify_statement, confirm_destructive_query, should_limit_rows
from real.pgcli.session_types import EvaluateError, EvaluateError_ConnectionLost, EvaluateError_Failed, EvaluateError_Interrupted, EvaluateError_NotImplemented, Evaluation, QueryOutcome, RefreshKind, RefreshKind_All, RefreshKind_Nothing, RefreshKind_Reset, RefreshKind_SearchPath, Session, SessionSettings, TerminalSize


def _settings(state: dict[str, object]) -> SessionSettings:
    return cast(SessionSettings, state["settings"])


def _connection(state: dict[str, object]) -> psycopg.Connection[tuple[object, ...]]:
    executor = cast(Executor, state["executor"])
    raw = executor.connection.unwrap()
    if not isinstance(raw, psycopg.Connection):
        raise TypeError("executor connection must be a psycopg connection")
    return cast(psycopg.Connection[tuple[object, ...]], raw)


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
    pieces = [str(piece) for piece in sqlparse.split(remaining)]
    if comments:
        if pieces:
            pieces[0] = "".join(comments) + pieces[0]
        else:
            pieces = ["".join(comments)]
    statements: list[str] = []
    for piece in pieces:
        sql = str(sqlparse.format(piece, strip_comments=True)).strip().rstrip(";").strip()
        if sql:
            statements.append(sql)
    return statements


def _result(title: str | None, rows: object, headers: list[str], status: str | None, sql: str, successful: bool, special: bool, db_error: bool) -> dict[str, object]:
    return {"title": title, "rows": rows, "headers": headers, "status": status, "sql": sql, "successful": successful, "special": special, "db_error": db_error}


def _message(message: str, sql: str, successful: bool) -> dict[str, object]:
    return _result(None, None, [], message, sql, successful, True, False)


def _resolve_command(special: Any, command: str) -> str | None:
    raw = cast(object, special.commands)
    if not isinstance(raw, dict):
        raise TypeError("special commands must be a dictionary")
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


def _read_command_file(path: pathlib.Path) -> str:
    try:
        return _cott_fixture_read(path).decode("utf-8")
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            with open(path, encoding="utf-8") as handle:
                return handle.read()
        if isinstance(error.__cause__, OSError):
            raise error.__cause__
        raise


def _touch_command_file(source: pathlib.Path, destination: pathlib.Path, append: bool) -> None:
    try:
        _cott_fixture_read(source)
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            if append:
                with open(destination, "a+", encoding="utf-8"):
                    return
            if not os.path.isfile(destination):
                with open(destination, "w", encoding="utf-8"):
                    return
            return
        if isinstance(error.__cause__, FileNotFoundError):
            try:
                _cott_fixture_replace(source, b"", create_parents=False)
            except CottContractViolation as replacement:
                if isinstance(replacement.__cause__, OSError):
                    raise replacement.__cause__
                raise
            return
        if isinstance(error.__cause__, OSError):
            raise error.__cause__
        raise


def _save_named_query(named: Any, name: str, query: str) -> None:
    raw = cast(object, named.config)
    if not isinstance(raw, ConfigObj):
        raise TypeError("named query configuration must be a ConfigObj")
    config: Any = raw
    filename = cast(object, config.filename)
    if not isinstance(filename, (str, pathlib.Path)):
        raise TypeError("named query configuration needs a filename")
    path = pathlib.Path(filename)
    try:
        _cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            named.save(name, query)
            return
        if not isinstance(error.__cause__, FileNotFoundError):
            if isinstance(error.__cause__, OSError):
                raise error.__cause__
            raise
    config.filename = None
    try:
        named.save(name, query)
        buffer = io.BytesIO()
        config.write(outfile=buffer)
    finally:
        config.filename = filename
    try:
        _cott_fixture_replace(path, buffer.getvalue(), create_parents=False)
    except CottContractViolation as error:
        if isinstance(error.__cause__, OSError):
            raise error.__cause__
        raise


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
        named: Any = pgspecial.namedqueries.NamedQueries.instance
        existing = cast(object, named.get(arg))
        editor = os.environ.get("PSQL_EDITOR") or os.environ.get("EDITOR") or os.environ.get("VISUAL") or None
        edited = cast(object, pgspecial.iocommands.open_external_editor(sql=existing if isinstance(existing, str) else "", editor=editor))
        if not isinstance(edited, tuple):
            raise TypeError("editor did not return a query and message")
        values = cast(tuple[object, ...], edited)
        if len(values) != 2:
            raise TypeError("editor did not return a query and message")
        query, message = values
        if message:
            yield _message(str(message), sql, True)
        new_query = str(query).strip() if query is not None else ""
        if not new_query:
            yield _message(arg + ": empty query, not saved.", sql, True)
        elif isinstance(existing, str) and new_query == existing:
            yield _message(arg + ": no changes.", sql, True)
        else:
            _save_named_query(named, arg, new_query)
            yield _message(arg + (": Saved" if isinstance(existing, str) else ": Created"), sql, True)
    elif key in ("\\c", "\\connect", "use", "USE"):
        args = list(change_db_arguments(pattern)) if arg else ["", "", "", ""]
        failure = _reconnect(state, ReconnectRequest(database=args[0], user=args[1], host=args[2], port=args[3]))
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
            contents = _read_command_file(pathlib.Path(os.path.expanduser(arg)))
        except OSError as error:
            yield _message(str(error), sql, False)
            return
        if settings.destructive_warning:
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
        source = pathlib.Path(os.path.expanduser(arg))
        destination = pathlib.Path(os.path.abspath(source))
        try:
            _touch_command_file(source, destination, False)
        except OSError as error:
            _replace_settings(state, {"output_file": Nothing()})
            yield _message(str(error) + "\nFile output disabled", sql, False)
            return
        _replace_settings(state, {"output_file": Some(value=str(destination))})
        yield _message('Writing to file "' + str(destination) + '"', sql, True)
    elif key == "\\log-file":
        if not arg:
            _replace_settings(state, {"log_file": Nothing()})
            yield _message("Logfile capture disabled", sql, True)
            return
        source = pathlib.Path(arg).expanduser()
        destination = source.absolute()
        try:
            _touch_command_file(source, destination, True)
        except OSError as error:
            _replace_settings(state, {"log_file": Nothing()})
            yield _message(str(error) + "\nLogfile capture disabled", sql, False)
            return
        _replace_settings(state, {"log_file": Some(value=str(destination))})
        yield _message('Writing to file "' + str(destination) + '"', sql, True)
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
    if diagnostic.message_primary is not None:
        title[0] += "\n" + diagnostic.message_primary
    if diagnostic.message_detail:
        title[0] += "\n" + diagnostic.message_detail


def _database_error_text(state: dict[str, object], error: psycopg.DatabaseError) -> str:
    message = str(error)
    if not _settings(state).verbose_errors:
        return message
    diag = error.diag
    fields: list[tuple[str, object]] = [
        ("Severity", diag.severity), ("Severity (non-localized)", diag.severity_nonlocalized),
        ("SQLSTATE code", diag.sqlstate), ("Message", diag.message_primary),
        ("Detail", diag.message_detail), ("Hint", diag.message_hint),
        ("Position", diag.statement_position), ("Internal position", diag.internal_position),
        ("Internal query", diag.internal_query), ("Where", diag.context),
        ("Schema name", diag.schema_name), ("Table name", diag.table_name),
        ("Column name", diag.column_name), ("Data type name", diag.datatype_name),
        ("Constraint name", diag.constraint_name), ("File", diag.source_file),
        ("Line", diag.source_line), ("Routine", diag.source_function),
    ]
    return message + "\n" + "\n".join(label + ": " + str(value) for label, value in fields if value is not None)


def _execute_statement(state: dict[str, object], sql: str) -> Iterator[dict[str, object]]:
    special: Any = state["special"]
    parsed = cast(object, pgspecial.main.parse_special_command(sql))
    if not isinstance(parsed, tuple):
        raise TypeError("invalid special command parse")
    parts = cast(tuple[object, ...], parsed)
    if len(parts) != 3:
        raise TypeError("invalid special command parse")
    command, _verbose, pattern = parts
    key = _resolve_command(special, str(command))
    if key in ("\\nq", "\\ne", "\\c", "\\connect", "use", "USE", "\\q", ":q", "quit", "exit", "\\#", "\\refresh", "\\i", "\\o", "\\log-file", "\\conninfo", "\\T", "\\echo", "\\qecho", "\\v"):
        yield from _own_command(state, cast(str, key), str(pattern), sql)
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
            raise TypeError("special command did not return results")
        for entry in cast(Iterable[object], raw_results):
            if not isinstance(entry, tuple):
                raise TypeError("special command returned an invalid result")
            values = cast(tuple[object, ...], entry)
            if len(values) != 4:
                raise TypeError("special command returned an invalid result")
            title, rows, headers, status = values
            if headers is None:
                names: list[str] = []
            elif isinstance(headers, Iterable):
                names = [str(header) for header in cast(Iterable[object], headers)]
            else:
                raise TypeError("special command returned invalid headers")
            yield _result(None if title is None else str(title), rows, names, None if status is None else str(status), sql, True, True, False)
    except CommandNotFound:
        query = "EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) " + sql if _settings(state).explain_mode else sql
    except psycopg.errors.ProtocolViolation as error:
        if not executor.virtual_database:
            raise
        _reconnect(state, ReconnectRequest(database="", user="", host="", port=""))
        yield _result(None, None, [], str(error), sql, False, True, True)
        return
    else:
        return
    if executor.virtual_database and "show help" in sql.lower():
        pgresult = connection.pgconn.exec_(query.encode("utf-8"))
        command_status = pgresult.command_status
        yield _result("", None, [], command_status.decode() if command_status is not None else "", sql, True, False, False)
        return
    title_cell: list[str] = [""]
    handler: Callable[[psycopg.errors.Diagnostic], None] = lambda diagnostic: _notice(title_cell, diagnostic)
    connection.add_notice_handler(handler)
    try:
        cursor = connection.cursor()
        cursor.execute(query.encode("utf-8"))
    finally:
        connection.remove_notice_handler(handler)
    description = cursor.description
    if description is not None:
        yield _result(title_cell[0], cursor, [column.name for column in description], cursor.statusmessage, sql, True, False, False)
    else:
        yield _result(title_cell[0], None, [], cursor.statusmessage, sql, True, False, False)


def _one_statement(state: dict[str, object], statement: str) -> Iterator[dict[str, object]]:
    special: Any = state["special"]
    sql = statement
    restore = False
    if sql.endswith("\\G"):
        if not bool(cast(object, special.expanded_output)):
            special.expanded_output = True
            restore = True
        sql = sql[:-2].strip()
    try:
        yield from _execute_statement(state, sql)
    except psycopg.errors.ProtocolViolation as error:
        executor = cast(Executor, state["executor"])
        if executor.virtual_database:
            _reconnect(state, ReconnectRequest(database="", user="", host="", port=""))
            yield _result(None, None, [], str(error), sql, False, False, True)
        elif _connection(state).closed != 0:
            raise
        else:
            yield _result(None, None, [], click.style(_database_error_text(state, error), fg="red"), sql, False, False, True)
    except psycopg.DatabaseError as error:
        if _connection(state).closed != 0:
            raise
        yield _result(None, None, [], click.style(_database_error_text(state, error), fg="red"), sql, False, False, True)
    finally:
        if restore:
            special.expanded_output = False


def _run_statements(state: dict[str, object], text: str) -> Iterator[dict[str, object]]:
    for sql in _split_statements(text):
        if state["quit"] or state["not_implemented"] or state["halt"]:
            return
        failed_database = False
        for result in _one_statement(state, sql):
            yield result
            if result["db_error"]:
                failed_database = True
        if failed_database and _settings(state).on_error != "RESUME":
            state["halt"] = True
            return


def _format_result(state: dict[str, object], session: Session, text: str, screen: TerminalSize, result: dict[str, object]) -> Result[tuple[str | None, int, str | None], EvaluateError]:
    settings = _settings(state)
    special: Any = state["special"]
    title = cast(str | None, result["title"])
    status = cast(str | None, result["status"])
    sql = cast(str, result["sql"])
    headers = cast(list[str], result["headers"])
    raw_rows = result["rows"]
    rows: list[tuple[object, ...]] | None = None
    rowcount = -1
    type_names: list[str] = []
    try:
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
        elif isinstance(raw_rows, list) and all(isinstance(row, tuple) for row in cast(list[object], raw_rows)):
            rows = cast(list[tuple[object, ...]], raw_rows)
            type_names = ["" for _ in headers]
        elif raw_rows is not None:
            if not isinstance(raw_rows, Iterable):
                raise TypeError("special command rows must be iterable")
            rows = []
            for row in cast(Iterable[object], raw_rows):
                if isinstance(row, tuple):
                    rows.append(cast(tuple[object, ...], row))
                elif isinstance(row, Iterable):
                    rows.append(tuple(cast(Iterable[object], row)))
                else:
                    raise TypeError("special command row must be iterable")
            type_names = ["" for _ in headers]
    except psycopg.DatabaseError as error:
        if _connection(state).closed != 0:
            raise
        title = None
        headers = []
        rows = None
        type_names = []
        status = click.style(_database_error_text(state, error), fg="red")
        result["successful"] = False
        result["special"] = False
        result["db_error"] = True
    stripped = text.strip()
    if settings.hide_named_query_text and stripped.startswith("\\n ") and not stripped.startswith(("\\ns ", "\\nd ")) and result["successful"] and result["special"] and title is not None and title.startswith("> "):
        title = None
    result_set = Nothing() if rows is None else Some(value=ResultSet(columns=CottList(values=headers), type_names=CottList(values=type_names), rows=Opaque(tag="pgcli.result-rows", value=rows), rowcount=rowcount))
    output_settings = OutputSettings(table_format=settings.table_format, column_date_formats=settings.column_date_formats, max_field_width=settings.max_field_width, decimal_format=settings.decimal_format, float_format=settings.float_format, missing_value=settings.null_string, expanded=bool(cast(object, special.expanded_output)) or settings.expanded_output, max_width=Some(value=screen.columns) if bool(cast(object, special.auto_expand)) or settings.auto_expand else Nothing(), header_casing=Some(value=session.catalog) if settings.case_column_headers else Nothing(), style=settings.output_style, tuples_only=settings.tuples_only, query=text)
    formatted = format_output(Nothing() if title is None else Some(value=title), result_set, Nothing() if status is None else Some(value=status), output_settings, settings.explain_mode)
    if isinstance(formatted, Err):
        return Err[EvaluateError](error=EvaluateError_Failed(message=formatted.error.message))
    if formatted.value.items:
        return Ok(value=(formatted.value.text, formatted.value.items, status))
    return Ok(value=(None, 0, status))


def evaluate_pgcli_command(session: Session, text: str, screen: TerminalSize) -> Result[Evaluation, EvaluateError]:
    start = time.time()
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
    state: dict[str, object] = {"settings": session.settings, "executor": session.executor, "quit": False, "not_implemented": False, "refresh_all": False, "halt": False}
    try:
        raw_special = session.special.unwrap()
        if not isinstance(raw_special, pgspecial.main.PGSpecial):
            raise TypeError("session special handle must contain a PGSpecial")
        special: Any = raw_special
        state["special"] = special
        if text.strip():
            try:
                _cott_fixture_database("read")
            except CottContractViolation as error:
                if error.message != "fixture adapters are inactive":
                    raise
            results = _run_statements(state, text)
        else:
            results = iter([_result(None, None, [], None, "", False, False, False)])
        for result in results:
            execution_time = time.time() - start
            formatted = _format_result(state, session, text, screen, result)
            if isinstance(formatted, Err):
                return Err[EvaluateError](error=formatted.error)
            rendered, count, status = formatted.value
            if rendered is not None:
                output.append(rendered)
                item_count += count
            total_time = time.time() - start
            if result["successful"]:
                changes = classify_statement(cast(str, result["sql"]), status or "")
                mutated = mutated or changes.mutated
                meta_changed = meta_changed or changes.meta_changed
                db_changed = db_changed or changes.db_changed
                path_changed = path_changed or changes.path_changed
            else:
                successful = False
            is_special = cast(bool, result["special"])
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
    query = QueryOutcome(query=text, successful=successful, total_time=total_time, execution_time=execution_time, meta_changed=meta_changed, db_changed=db_changed, path_changed=path_changed, mutated=mutated, is_special=is_special)
    updated = dataclasses.replace(session, settings=_settings(state), executor=cast(Executor, state["executor"]), last_query=text)
    return Ok(value=Evaluation(session=updated, output="\n".join(output), items=item_count, query=query, refresh=refresh, quit=cast(bool, state["quit"])))
