from __future__ import annotations

import datetime
import threading
import time
from collections.abc import Callable, Iterable
from types import SimpleNamespace
from typing import cast

from cott_runtime import CottList, Nothing, Ok, Opaque, Some
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion, ThreadedCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer, Float, FloatContainer, HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import NumberedMargin
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame
from pygments.lexers.sql import SqlLexer

from real.harlequin.catalog import buffer_identifiers, builtin_completions, complete, completion_set, render_tree
from real.harlequin.export import render_export_dialog
from real.harlequin.history import render_history
from real.harlequin.ide import initial_layout, layout_action, new_run_bar, render_confirm, render_context_menu, render_footer, render_input_modal, render_notifications, render_run_bar, render_tab_bar, render_text_modal, run_label, visible_panes
from real.harlequin.keymap import bind_keymaps, builtin_keymaps, footer_hints, terminal_key_sequence
from real.harlequin.results import render_grid, results_title
from real.harlequin.style import theme_style_rules
from real.harlequin.adapters_types import Connection
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.catalog_types import CatalogEntry, CompletionSet, TreeState
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.export_types import ExportDialog
from real.harlequin.history_types import HistoryScreen, QueryRecord
from real.harlequin.ide_types import ConfirmModal, ContextMenu, InputModal, LayoutState, Notification, Pane, Pane_Catalog, Pane_Editor, Pane_Results, Pane_RunBar, RunBar, Severity, Severity_Error, Severity_Information, Severity_Warning, TextModal
from real.harlequin.keymap_types import ActionScope, ActionScope_App, ActionScope_Catalog, ActionScope_Editor, ActionScope_Results, BoundKey, BoundKeySet, KeyMap
from real.harlequin.results_types import ResultSet, ResultsGrid
from real.harlequin.style_types import StyledLine


def _state(cells: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], cells["state"])


def _app(cells: dict[str, object]) -> Application[None]:
    return cast(Application[None], _state(cells)["app"])


def _windows(cells: dict[str, object]) -> dict[str, Window]:
    return cast(dict[str, Window], cells["windows"])


def _size(cells: dict[str, object]) -> tuple[int, int]:
    size = _app(cells).output.get_size()
    return size.columns, size.rows


def _fragments(lines: Iterable[StyledLine]) -> StyleAndTextTuples:
    fragments: StyleAndTextTuples = []
    for index, line in enumerate(lines):
        if index:
            fragments.append(("", "\n"))
        for span in line.spans:
            fragments.append((span.style, span.text))
    return fragments


def _dimensions(window: Window, fallback: tuple[int, int]) -> tuple[int, int]:
    info = window.render_info
    if info is None:
        return max(0, fallback[0]), max(0, fallback[1])
    return max(0, info.window_width), max(0, info.window_height)


def _pane(pane: Pane) -> str:
    if isinstance(pane, Pane_Catalog):
        return "Catalog"
    if isinstance(pane, Pane_Editor):
        return "Editor"
    if isinstance(pane, Pane_RunBar):
        return "RunBar"
    return "Results"


def _layout(state: dict[str, object]) -> LayoutState:
    return cast(LayoutState, state["layout"])


def _visible(cells: dict[str, object], name: str) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        return any(_pane(pane) == name for pane in visible_panes(_layout(state)))


def _scope(state: dict[str, object]) -> ActionScope:
    focus = _layout(state).focus
    if isinstance(focus, Pane_Catalog):
        return ActionScope_Catalog()
    if isinstance(focus, Pane_Results):
        return ActionScope_Results()
    return ActionScope_Editor()


def _buffer(state: dict[str, object]) -> Buffer:
    buffers = cast(list[dict[str, object]], state["buffers"])
    return cast(Buffer, buffers[min(max(0, cast(int, state["active"])), len(buffers) - 1)]["buffer"])


