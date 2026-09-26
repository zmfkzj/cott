import contextlib
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Final, cast

from cott_runtime import U64, UNIT, CottList, Err, Nothing, Ok, Option, Some, Unit
from prompt_toolkit.application import Application
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys

from real.harlequin.adapters import adapter_completions, cancel_queries, close_connection, commit_transaction, connect, execute_statements, fetch_result, load_catalog, rollback_transaction, toggle_transaction_mode
from real.harlequin.adapters_types import Connection, ConnectionError, ConnectionError_Failed, ConnectionError_InvalidOption, ConnectionError_ReadOnlyUnsupported, ConnectionRequest, ExecutedStatement, SettingValue_Text
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.catalog import builtin_completions, catalog_completions, completion_set, join_completion_sets, normalize_catalog
from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.history import record_query, update_query
from real.harlequin.history_types import QueryRecord, QueryStatus, QueryStatus_Error, QueryStatus_Ok
from real.harlequin.ide import effective_limit, error_modal, run_bar_key
from real.harlequin.ide_types import LayoutState, Pane_RunBar, RunBar
from real.harlequin.results import new_grid
from real.harlequin.results_types import ResultSet
from real.harlequin.sqltext import redact_sql, redact_text, selected_queries
from real.harlequin.sqltext_types import TextRange

_IDE_TAG: Final[str] = "harlequin.ide"
_SECRET_HINTS: Final[str] = "password passwd pwd secret token key"


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


def _app(s: dict[str, object]) -> Application[object]:
    with _lock(s):
        return cast(Application[object], s["app"])


def _invalidate(s: dict[str, object]) -> None:
    _app(s).invalidate()


def _notify(s: dict[str, object], title: str | None, message: str, severity: str) -> None:
    with _lock(s):
        raw = s.get("notify")
        if raw is not None:
            cast(Callable[[str | None, str, str], None], raw)(title, message, severity)
    _invalidate(s)


def _error(s: dict[str, object], title: str, header: str, message: str) -> None:
    with _lock(s):
        raw = s.get("open_dialog")
        if raw is not None:
            cast(Callable[[str, object], None], raw)("text", error_modal(title, header, message))
    _invalidate(s)


def _connection(s: dict[str, object]) -> Connection | None:
    with _lock(s):
        raw = s.get("connection")
    return raw if isinstance(raw, Connection) else None


def _context(s: dict[str, object]) -> IdeContext:
    with _lock(s):
        return cast(IdeContext, s["context"])


def _settings(s: dict[str, object]) -> HarlequinSettings:
    with _lock(s):
        return cast(HarlequinSettings, s["settings"])


def _spawn(target: Callable[[], None]) -> None:
    threading.Thread(target=target, daemon=True).start()


def _secrets(request: ConnectionRequest) -> list[str]:
    hints = _SECRET_HINTS.split()
    out: list[str] = []
    for setting in request.settings:
        value = setting.value
        name = setting.name.lower()
        if isinstance(value, SettingValue_Text) and any(hint in name for hint in hints):
            out.append(value.value)
    return out


def _error_text(error: ConnectionError) -> tuple[str, str]:
    if isinstance(error, ConnectionError_ReadOnlyUnsupported):
        return ("Harlequin could not connect to your database.", f"The {error.adapter} adapter does not support read-only connections.")
    if isinstance(error, ConnectionError_InvalidOption):
        return (error.title, error.message)
    failed: ConnectionError_Failed = error
    return (failed.title, failed.message)


def _print_connect_error(cell: list[ConnectionError]) -> None:
    for error in cell:
        title, message = _error_text(error)
        print(f"{title}\n\n{message}", file=sys.stderr)


def _do_exit(app: Application[object]) -> None:
    if app.is_running and not app.is_done:
        app.exit(result=2)


def _exit_app(app: Application[object]) -> None:
    deadline = time.monotonic() + 30.0
    while not app.is_running and time.monotonic() < deadline:
        time.sleep(0.05)
    loop = app.loop
    if loop is not None:
        loop.call_soon_threadsafe(lambda: _do_exit(app))


