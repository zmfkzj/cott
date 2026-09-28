import contextlib
import platform
import threading
import time
from collections.abc import Callable
from typing import Final, cast

from cott_runtime import UNIT, CottList, Ok, Option, Some, U64, Unit
from prompt_toolkit.application import Application

from real.harlequin.adapters_types import (
    AdapterKind,
    AdapterKind_Adbc,
    AdapterKind_BigQuery,
    AdapterKind_Cassandra,
    AdapterKind_Databricks,
    AdapterKind_DuckDb,
    AdapterKind_MySql,
    AdapterKind_NebulaGraph,
    AdapterKind_Odbc,
    AdapterKind_Postgres,
    AdapterKind_Sqlite,
    AdapterKind_Trino,
    Connection,
)
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.cli_types import HARLEQUIN_VERSION, HarlequinSettings
from real.harlequin.history import history_key, open_history_screen, recent_queries
from real.harlequin.history_types import HistoryOutcome_Close, HistoryOutcome_Reload, HistoryOutcome_Select, HistoryScreen, QueryRecord
from real.harlequin.ide import debug_modal, help_modal, text_modal_key
from real.harlequin.ide_types import DebugSection, TextModal, TextModalOutcome_Close, TextModalOutcome_Copy
from real.harlequin.keymap import help_lines
from real.harlequin.keymap_types import BoundKeySet
from real.harlequin.support import copy_to_clipboard, ssh_tunnel_alive
from real.harlequin.support_types import SshTunnel

_TAG: Final[str] = "harlequin.ide"
_HISTORY_LIMIT: Final[int] = 500
_TUNNEL_INTERVAL_S: Final[float] = 5.0


def _state_lock(state: dict[str, object]) -> contextlib.AbstractContextManager[object]:
    return cast(contextlib.AbstractContextManager[object], state["lock"])


def _handlers(state: dict[str, object]) -> dict[str, Callable[[], None]]:
    return cast(dict[str, Callable[[], None]], state["handlers"])


def _dialog_keys(state: dict[str, object]) -> dict[str, Callable[[str, str], None]]:
    return cast(dict[str, Callable[[str, str], None]], state["dialog_keys"])


def _context(state: dict[str, object]) -> IdeContext:
    return cast(IdeContext, state["context"])


def _connection(state: dict[str, object]) -> Connection | None:
    connection = state["connection"]
    return connection if isinstance(connection, Connection) else None


def _notify(state: dict[str, object], title: str | None, message: str, severity: str) -> None:
    with _state_lock(state):
        cast(Callable[[str | None, str, str], None], state["notify"])(title, message, severity)
        app = cast(Application[int], state["app"])
    app.invalidate()


def _open_dialog(state: dict[str, object], kind: str, model: object) -> None:
    with _state_lock(state):
        cast(Callable[[str, object], None], state["open_dialog"])(kind, model)
        app = cast(Application[int], state["app"])
    app.invalidate()


def _quit(state: dict[str, object]) -> None:
    cast(Application[int], state["app"]).exit(result=0)


def _focus(state: dict[str, object], action: str) -> None:
    cast(Callable[[str], None], state["focus"])(action)


def _register_focus(state: dict[str, object], name: str, action: str) -> None:
    handler: Callable[[], None] = lambda: _focus(state, action)
    _handlers(state)[name] = handler


def _show_help(state: dict[str, object]) -> None:
    with _state_lock(state):
        bound = cast(BoundKeySet, state["bound_handle"])
    _open_dialog(state, "text", help_modal(help_lines(bound)))


def _kind_name(kind: AdapterKind) -> str:
    if isinstance(kind, AdapterKind_DuckDb):
        return "DuckDb"
    if isinstance(kind, AdapterKind_Sqlite):
        return "Sqlite"
    if isinstance(kind, AdapterKind_Postgres):
        return "Postgres"
    if isinstance(kind, AdapterKind_MySql):
        return "MySql"
    if isinstance(kind, AdapterKind_Odbc):
        return "Odbc"
    if isinstance(kind, AdapterKind_BigQuery):
        return "BigQuery"
    if isinstance(kind, AdapterKind_Trino):
        return "Trino"
    if isinstance(kind, AdapterKind_Databricks):
        return "Databricks"
    if isinstance(kind, AdapterKind_Adbc):
        return "Adbc"
    if isinstance(kind, AdapterKind_Cassandra):
        return "Cassandra"
    if isinstance(kind, AdapterKind_NebulaGraph):
        return "NebulaGraph"
    return "Chdb"


def _option_text(value: Option[U64] | Option[str]) -> str:
    return str(value.value) if isinstance(value, Some) else "None"