def _completions(cells: dict[str, object], document: Document, complete_event: CompleteEvent) -> list[Completion]:
    prefix = document.get_word_before_cursor(WORD=True)
    if not prefix:
        return []
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        candidates = cast(CompletionSet, state["completions"])
    if candidates.tag != "harlequin.completions":
        raise TypeError("invalid completion handle")
    return [Completion(text=item.value, start_position=-len(prefix), display=item.label, display_meta=item.type_label) for item in complete(candidates, buffer_identifiers(document.text), prefix, 100)]


def _editor(cells: dict[str, object]) -> Window:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        buffer = _buffer(state)
        editors = cast(dict[int, Window], cells["editors"])
        identity = id(buffer)
        window = editors.get(identity)
        if window is None:
            get_completions: Callable[[Document, CompleteEvent], Iterable[Completion]] = lambda document, event: _completions(cells, document, event)
            buffer.completer = ThreadedCompleter(cast(Completer, SimpleNamespace(get_completions=get_completions)))
            window = Window(content=BufferControl(buffer=buffer, lexer=PygmentsLexer(SqlLexer)), left_margins=[NumberedMargin()], height=Dimension(weight=1))
            editors[identity] = window
        return window


def _focus(cells: dict[str, object], action: str) -> None:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        current = layout_action(_layout(state), action)
        state["layout"] = current
        target = _editor(cells) if isinstance(current.focus, Pane_Editor) else _windows(cells)[_pane(current.focus)]
        app = _app(cells)
        app.layout.focus(target)
    app.invalidate()


def _notify(cells: dict[str, object], title: str | None, message: str, severity: str) -> None:
    level: Severity
    if severity == "error":
        level = Severity_Error()
    elif severity == "warning":
        level = Severity_Warning()
    else:
        level = Severity_Information()
    note = Notification(title=Some(value=title) if title is not None else Nothing(), message=message, severity=level, expires_at_ms=int(time.monotonic() * 1000) + 5000)
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        cast(list[Notification], state["notifications"]).append(note)
    _app(cells).invalidate()


def _open_dialog(cells: dict[str, object], kind: str, model: object) -> None:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        state["dialog"] = (kind, model)
    _app(cells).invalidate()


def _close_dialog(cells: dict[str, object]) -> None:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        state["dialog"] = None
    _app(cells).invalidate()


def _dialog_kind(state: dict[str, object]) -> str | None:
    opened = state["dialog"]
    if opened is None:
        return None
    kind = cast(tuple[str, object], opened)[0]
    return kind if kind in cast(dict[str, Callable[[str, str], None]], state["dialog_keys"]) else None


def _action(state: dict[str, object], keys: list[BoundKey]) -> BoundKey | None:
    handlers = cast(dict[str, Callable[[], None]], state["handlers"])
    focused = _scope(state)
    for priority in (True, False):
        for scope in (focused, ActionScope_App()):
            for key in keys:
                if key.priority == priority and key.scope == scope and key.action in handlers:
                    return key
    return None


def _active(cells: dict[str, object], keys: list[BoundKey]) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        if state["dialog"] is not None:
            return _dialog_kind(state) is not None
        return _action(state, keys) is not None


def _dialog_active(cells: dict[str, object]) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        return _dialog_kind(state) is not None


def _key_name(event: KeyPressEvent) -> str:
    prefix = "alt+" if len(event.key_sequence) > 1 and event.key_sequence[0].key == Keys.Escape else ""
    last = event.key_sequence[-1].key
    value = last.value if isinstance(last, Keys) else last
    if value == Keys.Any.value:
        value = event.data
    names = {"c-m": "enter", "c-i": "tab", "c-h": "backspace", "s-tab": "shift+tab", " ": "space"}
    if value in names:
        return prefix + names[value]
    if value.startswith("c-s-"):
        return prefix + "ctrl+shift+" + value[4:]
    if value.startswith("c-"):
        return prefix + "ctrl+" + value[2:]
    if value.startswith("s-"):
        return prefix + "shift+" + value[2:]
    return prefix + value


