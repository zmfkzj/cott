from __future__ import annotations

import contextlib
import re
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, cast

from cott_runtime import UNIT, CottList, Err, Nothing, Ok, Option, Some, U64, Unit
from prompt_toolkit.application import Application
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys

from real.harlequin.adapters import adapter_completions, cancel_queries, close_connection, commit_transaction, connect, execute_statements, fetch_result, load_catalog, rollback_transaction, toggle_transaction_mode
from real.harlequin.adapters_types import Connection, ConnectionError, ConnectionError_Failed, ConnectionError_InvalidOption, ConnectionError_ReadOnlyUnsupported, ConnectionRequest, ExecutedStatement, SettingValue_Text, SettingValue_Values
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.catalog import builtin_completions, catalog_completions, completion_set, join_completion_sets, normalize_catalog
from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.history import record_query, update_query
from real.harlequin.history_types import QueryRecord, QueryStatus, QueryStatus_Canceled, QueryStatus_Error, QueryStatus_Ok
from real.harlequin.ide import effective_limit, error_modal, run_bar_key
from real.harlequin.ide_types import LayoutState, Pane_RunBar, RunBar
from real.harlequin.results import new_grid
from real.harlequin.results_types import ResultSet
from real.harlequin.sqltext import redact_sql, selected_queries
from real.harlequin.sqltext_types import TextRange

_IDE_TAG: Final[str] = "harlequin.ide"
_SECRET_NAMES: Final[str] = "password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key"