def _connect_worker(s: dict[str, object], cell: list[ConnectionError]) -> None:
    result = connect(_settings(s).request)
    if isinstance(result, Ok):
        conn = result.value
        with _lock(s):
            s["connection"] = conn
        if conn.init_message:
            _notify(s, "Database Connected.", conn.init_message, "information")
        else:
            _notify(s, None, "Database Connected.", "information")
        _refresh_catalog(s)
        return
    with _lock(s):
        cell.append(result.error)
    _exit_app(_app(s))


def _catalog_worker(s: dict[str, object]) -> None:
    conn = _connection(s)
    if conn is None:
        return
    loaded = load_catalog(conn)
    if isinstance(loaded, Err):
        _error(s, "Catalog Error", "Could not update data catalog", loaded.error.message)
        return
    catalog: CottList[CatalogEntry] = normalize_catalog(loaded.value)
    joined = completion_set(builtin_completions())
    extra = adapter_completions(conn)
    if isinstance(extra, Ok):
        joined = join_completion_sets(joined, extra.value)
    else:
        _notify(s, None, "Harlequin could not load completions from your adapter.", "warning")
    joined = join_completion_sets(joined, completion_set(catalog_completions(catalog)))
    with _lock(s):
        s["catalog"] = list(catalog)
        s["completions"] = joined
    _invalidate(s)


def _refresh_catalog(s: dict[str, object]) -> None:
    _spawn(lambda: _catalog_worker(s))


def _run_query(s: dict[str, object]) -> None:
    with _lock(s):
        raw = s.get("selection")
    if raw is None:
        return
    text, anchor, cursor = cast(Callable[[], tuple[str, int, int]], raw)()
    statements = [q for q in selected_queries(text, TextRange(start=min(anchor, cursor), end=max(anchor, cursor)))]
    _run_statements(s, statements)


def _set_running(s: dict[str, object], running: bool) -> None:
    s["running"] = running
    bar = cast(RunBar, s["run_bar"])
    s["run_bar"] = RunBar(limit_enabled=bar.limit_enabled, limit_text=bar.limit_text, limit_cursor=bar.limit_cursor, running=running)


def _run_statements(s: dict[str, object], statements: list[str]) -> None:
    if not statements:
        return
    with _lock(s):
        raw = s.get("connection")
        if not isinstance(raw, Connection) or s.get("running") is True:
            return
        conn: Connection = raw
        layout = cast(LayoutState, s["layout"])
        s["layout"] = LayoutState(focus=layout.focus, sidebar_hidden=layout.sidebar_hidden, full_screen=False)
        _set_running(s, True)
        s["results_state"] = "loading"
        limit: Option[U64] = effective_limit(cast(RunBar, s["run_bar"]))
    _invalidate(s)
    _spawn(lambda: _query_worker(s, conn, statements, limit))


def _log(s: dict[str, object], warned: list[bool], record: QueryRecord | None, row: int | None, outcome: tuple[QueryStatus, int | None, bool | None, float | None, str | None]) -> int | None:
    if not _settings(s).record_history:
        return None
    path = _context(s).paths.query_log
    status, rows, truncated, elapsed, failure = outcome
    if record is not None:
        result = record_query(path, record)
        if isinstance(result, Ok):
            return result.value
        error = result.error
    else:
        if row is None:
            return None
        updated = update_query(path, row, status, Nothing() if rows is None else Some(value=rows), Nothing() if truncated is None else Some(value=truncated), Nothing() if elapsed is None else Some(value=elapsed), Nothing() if failure is None else Some(value=failure))
        if isinstance(updated, Ok):
            return row
        error = updated.error
    if not warned[0]:
        warned[0] = True
        _notify(s, "Query History", error.message, "warning")
    return None


def _query_worker(s: dict[str, object], conn: Connection, statements: list[str], limit: Option[U64]) -> None:
    try:
        _execute_batch(s, conn, statements, limit)
    finally:
        with _lock(s):
            _set_running(s, False)
            if s.get("results_state") == "loading":
                results = s.get("results")
                s["results_state"] = "ready" if isinstance(results, list) and results else "empty"
        _invalidate(s)


