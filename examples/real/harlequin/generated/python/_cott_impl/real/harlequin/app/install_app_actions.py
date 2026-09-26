import contextlib
import platform
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final, cast

from cott_runtime import UNIT, CottList, Ok, Some, Unit

from real.harlequin.adapters_types import Connection
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.history import history_key, open_history_screen, recent_queries
from real.harlequin.history_types import HistoryOutcome_Close, HistoryOutcome_Reload, HistoryOutcome_Select, HistoryScreen, QueryRecord
from real.harlequin.ide import debug_modal, help_modal, text_modal_key
from real.harlequin.ide_types import DebugSection, TextModal, TextModalOutcome_Close, TextModalOutcome_Copy
from real.harlequin.keymap import help_lines
from real.harlequin.keymap_types import BoundKeySet
from real.harlequin.support import copy_to_clipboard, ssh_tunnel_alive
from real.harlequin.support_types import SshTunnel

_TAG: Final[str] = "harlequin.ide"
_FOCUS_ACTIONS: Final[str] = "toggle_sidebar,toggle_full_screen,focus_query_editor,focus_results_viewer,focus_data_catalog,focus_next,focus_previous"
_PANE_FOCUS: Final[str] = "code_editor.focus_results_viewer,code_editor.focus_data_catalog,data_catalog.focus_query_editor,data_catalog.focus_results_viewer,results_viewer.focus_query_editor,results_viewer.focus_data_catalog"
_HISTORY_LIMIT: Final[int] = 500
_TUNNEL_INTERVAL_S: Final[float] = 5.0
_HARLEQUIN_VERSION: Final[str] = "2.15.0"


def _lock(s: dict[str, object]) -> contextlib.AbstractContextManager[object]:
    return cast(contextlib.AbstractContextManager[object], s["lock"])


def _invalidate(s: dict[str, object]) -> None:
    cast(Callable[[], None], s["invalidate"])()


def _notify(s: dict[str, object], title: str | None, message: str, severity: str) -> None:
    cast(Callable[[str | None, str, str], None], s["notify"])(title, message, severity)


def _open_dialog(s: dict[str, object], kind: str, model: object) -> None:
    cast(Callable[[str, object], None], s["open_dialog"])(kind, model)


def _close_dialog(s: dict[str, object]) -> None:
    cast(Callable[[], None], s["close_dialog"])()


def _handlers(s: dict[str, object]) -> dict[str, Callable[[], None]]:
    return cast(dict[str, Callable[[], None]], s["handlers"])


def _dialog_keys(s: dict[str, object]) -> dict[str, Callable[[str, str], None]]:
    return cast(dict[str, Callable[[str, str], None]], s["dialog_keys"])


def _context(s: dict[str, object]) -> IdeContext:
    return cast(IdeContext, s["context"])


def _connection(s: dict[str, object]) -> Connection | None:
    raw = s.get("connection")
    if isinstance(raw, Connection):
        return raw
    return None


def _quit(s: dict[str, object]) -> None:
    app: Any = s["app"]
    app.exit(result=0)


def _focus(s: dict[str, object], action: str) -> None:
    cast(Callable[[str], None], s["focus"])(action)


def _register_focus(s: dict[str, object], name: str, action: str) -> None:
    _handlers(s)[name] = lambda: _focus(s, action)


def _visible_lines(s: dict[str, object]) -> int:
    size = s.get("size")
    if size is None:
        return 20
    dims = cast(Callable[[], tuple[int, int]], size)()
    return max(dims[1] - 8, 1)


def _show_help(s: dict[str, object]) -> None:
    with _lock(s):
        bound = cast(BoundKeySet, s["bound_handle"])
    modal = help_modal(help_lines(bound))
    _open_dialog(s, "text", modal)
    _invalidate(s)


def _option_text(value: object) -> str:
    if isinstance(value, Some):
        return str(cast(Some[object], value).value)
    return "None"


def _settings_lines(settings: HarlequinSettings) -> list[str]:
    return [
        f"Theme: {settings.theme}",
        f"Keymaps: {', '.join(name for name in settings.keymap_names)}",
        f"Limit: {_option_text(settings.limit)}",
        f"Viewer Max Rows: {_option_text(settings.viewer_max_rows)}",
        f"Locale: {_option_text(settings.locale)}",
    ]


def _show_debug(s: dict[str, object]) -> None:
    with _lock(s):
        descriptor = _context(s).descriptor
        connection = _connection(s)
        settings = cast(HarlequinSettings, s["settings"])
    harlequin = DebugSection(title="Harlequin", body=CottList(values=[f"Version: {_HARLEQUIN_VERSION}", f"Python: {platform.python_version()}", f"Platform: {platform.platform()}"]))
    adapter = DebugSection(
        title="Adapter",
        body=CottList(values=[
            f"Name: {descriptor.name}",
            f"Display Name: {descriptor.display_name}",
            f"Distribution: {descriptor.distribution}",
            f"Details: {descriptor.details}",
            f"Implements Read-Only: {descriptor.implements_read_only}",
            f"Implements Cancel: {descriptor.implements_cancel}",
            f"Implements Catalog Search: {descriptor.implements_catalog_search}",
            f"Implements Validate SQL: {descriptor.implements_validate_sql}",
        ]),
    )
    if connection is None:
        connection_lines = ["Not connected."]
    else:
        mode = connection.transaction_mode
        mode_label = mode.value.label if isinstance(mode, Some) else "None"
        connection_lines = [f"Connection ID: {connection.connection_id}", f"Driver Details: {connection.driver_details}", f"Transaction Mode: {mode_label}"]
    connection_section = DebugSection(title="Connection", body=CottList(values=connection_lines))
    settings_section = DebugSection(title="Settings", body=CottList(values=_settings_lines(settings)))
    modal = debug_modal(CottList(values=[harlequin, adapter, connection_section, settings_section]))
    _open_dialog(s, "text", modal)
    _invalidate(s)