def _settings_lines(settings: HarlequinSettings) -> list[str]:
    return [
        f"Theme: {settings.theme}",
        f"Keymaps: {', '.join(settings.keymap_names)}",
        f"Limit: {_option_text(settings.limit)}",
        f"Viewer Max Rows: {_option_text(settings.viewer_max_rows)}",
        f"Locale: {_option_text(settings.locale)}",
    ]


def _show_debug(state: dict[str, object]) -> None:
    with _state_lock(state):
        descriptor = _context(state).descriptor
        connection = _connection(state)
        settings = cast(HarlequinSettings, state["settings"])
    harlequin = DebugSection(title="Harlequin", body=CottList(values=[
        f"Version: {HARLEQUIN_VERSION}",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()}",
    ]))
    adapter = DebugSection(title="Adapter", body=CottList(values=[
        f"Kind: {_kind_name(descriptor.kind)}",
        f"Name: {descriptor.name}",
        f"Display Name: {descriptor.display_name}",
        f"Distribution: {descriptor.distribution}",
        f"Details: {descriptor.details}",
        f"Implements Read-Only: {descriptor.implements_read_only}",
        f"Implements Cancel: {descriptor.implements_cancel}",
        f"Implements Catalog Search: {descriptor.implements_catalog_search}",
        f"Implements Validate SQL: {descriptor.implements_validate_sql}",
    ]))
    if connection is None:
        connection_lines = ["Not connected."]
    else:
        mode = connection.transaction_mode
        label = mode.value.label if isinstance(mode, Some) else "None"
        connection_lines = [
            f"Connection ID: {connection.connection_id}",
            f"Driver Details: {connection.driver_details}",
            f"Transaction Mode: {label}",
        ]
    sections = CottList(values=[
        harlequin,
        adapter,
        DebugSection(title="Connection", body=CottList(values=connection_lines)),
        DebugSection(title="Settings", body=CottList(values=_settings_lines(settings))),
    ])
    _open_dialog(state, "text", debug_modal(sections))


def _visible_lines(state: dict[str, object]) -> U64:
    with _state_lock(state):
        _, rows = cast(Callable[[], tuple[int, int]], state["size"])()
    return max(rows - 8, 1)


def _text_key(state: dict[str, object], key: str, _text: str) -> None:
    visible_lines = _visible_lines(state)
    with _state_lock(state):
        raw = state["dialog"]
        if not isinstance(raw, tuple):
            return
        dialog = cast(tuple[object, ...], raw)
        if len(dialog) != 2 or dialog[0] != "text" or not isinstance(dialog[1], TextModal):
            return
        step = text_modal_key(dialog[1], key, visible_lines)
        if isinstance(step.outcome, TextModalOutcome_Close):
            cast(Callable[[], None], state["close_dialog"])()
        else:
            state["dialog"] = ("text", step.modal)
        app = cast(Application[int], state["app"])
    app.invalidate()
    if isinstance(step.outcome, TextModalOutcome_Copy):
        copied = copy_to_clipboard(step.outcome.text)
        if isinstance(copied, Ok):
            _notify(state, None, step.outcome.notice, "information")
        else:
            _notify(state, "Clipboard Error", copied.error.message, "error")


def _history_worker(state: dict[str, object], generation: list[int], ticket: int, screen: HistoryScreen, opening: bool) -> None:
    with _state_lock(state):
        log_path = _context(state).paths.query_log
    result = recent_queries(log_path, screen.filter, Some(value=_HISTORY_LIMIT))
    changed = False
    warning = False
    with _state_lock(state):
        if generation[0] != ticket:
            return
        if isinstance(result, Ok):
            if opening:
                if state["dialog"] is None:
                    cast(Callable[[str, object], None], state["open_dialog"])("history", (screen, list(result.value)))
                    changed = True
            else:
                raw = state["dialog"]
                if isinstance(raw, tuple):
                    dialog = cast(tuple[object, ...], raw)
                    if len(dialog) == 2 and dialog[0] == "history" and isinstance(dialog[1], tuple):
                        model = cast(tuple[object, ...], dialog[1])
                        if len(model) == 2 and isinstance(model[0], HistoryScreen) and model[0].filter == screen.filter:
                            state["dialog"] = ("history", (model[0], list(result.value)))
                            changed = True
        else:
            warning = True
        app = cast(Application[int], state["app"])
    if changed:
        app.invalidate()
    if warning:
        _notify(state, "Query History", "Harlequin could not read your query history.", "warning")


def _start_history(state: dict[str, object], generation: list[int], ticket: int, screen: HistoryScreen, opening: bool) -> None:
    threading.Thread(target=lambda: _history_worker(state, generation, ticket, screen, opening), daemon=True).start()