def _typed(event: KeyPressEvent) -> str:
    return event.data if len(event.data) == 1 and event.data.isprintable() else ""


def _press(cells: dict[str, object], keys: list[BoundKey], event: KeyPressEvent) -> None:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        kind = _dialog_kind(state)
        action = _action(state, keys) if state["dialog"] is None else None
        dialogs = cast(dict[str, Callable[[str, str], None]], state["dialog_keys"])
        handlers = cast(dict[str, Callable[[], None]], state["handlers"])
    if kind is not None:
        dialogs[kind](_key_name(event), _typed(event))
    elif action is not None:
        handlers[action.action]()


def _dialog_any(cells: dict[str, object], event: KeyPressEvent) -> None:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        kind = _dialog_kind(state)
        dialogs = cast(dict[str, Callable[[str, str], None]], state["dialog_keys"])
    if kind is not None:
        dialogs[kind](_key_name(event), _typed(event))


def _catalog_tabs(state: dict[str, object]) -> list[str]:
    settings = cast(HarlequinSettings, state["settings"])
    tabs = ["Databases"]
    if isinstance(settings.show_files, Some):
        tabs.append("Files")
    if isinstance(settings.show_s3, Some):
        tabs.append("S3")
    return tabs


def _catalog_tabs_visible(cells: dict[str, object]) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        return len(_catalog_tabs(state)) > 1