def _text_key(s: dict[str, object], key: str, text: str) -> None:
    visible = _visible_lines(s)
    with _lock(s):
        dialog = s.get("dialog")
        if not isinstance(dialog, tuple):
            return
        kind, model = cast(tuple[object, object], dialog)
        if kind != "text" or not isinstance(model, TextModal):
            return
        step = text_modal_key(model, key, visible)
        outcome = step.outcome
        if isinstance(outcome, TextModalOutcome_Close):
            _close_dialog(s)
        else:
            s["dialog"] = ("text", step.modal)
    if isinstance(outcome, TextModalOutcome_Copy):
        copied = copy_to_clipboard(outcome.text)
        if isinstance(copied, Ok):
            _notify(s, None, outcome.notice, "information")
        else:
            _notify(s, "Clipboard Error", copied.error.message, "error")
    _invalidate(s)


def _history_worker(s: dict[str, object], screen: HistoryScreen, opening: bool) -> None:
    with _lock(s):
        log_path = Path(_context(s).paths.query_log)
    result = recent_queries(log_path, screen.filter, Some(value=_HISTORY_LIMIT))
    with _lock(s):
        if isinstance(result, Ok):
            records = [record for record in result.value]
            if opening:
                _open_dialog(s, "history", (screen, records))
            else:
                dialog = s.get("dialog")
                if isinstance(dialog, tuple) and cast(tuple[object, object], dialog)[0] == "history":
                    s["dialog"] = ("history", (screen, records))
        else:
            _notify(s, "Query History", "Harlequin could not read your query history.", "warning")
    _invalidate(s)


def _start_history(s: dict[str, object], screen: HistoryScreen, opening: bool) -> None:
    threading.Thread(target=lambda: _history_worker(s, screen, opening), daemon=True).start()


def _show_history(s: dict[str, object]) -> None:
    with _lock(s):
        connection = _connection(s)
    connection_id = connection.connection_id if connection is not None else ""
    _start_history(s, open_history_screen(connection_id), True)


def _history_dialog_key(s: dict[str, object], key: str, text: str) -> None:
    selected_sql: str | None = None
    with _lock(s):
        dialog = s.get("dialog")
        if not isinstance(dialog, tuple):
            return
        kind, model = cast(tuple[object, object], dialog)
        if kind != "history" or not isinstance(model, tuple):
            return
        screen_raw, records_raw = cast(tuple[object, object], model)
        if not isinstance(screen_raw, HistoryScreen) or not isinstance(records_raw, list):
            return
        records = [item for item in cast(list[object], records_raw) if isinstance(item, QueryRecord)]
        step = history_key(screen_raw, CottList(values=records), key, text)
        outcome = step.outcome
        if isinstance(outcome, HistoryOutcome_Close):
            _close_dialog(s)
        elif isinstance(outcome, HistoryOutcome_Select):
            _close_dialog(s)
            selected_sql = outcome.sql
        else:
            s["dialog"] = ("history", (step.screen, records))
    if isinstance(outcome, HistoryOutcome_Reload):
        _start_history(s, step.screen, False)
    if selected_sql is not None:
        new_buffer = s.get("new_buffer")
        if new_buffer is not None:
            cast(Callable[[str], None], new_buffer)(selected_sql)
    _invalidate(s)


def _watch_tunnel(s: dict[str, object], tunnel: SshTunnel) -> None:
    while True:
        time.sleep(_TUNNEL_INTERVAL_S)
        if not ssh_tunnel_alive(tunnel):
            _notify(s, None, f"The SSH tunnel to {tunnel.host} closed.", "error")
            _invalidate(s)
            return


def install_app_actions(session: IdeSession) -> Unit:
    handle = session.handle
    if handle.tag != _TAG:
        raise ValueError("The IDE session handle is malformed.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        raise ValueError("The IDE session handle is malformed.")
    s = cast(dict[str, object], raw)
    with _lock(s):
        handlers = _handlers(s)
        handlers["quit"] = lambda: _quit(s)
        for action in _FOCUS_ACTIONS.split(","):
            _register_focus(s, action, action)
        for name in _PANE_FOCUS.split(","):
            _register_focus(s, name, name.split(".", 1)[1])
        handlers["help"] = lambda: _show_help(s)
        handlers["show_debug_info"] = lambda: _show_debug(s)
        handlers["show_query_history"] = lambda: _show_history(s)
        keys = _dialog_keys(s)
        keys["text"] = lambda key, text: _text_key(s, key, text)
        keys["history"] = lambda key, text: _history_dialog_key(s, key, text)
        tunnel = _context(s).tunnel
    if isinstance(tunnel, Some):
        watched = tunnel.value
        threading.Thread(target=lambda: _watch_tunnel(s, watched), daemon=True).start()
    return UNIT