def _show_history(state: dict[str, object], generation: list[int]) -> None:
    with _state_lock(state):
        connection = _connection(state)
        generation[0] += 1
        ticket = generation[0]
    connection_id = connection.connection_id if connection is not None else ""
    _start_history(state, generation, ticket, open_history_screen(connection_id), True)


def _history_dialog_key(state: dict[str, object], generation: list[int], key: str, text: str) -> None:
    selected_sql: str | None = None
    reload_screen: HistoryScreen | None = None
    ticket = 0
    with _state_lock(state):
        raw = state["dialog"]
        if not isinstance(raw, tuple):
            return
        dialog = cast(tuple[object, ...], raw)
        if len(dialog) != 2 or dialog[0] != "history" or not isinstance(dialog[1], tuple):
            return
        model = cast(tuple[object, ...], dialog[1])
        if len(model) != 2 or not isinstance(model[0], HistoryScreen) or not isinstance(model[1], list):
            return
        raw_records = cast(list[object], model[1])
        if not all(isinstance(record, QueryRecord) for record in raw_records):
            return
        records = cast(list[QueryRecord], raw_records)
        step = history_key(model[0], CottList(values=records), key, text)
        outcome = step.outcome
        if isinstance(outcome, HistoryOutcome_Close):
            generation[0] += 1
            cast(Callable[[], None], state["close_dialog"])()
        elif isinstance(outcome, HistoryOutcome_Select):
            generation[0] += 1
            cast(Callable[[], None], state["close_dialog"])()
            selected_sql = outcome.sql
        elif isinstance(outcome, HistoryOutcome_Reload):
            state["dialog"] = ("history", (step.screen, []))
            generation[0] += 1
            ticket = generation[0]
            reload_screen = step.screen
        else:
            state["dialog"] = ("history", (step.screen, records))
        app = cast(Application[int], state["app"])
    app.invalidate()
    if reload_screen is not None:
        _start_history(state, generation, ticket, reload_screen, False)
    if selected_sql is not None:
        with _state_lock(state):
            new_buffer = state.get("new_buffer")
        if new_buffer is not None:
            cast(Callable[[str], None], new_buffer)(selected_sql)


def _watch_tunnel(state: dict[str, object], tunnel: SshTunnel) -> None:
    while True:
        time.sleep(_TUNNEL_INTERVAL_S)
        if not ssh_tunnel_alive(tunnel):
            _notify(state, None, f"The SSH tunnel to {tunnel.host} closed.", "error")
            return


def install_app_actions(session: IdeSession) -> Unit:
    if session.handle.tag != _TAG:
        raise ValueError("The IDE session handle is malformed.")
    raw = session.handle.unwrap()
    if not isinstance(raw, dict):
        raise ValueError("The IDE session handle is malformed.")
    state = cast(dict[str, object], raw)
    generation = [0]
    with _state_lock(state):
        handlers = _handlers(state)
        quit_handler: Callable[[], None] = lambda: _quit(state)
        handlers["quit"] = quit_handler
        for action in (
            "toggle_sidebar", "toggle_full_screen", "focus_query_editor",
            "focus_results_viewer", "focus_data_catalog", "focus_next", "focus_previous",
        ):
            _register_focus(state, action, action)
        for name, action in (
            ("code_editor.focus_results_viewer", "focus_results_viewer"),
            ("code_editor.focus_data_catalog", "focus_data_catalog"),
            ("data_catalog.focus_query_editor", "focus_query_editor"),
            ("data_catalog.focus_results_viewer", "focus_results_viewer"),
            ("results_viewer.focus_query_editor", "focus_query_editor"),
            ("results_viewer.focus_data_catalog", "focus_data_catalog"),
        ):
            _register_focus(state, name, action)
        help_handler: Callable[[], None] = lambda: _show_help(state)
        debug_handler: Callable[[], None] = lambda: _show_debug(state)
        history_handler: Callable[[], None] = lambda: _show_history(state, generation)
        handlers["help"] = help_handler
        handlers["show_debug_info"] = debug_handler
        handlers["show_query_history"] = history_handler
        keys = _dialog_keys(state)
        text_key: Callable[[str, str], None] = lambda key, text: _text_key(state, key, text)
        history_key_handler: Callable[[str, str], None] = lambda key, text: _history_dialog_key(state, generation, key, text)
        keys["text"] = text_key
        keys["history"] = history_key_handler
        tunnel = _context(state).tunnel
    if isinstance(tunnel, Some):
        active_tunnel = tunnel.value
        threading.Thread(target=lambda: _watch_tunnel(state, active_tunnel), daemon=True).start()
    return UNIT