def _execute_batch(s: dict[str, object], conn: Connection, statements: list[str], limit: Option[U64]) -> None:
    settings = _settings(s)
    secrets = CottList(values=_secrets(settings.request))
    adapter = _context(s).descriptor.name
    warned = [False]
    started = time.monotonic()
    executed: list[ExecutedStatement] = list(execute_statements(conn, CottList(values=statements), limit, False))
    rows_logged: list[int | None] = []
    first_failure: tuple[str, str] | None = None
    succeeded = 0
    for item in executed:
        failure = item.failure
        status: QueryStatus = QueryStatus_Ok()
        error_text: str | None = None
        if isinstance(failure, Some):
            status = QueryStatus_Error()
            error_text = redact_text(failure.value.message, secrets)
            if first_failure is None:
                first_failure = (failure.value.title, failure.value.message)
        else:
            succeeded += 1
        record = QueryRecord(run_at=datetime.now(timezone.utc).isoformat(), program="harlequin", connection=conn.connection_id, profile=settings.profile_name, adapter=adapter, sql=redact_sql(item.sql, secrets), status=status, rows=Nothing(), truncated=Nothing(), elapsed_ms=Nothing(), error_text=Nothing() if error_text is None else Some(value=error_text))
        rows_logged.append(_log(s, warned, record, None, (status, None, None, None, None)))
    results: list[ResultSet] = []
    for item, row in zip(executed, rows_logged):
        if not isinstance(item.cursor, Some):
            continue
        fetched = fetch_result(conn, item, limit, settings.viewer_max_rows)
        if isinstance(fetched, Ok):
            result = fetched.value
            results.append(result)
            _log(s, warned, None, row, (QueryStatus_Ok(), result.fetched_row_count, result.truncated, float(result.elapsed_ms), None))
        else:
            err = fetched.error
            _log(s, warned, None, row, (QueryStatus_Error(), None, None, None, redact_text(err.message, secrets)))
            succeeded -= 1
            if first_failure is None:
                first_failure = (err.title, err.message)
    seconds = time.monotonic() - started
    noun = "query" if succeeded == 1 else "queries"
    if results:
        with _lock(s):
            s["results"] = results
            s["grids"] = [new_grid(r) for r in results]
            s["result_index"] = 0
            s["results_state"] = "ready"
            focus = s.get("focus")
            if focus is not None:
                cast(Callable[[str], None], focus)("focus_results_viewer")
        _notify(s, None, f"{succeeded} {noun} executed successfully in {seconds:.2f} seconds.", "information")
    elif succeeded > 0:
        _notify(s, None, f"{succeeded} DDL/DML {noun} executed successfully in {seconds:.2f} seconds.", "information")
        _refresh_catalog(s)
    if first_failure is not None:
        _error(s, "Query Error", first_failure[0], first_failure[1])


def _cancel_query(s: dict[str, object]) -> None:
    with _lock(s):
        running = s.get("running") is True
    if not running or not _context(s).descriptor.implements_cancel:
        return
    conn = _connection(s)
    if conn is not None:
        live: Connection = conn
        _spawn(lambda: _cancel_worker(s, live))


def _cancel_worker(s: dict[str, object], conn: Connection) -> None:
    result = cancel_queries(conn)
    if isinstance(result, Ok):
        _notify(s, None, "Queries canceled.", "error")
    else:
        _error(s, "Cancel Error", "Harlequin could not cancel your queries.", result.error.message)


def _transaction(s: dict[str, object], action: str) -> None:
    conn = _connection(s)
    if conn is not None:
        live: Connection = conn
        _spawn(lambda: _transaction_worker(s, live, action))