def _catalog_tabs_text(cells: dict[str, object]) -> StyleAndTextTuples:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        tabs = _catalog_tabs(state)
        selected = cast(str, state["catalog_tab"])
        columns, _ = _size(cells)
        width, _ = _dimensions(_windows(cells)["Catalog"], (columns // 4, 1))
        line = render_tab_bar(CottList(values=tabs), tabs.index(selected) if selected in tabs else 0, min(width, 65535))
    return _fragments((line,))


def _catalog_text(cells: dict[str, object]) -> StyleAndTextTuples:
    columns, rows = _size(cells)
    width, height = _dimensions(_windows(cells)["Catalog"], (columns // 4 - 2, rows - 4))
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        tab = cast(str, state["catalog_tab"])
        entries_key, tree_key = ("files", "files_tree") if tab == "Files" else ("s3", "s3_tree") if tab == "S3" else ("catalog", "tree")
        tree = cast(TreeState, state[tree_key])
        frame = render_tree(CottList(values=cast(list[CatalogEntry], state[entries_key])), tree, width, height, isinstance(_layout(state).focus, Pane_Catalog))
        if frame.first_row != tree.first_row:
            state[tree_key] = TreeState(expanded=tree.expanded, cursor=tree.cursor, first_row=frame.first_row)
    return _fragments(frame.lines)


def _editor_tabs_visible(cells: dict[str, object]) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        return len(cast(list[dict[str, object]], state["buffers"])) > 1


def _editor_tabs(cells: dict[str, object]) -> StyleAndTextTuples:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        titles = [cast(str, item["title"]) for item in cast(list[dict[str, object]], state["buffers"])]
        columns, _ = _size(cells)
        width, _ = _dimensions(_editor(cells), (columns * 3 // 4, 1))
        line = render_tab_bar(CottList(values=titles), cast(int, state["active"]), min(width, 65535))
    return _fragments((line,))


def _run_text(cells: dict[str, object]) -> StyleAndTextTuples:
    columns, _ = _size(cells)
    width, _ = _dimensions(_windows(cells)["RunBar"], (columns * 3 // 4, 1))
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        connection = state["connection"]
        buffer = _buffer(state)
        selection = ""
        if buffer.selection_state is not None:
            start, end = buffer.document.selection_range()
            selection = buffer.text[start:end]
        transaction = connection.transaction_mode if isinstance(connection, Connection) else Nothing()
        line = render_run_bar(cast(RunBar, state["run_bar"]), transaction, cast(IdeContext, state["context"]).descriptor.implements_cancel, run_label(selection, True), bool(buffer.text.strip()), isinstance(_layout(state).focus, Pane_RunBar), min(width, 65535))
    return _fragments((line,))


def _result(state: dict[str, object]) -> ResultSet | None:
    results = cast(list[ResultSet], state["results"])
    return results[min(max(0, cast(int, state["result_index"])), len(results) - 1)] if results else None


def _result_title(cells: dict[str, object]) -> str:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        if state["results_state"] == "loading":
            return "Running Query"
        result = _result(state)
        if result is not None and state["results_state"] == "ready":
            return results_title(result, cast(IdeContext, state["context"]).number_format)
        return "Query Results"


def _result_tabs_visible(cells: dict[str, object]) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        return len(cast(list[ResultSet], state["results"])) > 1


def _result_tabs(cells: dict[str, object]) -> StyleAndTextTuples:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        count = len(cast(list[ResultSet], state["results"]))
        columns, _ = _size(cells)
        width, _ = _dimensions(_windows(cells)["Results"], (columns * 3 // 4, 1))
        line = render_tab_bar(CottList(values=[f"Result {index + 1}" for index in range(count)]), cast(int, state["result_index"]), min(width, 65535))
    return _fragments((line,))


def _result_text(cells: dict[str, object]) -> StyleAndTextTuples:
    columns, rows = _size(cells)
    width, height = _dimensions(_windows(cells)["Results"], (columns * 3 // 4 - 2, rows // 2 - 2))
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        grids = cast(list[ResultsGrid], state["grids"])
        if state["results_state"] != "ready" or not grids:
            return []
        index = min(max(0, cast(int, state["result_index"])), len(grids) - 1)
        grid = grids[index]
        if grid.result.row_count == 0:
            return [("class:hq.muted", "Query Returned No Records")]
        frame = render_grid(grid, width, height, isinstance(_layout(state).focus, Pane_Results), cast(IdeContext, state["context"]).number_format)
        if frame.first_row != grid.first_row or frame.first_column != grid.first_column:
            grids[index] = ResultsGrid(result=grid.result, cursor=grid.cursor, anchor=grid.anchor, first_row=frame.first_row, first_column=frame.first_column)
    return _fragments(frame.lines)


def _footer(cells: dict[str, object]) -> StyleAndTextTuples:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        columns, _ = _size(cells)
        line = render_footer(footer_hints(cast(BoundKeySet, state["bound_handle"]), _scope(state)), min(columns, 65535))
    return _fragments((line,))


def _dialog_width(cells: dict[str, object]) -> int:
    columns, _ = _size(cells)
    return max(1, min(columns - 4, 100))


def _has_dialog(cells: dict[str, object]) -> bool:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        return state["dialog"] is not None


def _dialog_text(cells: dict[str, object]) -> StyleAndTextTuples:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        opened = state["dialog"]
        if opened is None:
            return []
        kind, model = cast(tuple[str, object], opened)
        width = _dialog_width(cells)
        _, rows = _size(cells)
        height = max(rows - 6, 3)
        if kind == "text" and isinstance(model, TextModal):
            return _fragments(render_text_modal(model, width, height))
        if kind == "input" and isinstance(model, InputModal):
            return _fragments(render_input_modal(model, width))
        if kind == "confirm" and isinstance(model, ConfirmModal):
            return _fragments(render_confirm(model, width))
        if kind == "menu" and isinstance(model, ContextMenu):
            return _fragments(render_context_menu(model, min(width, 65535)))
        if kind == "export" and isinstance(model, ExportDialog):
            return _fragments(render_export_dialog(model, width))
        if kind == "history" and isinstance(model, tuple):
            pair = cast(tuple[object, ...], model)
            if len(pair) == 2 and isinstance(pair[0], HistoryScreen) and isinstance(pair[1], list):
                records = cast(list[object], pair[1])
                if all(isinstance(record, QueryRecord) for record in records):
                    offset = datetime.datetime.now().astimezone().utcoffset()
                    minutes = 0 if offset is None else int(offset.total_seconds() // 60)
                    return _fragments(render_history(pair[0], CottList(values=cast(list[QueryRecord], records)), width, height, minutes))
    return []


def _live(cells: dict[str, object], now: int) -> list[Notification]:
    state = _state(cells)
    with cast(threading.RLock, state["lock"]):
        notes = cast(list[Notification], state["notifications"])
        live = [note for note in notes if note.expires_at_ms > now]
        if len(live) != len(notes):
            notes[:] = live
        return live


def _notifications(cells: dict[str, object]) -> StyleAndTextTuples:
    now = int(time.monotonic() * 1000)
    return _fragments(render_notifications(CottList(values=_live(cells, now)), now, 60))


def _register(cells: dict[str, object], kb: KeyBindings, sequence: tuple[str, ...], group: list[BoundKey]) -> None:
    predicate: Callable[[], bool] = lambda: _active(cells, group)
    callback: Callable[[KeyPressEvent], None] = lambda event: _press(cells, group, event)
    kb.add(*sequence, filter=Condition(predicate), eager=any(key.priority for key in group))(callback)


def build_ide(settings: HarlequinSettings, context: IdeContext, keymaps: CottList[KeyMap]) -> IdeSession:
    builtin = builtin_keymaps()
    bound_result = bind_keymaps(CottList(values=[*builtin, *keymaps]), settings.keymap_names)
    if not isinstance(bound_result, Ok):
        bound_result = bind_keymaps(builtin, CottList(values=["vscode"]))
    if not isinstance(bound_result, Ok):
        raise RuntimeError("Builtin vscode keymap failed to bind")
    bound_handle = bound_result.value
    if bound_handle.handle.tag != "harlequin.bound_keys":
        raise TypeError("invalid bound key handle")
    bound = cast(tuple[BoundKey, ...], bound_handle.handle.unwrap())
    state: dict[str, object] = {
        "lock": threading.RLock(), "settings": settings, "context": context,
        "bound_handle": bound_handle, "bound": bound, "connection": None, "running": False,
        "buffers": [{"title": "Tab 1", "buffer": Buffer(multiline=True)}], "active": 0, "tab_counter": 1,
        "layout": initial_layout(), "run_bar": new_run_bar(settings.limit),
        "results": [], "grids": [], "result_index": 0, "results_state": "empty",
        "catalog": [], "tree": TreeState(expanded=CottList(values=[]), cursor=0, first_row=0),
        "catalog_tab": "Databases", "files": [], "files_tree": TreeState(expanded=CottList(values=[]), cursor=0, first_row=0),
        "s3": [], "s3_tree": TreeState(expanded=CottList(values=[]), cursor=0, first_row=0),
        "completions": completion_set(builtin_completions()), "notifications": [], "dialog": None,
        "handlers": {}, "dialog_keys": {}, "on_exit": [], "on_crash": [],
    }
    windows: dict[str, Window] = {}
    editors: dict[int, Window] = {}
    cells: dict[str, object] = {"state": state, "windows": windows, "editors": editors}
    windows["Catalog"] = Window(content=FormattedTextControl(lambda: _catalog_text(cells), focusable=True), width=Dimension(weight=1), height=Dimension(weight=1))
    windows["RunBar"] = Window(content=FormattedTextControl(lambda: _run_text(cells), focusable=True), height=1)
    windows["Results"] = Window(content=FormattedTextControl(lambda: _result_text(cells), focusable=True), height=Dimension(weight=1))
    editor_window = _editor(cells)
    catalog = ConditionalContainer(Frame(HSplit([
        ConditionalContainer(Window(content=FormattedTextControl(lambda: _catalog_tabs_text(cells)), height=1), filter=Condition(lambda: _catalog_tabs_visible(cells))),
        windows["Catalog"],
    ]), title="Data Catalog", width=Dimension(weight=1)), filter=Condition(lambda: _visible(cells, "Catalog")))
    editor = ConditionalContainer(Frame(HSplit([
        ConditionalContainer(Window(content=FormattedTextControl(lambda: _editor_tabs(cells)), height=1), filter=Condition(lambda: _editor_tabs_visible(cells))),
        DynamicContainer(lambda: _editor(cells)),
    ]), title="Query Editor", height=Dimension(weight=1)), filter=Condition(lambda: _visible(cells, "Editor")))
    run_bar = ConditionalContainer(windows["RunBar"], filter=Condition(lambda: _visible(cells, "RunBar")))
    results = ConditionalContainer(Frame(HSplit([
        ConditionalContainer(Window(content=FormattedTextControl(lambda: _result_tabs(cells)), height=1), filter=Condition(lambda: _result_tabs_visible(cells))),
        windows["Results"],
    ]), title=lambda: _result_title(cells), height=Dimension(weight=1)), filter=Condition(lambda: _visible(cells, "Results")))
    root = FloatContainer(content=HSplit([
        VSplit([catalog, HSplit([editor, run_bar, results], width=Dimension(weight=3))]),
        Window(content=FormattedTextControl(lambda: _footer(cells)), height=1),
    ]), floats=[
        Float(content=ConditionalContainer(Frame(Window(content=FormattedTextControl(lambda: _dialog_text(cells)), width=lambda: _dialog_width(cells), dont_extend_height=True), style="class:hq.dialog"), filter=Condition(lambda: _has_dialog(cells)))),
        Float(bottom=1, right=1, content=ConditionalContainer(Window(content=FormattedTextControl(lambda: _notifications(cells)), width=60, dont_extend_height=True), filter=Condition(lambda: bool(_live(cells, int(time.monotonic() * 1000)))))),
    ])
    kb = KeyBindings()
    groups: dict[tuple[str, ...], list[BoundKey]] = {}
    for key in bound:
        translated = terminal_key_sequence(key.key)
        if isinstance(translated, Some):
            groups.setdefault(tuple(translated.value), []).append(key)
    for sequence, group in groups.items():
        _register(cells, kb, sequence, group)
    dialog_filter = Condition(lambda: _dialog_active(cells))
    dialog_callback: Callable[[KeyPressEvent], None] = lambda event: _dialog_any(cells, event)
    kb.add(Keys.Any, filter=dialog_filter)(dialog_callback)
    for name in ("escape", "enter", "tab", "up", "down", "left", "right", "backspace", "delete", "home", "end", "pageup", "pagedown", "space"):
        translated = terminal_key_sequence(name)
        if isinstance(translated, Some) and tuple(translated.value) not in groups:
            kb.add(*translated.value, filter=dialog_filter, eager=True)(dialog_callback)
    style = Style.from_dict({rule.selector: rule.style for rule in theme_style_rules(context.palette)})
    app: Application[None] = Application(layout=Layout(root, focused_element=editor_window), key_bindings=kb, style=style, full_screen=True, mouse_support=False, refresh_interval=0.5)
    state["app"] = app
    state["kb"] = kb
    invalidate: Callable[[], None] = lambda: app.invalidate()
    notify: Callable[[str | None, str, str], None] = lambda title, message, severity: _notify(cells, title, message, severity)
    open_dialog: Callable[[str, object], None] = lambda kind, model: _open_dialog(cells, kind, model)
    close_dialog: Callable[[], None] = lambda: _close_dialog(cells)
    focus: Callable[[str], None] = lambda action: _focus(cells, action)
    size: Callable[[], tuple[int, int]] = lambda: _size(cells)
    state["invalidate"] = invalidate
    state["notify"] = notify
    state["open_dialog"] = open_dialog
    state["close_dialog"] = close_dialog
    state["focus"] = focus
    state["size"] = size
    return IdeSession(handle=Opaque(tag="harlequin.ide", value=state))