def _state(session: IdeSession) -> dict[str, object]:
    handle = session.handle
    if handle.tag != _IDE_TAG:
        raise ValueError("The IDE handle is not a Harlequin IDE session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        raise ValueError("The IDE handle is malformed.")
    return cast(dict[str, object], raw)


def _lock(s: dict[str, object]) -> contextlib.AbstractContextManager[object]:
    return cast(contextlib.AbstractContextManager[object], s["lock"])


def _invalidate(s: dict[str, object]) -> None:
    with _lock(s):
        app = cast(Application[object], s["app"])
    app.invalidate()


def _notify(s: dict[str, object], done: list[bool], title: str | None, message: str, severity: str) -> None:
    with _lock(s):
        if done[0]:
            return
        cast(Callable[[str | None, str, str], None], s["notify"])(title, message, severity)
    _invalidate(s)


def _error(s: dict[str, object], done: list[bool], title: str, header: str, message: str) -> None:
    with _lock(s):
        if done[0]:
            return
        cast(Callable[[str, object], None], s["open_dialog"])("text", error_modal(title, header, message))
    _invalidate(s)


def _connection_error_text(error: ConnectionError) -> tuple[str, str]:
    if isinstance(error, ConnectionError_ReadOnlyUnsupported):
        return ("Harlequin could not connect to your database.", f"The {error.adapter} adapter does not support read-only connections.")
    if isinstance(error, ConnectionError_InvalidOption):
        return (error.title, error.message)
    failed: ConnectionError_Failed = error
    return (failed.title, failed.message)


def _print_connect_errors(s: dict[str, object], errors: list[ConnectionError]) -> None:
    with _lock(s):
        failures = list(errors)
    for failure in failures:
        title, message = _connection_error_text(failure)
        print(f"{title}\n\n{message}", file=sys.stderr)


def _do_exit(app: Application[object]) -> None:
    if app.is_running and not app.is_done:
        app.exit(result=2)


def _exit_app(app: Application[object]) -> None:
    loop = app.loop
    if app.is_running and loop is not None:
        loop.call_soon_threadsafe(lambda: _do_exit(app))
    else:
        app.pre_run_callables.append(lambda: _do_exit(app))
        loop = app.loop
        if app.is_running and loop is not None:
            loop.call_soon_threadsafe(lambda: _do_exit(app))


def _connect_worker(s: dict[str, object], errors: list[ConnectionError], done: list[bool]) -> None:
    with _lock(s):
        settings = cast(HarlequinSettings, s["settings"])
    opened = connect(settings.request)
    if isinstance(opened, Ok):
        connection = opened.value
        with _lock(s):
            exiting = done[0]
            if not exiting:
                s["connection"] = connection
        if exiting:
            close_connection(connection)
            return
        _invalidate(s)
        if connection.init_message:
            _notify(s, done, "Database Connected.", connection.init_message, "information")
        else:
            _notify(s, done, None, "Database Connected.", "information")
        _refresh_catalog(s, done)
        return
    with _lock(s):
        if done[0]:
            return
        errors.append(opened.error)
        app = cast(Application[object], s["app"])
    _exit_app(app)


def _catalog_worker(s: dict[str, object], done: list[bool], connection: Connection) -> None:
    loaded = load_catalog(connection)
    if isinstance(loaded, Err):
        _error(s, done, "Catalog Error", "Could not update data catalog", loaded.error.message)
        return
    catalog: CottList[CatalogEntry] = normalize_catalog(loaded.value)
    candidates = completion_set(builtin_completions())
    adapter = adapter_completions(connection)
    if isinstance(adapter, Ok):
        candidates = join_completion_sets(candidates, adapter.value)
    else:
        _notify(s, done, "Harlequin could not load completions from your adapter.", adapter.error.message, "warning")
    candidates = join_completion_sets(candidates, completion_set(catalog_completions(catalog)))
    with _lock(s):
        current = s["connection"]
        if done[0] or not isinstance(current, Connection) or current.session.tag != "harlequin.session" or connection.session.tag != "harlequin.session" or current.session.unwrap() is not connection.session.unwrap():
            return
        s["catalog"] = list(catalog)
        s["completions"] = candidates
    _invalidate(s)


def _refresh_catalog(s: dict[str, object], done: list[bool]) -> None:
    with _lock(s):
        connection = s["connection"]
        if done[0] or not isinstance(connection, Connection):
            return
    threading.Thread(target=lambda: _catalog_worker(s, done, connection), daemon=True).start()


def _set_running(s: dict[str, object], running: bool) -> None:
    s["running"] = running
    bar = cast(RunBar, s["run_bar"])
    s["run_bar"] = RunBar(limit_enabled=bar.limit_enabled, limit_text=bar.limit_text, limit_cursor=bar.limit_cursor, running=running)


def _run_query(s: dict[str, object], done: list[bool], gate: threading.Lock) -> None:
    with _lock(s):
        if done[0] or s["running"] is True or not isinstance(s["connection"], Connection) or "selection" not in s:
            return
        text, anchor, cursor = cast(Callable[[], tuple[str, int, int]], s["selection"])()
    statements = list(selected_queries(text, TextRange(start=min(anchor, cursor), end=max(anchor, cursor))))
    _run_statements(s, done, gate, statements)


def _run_statements(s: dict[str, object], done: list[bool], gate: threading.Lock, statements: list[str]) -> None:
    if not statements:
        return
    with _lock(s):
        connection = s["connection"]
        if done[0] or not isinstance(connection, Connection) or s["running"] is True:
            return
        layout = cast(LayoutState, s["layout"])
        s["layout"] = LayoutState(focus=layout.focus, sidebar_hidden=layout.sidebar_hidden, full_screen=False)
        _set_running(s, True)
        s["results_state"] = "loading"
        limit: Option[U64] = effective_limit(cast(RunBar, s["run_bar"]))
    _invalidate(s)
    threading.Thread(target=lambda: _query_worker(s, done, gate, connection, statements, limit), daemon=True).start()


def _secrets(request: ConnectionRequest) -> CottList[str]:
    secrets: list[str] = []
    for setting in request.settings:
        if re.search(_SECRET_NAMES, setting.name, re.IGNORECASE) is None:
            continue
        value = setting.value
        if isinstance(value, SettingValue_Text):
            secrets.append(value.value)
        elif isinstance(value, SettingValue_Values):
            secrets.extend(value.values)
    pair = "[\\w.\\-]*(?:" + _SECRET_NAMES + ")[\\w.\\-]*\\s*=\\s*(?:'([^']*)'|\"([^\"]*)\"|([^&;\\s]+))"
    for conn_str in request.conn_str:
        for match in re.finditer("://[^/?#@\\s]*?:([^/?#@\\s]+)@", conn_str):
            secrets.append(match.group(1))
        for match in re.finditer(pair, conn_str, re.IGNORECASE):
            for value in (match.group(1), match.group(2), match.group(3)):
                if value is not None:
                    secrets.append(value)
                    break
    return CottList(values=secrets)


def _history_warning(s: dict[str, object], done: list[bool], warned: list[bool], message: str) -> None:
    if not warned[0]:
        warned[0] = True
        _notify(s, done, "Query History", message, "warning")


def _record(s: dict[str, object], done: list[bool], warned: list[bool], path: Path, record: QueryRecord) -> int | None:
    saved = record_query(path, record)
    if isinstance(saved, Ok):
        return saved.value
    _history_warning(s, done, warned, saved.error.message)
    return None


def _update(s: dict[str, object], done: list[bool], warned: list[bool], path: Path, row: int | None, status: QueryStatus, rows: int | None, truncated: bool | None, elapsed: float | None, failure: str | None) -> None:
    if row is None:
        return
    updated = update_query(path, row, status, Nothing() if rows is None else Some(value=rows), Nothing() if truncated is None else Some(value=truncated), Nothing() if elapsed is None else Some(value=elapsed), Nothing() if failure is None else Some(value=failure))
    if isinstance(updated, Err):
        _history_warning(s, done, warned, updated.error.message)


def _query_worker(s: dict[str, object], done: list[bool], gate: threading.Lock, connection: Connection, statements: list[str], limit: Option[U64]) -> None:
    with gate:
        with _lock(s):
            if done[0]:
                return
        try:
            _execute_batch(s, done, connection, statements, limit)
        finally:
            with _lock(s):
                redraw = not done[0]
                if redraw:
                    _set_running(s, False)
                    if s["results_state"] == "loading":
                        results = cast(list[ResultSet], s["results"])
                        s["results_state"] = "ready" if results else "empty"
            if redraw:
                _invalidate(s)


def _execute_batch(s: dict[str, object], done: list[bool], connection: Connection, statements: list[str], limit: Option[U64]) -> None:
    with _lock(s):
        settings = cast(HarlequinSettings, s["settings"])
        context = cast(IdeContext, s["context"])
    started = time.monotonic()
    run_at = datetime.now(timezone.utc).isoformat() if settings.record_history else ""
    executed: list[ExecutedStatement] = list(execute_statements(connection, CottList(values=statements), limit, False))
    warned = [False]
    secrets: CottList[str] | None = _secrets(settings.request) if settings.record_history else None
    logged: list[int | None] = []
    first_failure: tuple[int, str, str] | None = None
    succeeded = 0
    for item in executed:
        failure = item.failure
        if isinstance(failure, Some):
            if first_failure is None:
                first_failure = (item.index, failure.value.title, failure.value.message)
        elif not isinstance(item.cursor, Some):
            succeeded += 1
        if secrets is not None:
            status: QueryStatus = QueryStatus_Ok()
            error_text: Option[str] = Nothing()
            if isinstance(failure, Some):
                status = QueryStatus_Canceled() if failure.value.title == "Query canceled" else QueryStatus_Error()
                error_text = Some(value=redact_sql(failure.value.message, secrets))
            record = QueryRecord(run_at=run_at, program="harlequin", connection=connection.connection_id, profile=settings.profile_name, adapter=context.descriptor.name, sql=redact_sql(item.sql, secrets), status=status, rows=Nothing(), truncated=Nothing(), elapsed_ms=Nothing(), error_text=error_text)
            logged.append(_record(s, done, warned, context.paths.query_log, record))
    results: list[ResultSet] = []
    for index, item in enumerate(executed):
        if not isinstance(item.cursor, Some):
            continue
        fetched = fetch_result(connection, item, limit, settings.viewer_max_rows)
        row = logged[index] if secrets is not None else None
        if isinstance(fetched, Ok):
            result = fetched.value
            results.append(result)
            succeeded += 1
            if secrets is not None:
                _update(s, done, warned, context.paths.query_log, row, QueryStatus_Ok(), result.fetched_row_count, result.truncated, float(result.elapsed_ms), None)
        else:
            problem = fetched.error
            if secrets is not None:
                status = QueryStatus_Canceled() if problem.title == "Query canceled" else QueryStatus_Error()
                _update(s, done, warned, context.paths.query_log, row, status, None, None, None, redact_sql(problem.message, secrets))
            if first_failure is None or item.index < first_failure[0]:
                first_failure = (item.index, problem.title, problem.message)
    grids = [new_grid(result) for result in results]
    with _lock(s):
        if done[0]:
            return
        s["results"] = results
        s["grids"] = grids
        s["result_index"] = 0
        s["results_state"] = "ready" if results else "empty"
        cast(Callable[[str], None], s["focus"])("focus_results_viewer")
    _invalidate(s)
    seconds = time.monotonic() - started
    noun = "query" if succeeded == 1 else "queries"
    if results:
        _notify(s, done, None, f"{succeeded} {noun} executed successfully in {seconds:.2f} seconds.", "information")
    elif succeeded:
        _notify(s, done, None, f"{succeeded} DDL/DML {noun} executed successfully in {seconds:.2f} seconds.", "information")
        _refresh_catalog(s, done)
    if first_failure is not None:
        _error(s, done, "Query Error", first_failure[1], first_failure[2])


def _cancel_query(s: dict[str, object], done: list[bool]) -> None:
    with _lock(s):
        context = cast(IdeContext, s["context"])
        connection = s["connection"]
        if done[0] or s["running"] is not True or not context.descriptor.implements_cancel or not isinstance(connection, Connection):
            return
    threading.Thread(target=lambda: _cancel_worker(s, done, connection), daemon=True).start()


def _cancel_worker(s: dict[str, object], done: list[bool], connection: Connection) -> None:
    canceled = cancel_queries(connection)
    if isinstance(canceled, Ok):
        _notify(s, done, None, "Queries canceled.", "error")
    else:
        _error(s, done, "Cancel Error", "Harlequin could not cancel your queries.", canceled.error.message)


def _transaction(s: dict[str, object], done: list[bool], gate: threading.Lock, action: str) -> None:
    with _lock(s):
        if done[0] or not isinstance(s["connection"], Connection):
            return
    threading.Thread(target=lambda: _transaction_worker(s, done, gate, action), daemon=True).start()


def _transaction_worker(s: dict[str, object], done: list[bool], gate: threading.Lock, action: str) -> None:
    with gate:
        with _lock(s):
            connection = s["connection"]
            if done[0] or not isinstance(connection, Connection):
                return
        started = time.monotonic()
        if action == "toggle":
            toggled = toggle_transaction_mode(connection)
            if isinstance(toggled, Ok):
                with _lock(s):
                    redraw = not done[0]
                    if redraw:
                        s["connection"] = toggled.value
                if redraw:
                    _invalidate(s)
            else:
                _error(s, done, "Transaction Error", "Harlequin could not change the transaction mode.", toggled.error.message)
            return
        if action == "commit":
            committed = commit_transaction(connection)
            if isinstance(committed, Err):
                _error(s, done, "Transaction Error", "Harlequin could not commit the transaction.", committed.error.message)
                return
            _notify(s, done, None, f"Transaction committed in {time.monotonic() - started:.2f} seconds.", "information")
            _refresh_catalog(s, done)
            return
        rolled = rollback_transaction(connection)
        if isinstance(rolled, Err):
            _error(s, done, "Transaction Error", "Harlequin could not roll back the transaction.", rolled.error.message)
            return
        _notify(s, done, None, f"Transaction rolled back in {time.monotonic() - started:.2f} seconds.", "information")


def _run_bar_focused(s: dict[str, object]) -> bool:
    with _lock(s):
        layout = cast(LayoutState, s["layout"])
        return isinstance(layout.focus, Pane_RunBar) and s["dialog"] is None


def _key_name(key: str, text: str) -> str:
    names = {"c-m": "enter", "c-j": "enter", "c-h": "backspace", "backspace": "backspace", "delete": "delete", "left": "left", "right": "right", "home": "home", "end": "end"}
    if key in names:
        return names[key]
    if text == " ":
        return "space"
    return text


def _run_bar_event(s: dict[str, object], done: list[bool], gate: threading.Lock, event: KeyPressEvent) -> None:
    press = event.key_sequence[-1]
    raw_key = press.key
    key = raw_key.value if isinstance(raw_key, Keys) else raw_key
    with _lock(s):
        step = run_bar_key(cast(RunBar, s["run_bar"]), _key_name(key, press.data), press.data)
        s["run_bar"] = step.bar
    if step.submit:
        _run_query(s, done, gate)
    _invalidate(s)


def _close(s: dict[str, object], done: list[bool], gate: threading.Lock) -> None:
    with _lock(s):
        done[0] = True
        connection = s["connection"]
    with gate:
        if isinstance(connection, Connection):
            close_connection(connection)


def _tunnel_notice(s: dict[str, object], done: list[bool]) -> None:
    with _lock(s):
        context = cast(IdeContext, s["context"])
    tunnel = context.tunnel
    if isinstance(tunnel, Some):
        value = tunnel.value
        ports = ", ".join(str(port) for port in value.local_ports)
        lines = [f"{value.host} forwarded to local port(s) {ports}" + (" (reused existing tunnel)" if value.reused else "")]
        lines.extend(value.warnings)
        _notify(s, done, "SSH tunnel", "\n".join(lines), "warning" if value.reused or len(value.warnings) > 0 else "information")


def install_query_actions(session: IdeSession) -> Unit:
    s = _state(session)
    errors: list[ConnectionError] = []
    done = [False]
    gate = threading.Lock()
    with _lock(s):
        handlers = cast(dict[str, Callable[[], None]], s["handlers"])
        handlers["run_query"] = lambda: _run_query(s, done, gate)
        handlers["code_editor.run_query"] = lambda: _run_query(s, done, gate)
        handlers["refresh_catalog"] = lambda: _refresh_catalog(s, done)
        handlers["cancel_query"] = lambda: _cancel_query(s, done)
        handlers["toggle_transaction_mode"] = lambda: _transaction(s, done, gate, "toggle")
        handlers["commit_transaction"] = lambda: _transaction(s, done, gate, "commit")
        handlers["rollback_transaction"] = lambda: _transaction(s, done, gate, "rollback")
        run_service: Callable[[list[str]], None] = lambda statements: _run_statements(s, done, gate, statements)
        s["run_statements"] = run_service
        refresh_service: Callable[[], None] = lambda: _refresh_catalog(s, done)
        s["refresh_catalog"] = refresh_service
        kb = cast(KeyBindings, s["kb"])
        bar_filter = Condition(lambda: _run_bar_focused(s))
        bar_callback: Callable[[KeyPressEvent], None] = lambda event: _run_bar_event(s, done, gate, event)
        for key in (Keys.Any, "c-m", "c-j", "c-h", "delete", "left", "right", "home", "end", " "):
            kb.add(key, filter=bar_filter)(bar_callback)
        on_exit = cast(list[Callable[[], None]], s["on_exit"])
        on_exit.append(lambda: _print_connect_errors(s, errors))
        on_exit.append(lambda: _close(s, done, gate))
    _tunnel_notice(s, done)
    threading.Thread(target=lambda: _connect_worker(s, errors, done), daemon=True).start()
    return UNIT