def _transaction_worker(s: dict[str, object], conn: Connection, action: str) -> None:
    started = time.monotonic()
    if action == "toggle":
        toggled = toggle_transaction_mode(conn)
        if isinstance(toggled, Ok):
            with _lock(s):
                s["connection"] = toggled.value
            _invalidate(s)
        else:
            _error(s, "Transaction Error", "Harlequin could not change the transaction mode.", toggled.error.message)
        return
    if action == "commit":
        committed = commit_transaction(conn)
        if isinstance(committed, Err):
            _error(s, "Transaction Error", "Harlequin could not commit the transaction.", committed.error.message)
            return
        _notify(s, None, f"Transaction committed in {time.monotonic() - started:.2f} seconds.", "information")
        _refresh_catalog(s)
        return
    rolled = rollback_transaction(conn)
    if isinstance(rolled, Err):
        _error(s, "Transaction Error", "Harlequin could not roll back the transaction.", rolled.error.message)
        return
    _notify(s, None, f"Transaction rolled back in {time.monotonic() - started:.2f} seconds.", "information")


def _run_bar_focused(s: dict[str, object]) -> bool:
    with _lock(s):
        layout = s.get("layout")
        dialog = s.get("dialog")
    return isinstance(layout, LayoutState) and isinstance(layout.focus, Pane_RunBar) and dialog is None


def _key_name(key: str, data: str) -> str:
    names: dict[str, str] = {"c-m": "enter", "c-j": "enter", "c-h": "backspace", "delete": "delete", "left": "left", "right": "right", "home": "home", "end": "end"}
    if key in names:
        return names[key]
    if data == " ":
        return "space"
    return data


def _run_bar_event(s: dict[str, object], event: KeyPressEvent) -> None:
    press = event.key_sequence[0]
    raw_key = press.key
    key = raw_key.value if isinstance(raw_key, Keys) else raw_key
    with _lock(s):
        step = run_bar_key(cast(RunBar, s["run_bar"]), _key_name(key, press.data), press.data)
        s["run_bar"] = step.bar
    if step.submit:
        _run_query(s)
    _invalidate(s)


def _close(s: dict[str, object]) -> None:
    conn = _connection(s)
    if conn is not None:
        close_connection(conn)


def _tunnel_notice(s: dict[str, object]) -> None:
    tunnel = _context(s).tunnel
    if isinstance(tunnel, Some):
        t = tunnel.value
        ports = ", ".join(str(p) for p in t.local_ports)
        lines = [f"{t.host} forwarded to local port(s) {ports}" + (" (reused existing tunnel)" if t.reused else "")]
        lines.extend(w for w in t.warnings)
        severity = "warning" if t.reused or len(t.warnings) > 0 else "information"
        _notify(s, "SSH tunnel", "\n".join(lines), severity)


def install_query_actions(session: IdeSession) -> Unit:
    s = _state(session)
    cell: list[ConnectionError] = []
    runner: Callable[[list[str]], None] = lambda statements: _run_statements(s, statements)
    on_key: Callable[[KeyPressEvent], None] = lambda event: _run_bar_event(s, event)
    with _lock(s):
        handlers = cast(dict[str, Callable[[], None]], s["handlers"])
        handlers["run_query"] = lambda: _run_query(s)
        handlers["code_editor.run_query"] = lambda: _run_query(s)
        handlers["refresh_catalog"] = lambda: _refresh_catalog(s)
        handlers["cancel_query"] = lambda: _cancel_query(s)
        handlers["toggle_transaction_mode"] = lambda: _transaction(s, "toggle")
        handlers["commit_transaction"] = lambda: _transaction(s, "commit")
        handlers["rollback_transaction"] = lambda: _transaction(s, "rollback")
        s["run_statements"] = runner
        s["refresh_catalog"] = lambda: _refresh_catalog(s)
        kb = cast(KeyBindings, s["kb"])
        kb.add(Keys.Any, filter=Condition(lambda: _run_bar_focused(s)))(on_key)
        on_exit = cast(list[Callable[[], None]], s["on_exit"])
        on_exit.append(lambda: _print_connect_error(cell))
        on_exit.append(lambda: _close(s))
    _tunnel_notice(s)
    _spawn(lambda: _connect_worker(s, cell))
    return UNIT
