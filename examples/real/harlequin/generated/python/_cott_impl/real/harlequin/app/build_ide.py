import datetime
import threading
import time
from collections.abc import Callable
from typing import Final, cast

from cott_runtime import CottList, Nothing, Ok, Opaque, Some
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
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

from real.harlequin.catalog import builtin_completions, completion_set, render_tree
from real.harlequin.export import render_export_dialog
from real.harlequin.history import render_history
from real.harlequin.ide import initial_layout, layout_action, new_run_bar, render_confirm, render_context_menu, render_footer, render_input_modal, render_notifications, render_run_bar, render_tab_bar, render_text_modal, run_label, visible_panes
from real.harlequin.keymap import bind_keymaps, builtin_keymaps, footer_hints, terminal_key_sequence
from real.harlequin.results import render_grid, results_title
from real.harlequin.style import theme_style_rules
from real.harlequin.adapters_types import Connection
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.catalog_types import CatalogEntry, TreeState
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.export_types import ExportDialog
from real.harlequin.history_types import HistoryScreen, QueryRecord
from real.harlequin.ide_types import ConfirmModal, ContextMenu, InputModal, LayoutState, Notification, Pane, Pane_Catalog, Pane_Editor, Pane_Results, Pane_RunBar, RunBar, Severity, Severity_Error, Severity_Information, Severity_Warning, TextModal
from real.harlequin.keymap_types import ActionScope, ActionScope_App, ActionScope_Catalog, ActionScope_ContextMenu, ActionScope_Editor, ActionScope_Results, BoundKey, BoundKeySet, KeyMap
from real.harlequin.results_types import ResultSet, ResultsGrid
from real.harlequin.style_types import StyledLine

_NOTIFY_MS: Final[int] = 5000
_NOTIFY_WIDTH: Final[int] = 60
_BOUND_TAG: Final[str] = "harlequin.bound_keys"


def _lock(s: dict[str, object]) -> threading.RLock:
    return cast(threading.RLock, s["lock"])


def _app(s: dict[str, object]) -> Application[None]:
    return cast(Application[None], s["app"])


def _invalidate(s: dict[str, object]) -> None:
    _app(s).invalidate()


def _size(s: dict[str, object]) -> tuple[int, int]:
    size = _app(s).output.get_size()
    return (size.columns, size.rows)


def _fragments(lines: list[StyledLine]) -> StyleAndTextTuples:
    out: StyleAndTextTuples = []
    for index, line in enumerate(lines):
        if index:
            out.append(("", "\n"))
        for span in line.spans:
            out.append((span.style, span.text))
    return out


def _win_size(window: Window, width: int, height: int) -> tuple[int, int]:
    info = window.render_info
    if info is None:
        return (max(width, 1), max(height, 1))
    return (info.window_width, info.window_height)


def _layout(s: dict[str, object]) -> LayoutState:
    return cast(LayoutState, s["layout"])


def _pane_name(pane: Pane) -> str:
    if isinstance(pane, Pane_Catalog):
        return "Catalog"
    if isinstance(pane, Pane_Editor):
        return "Editor"
    if isinstance(pane, Pane_RunBar):
        return "RunBar"
    return "Results"


def _pane_visible(s: dict[str, object], name: str) -> bool:
    with _lock(s):
        panes = visible_panes(_layout(s))
    return any(_pane_name(pane) == name for pane in panes)


def _focused_scope(s: dict[str, object]) -> str:
    name = _pane_name(_layout(s).focus)
    if name == "Catalog":
        return "Catalog"
    if name == "Results":
        return "Results"
    return "Editor"


def _scope_name(scope: ActionScope) -> str:
    if isinstance(scope, ActionScope_App):
        return "App"
    if isinstance(scope, ActionScope_Editor):
        return "Editor"
    if isinstance(scope, ActionScope_Catalog):
        return "Catalog"
    if isinstance(scope, ActionScope_ContextMenu):
        return "ContextMenu"
    if isinstance(scope, ActionScope_Results):
        return "Results"
    return "History"


def _buffers(s: dict[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], s["buffers"])


def _active_buffer(s: dict[str, object]) -> Buffer:
    buffers = _buffers(s)
    index = min(max(cast(int, s["active"]), 0), len(buffers) - 1)
    return cast(Buffer, buffers[index]["buffer"])


def _editor_window(s: dict[str, object], editors: dict[int, Window]) -> Window:
    with _lock(s):
        buffer = _active_buffer(s)
    key = id(buffer)
    window = editors.get(key)
    if window is None:
        control = BufferControl(buffer=buffer, lexer=PygmentsLexer(SqlLexer))
        window = Window(content=control, left_margins=[NumberedMargin()], wrap_lines=False)
        editors[key] = window
    return window


def _pane_window(s: dict[str, object], windows: dict[str, Window], editors: dict[int, Window], pane: Pane) -> Window:
    name = _pane_name(pane)
    if name == "Catalog":
        return windows["catalog"]
    if name == "RunBar":
        return windows["run_bar"]
    if name == "Results":
        return windows["results"]
    return _editor_window(s, editors)


def _focus(s: dict[str, object], windows: dict[str, Window], editors: dict[int, Window], action: str) -> None:
    with _lock(s):
        layout = layout_action(_layout(s), action)
        s["layout"] = layout
    target = _pane_window(s, windows, editors, layout.focus)
    app = _app(s)
    try:
        app.layout.focus(target)
    except ValueError:
        app.invalidate()
        return
    app.invalidate()


def _notify(s: dict[str, object], title: str | None, message: str, severity: str) -> None:
    level: Severity
    if severity == "error":
        level = Severity_Error()
    elif severity == "warning":
        level = Severity_Warning()
    else:
        level = Severity_Information()
    note = Notification(
        title=Some(value=title) if title is not None else Nothing(),
        message=message,
        severity=level,
        expires_at_ms=int(time.monotonic() * 1000) + _NOTIFY_MS,
    )
    with _lock(s):
        cast(list[Notification], s["notifications"]).append(note)
    _invalidate(s)


def _open_dialog(s: dict[str, object], kind: str, model: object) -> None:
    with _lock(s):
        s["dialog"] = (kind, model)
    _invalidate(s)


def _close_dialog(s: dict[str, object]) -> None:
    with _lock(s):
        s["dialog"] = None
    _invalidate(s)


def _dialog_keys(s: dict[str, object]) -> dict[str, Callable[[str, str], None]]:
    return cast(dict[str, Callable[[str, str], None]], s["dialog_keys"])


def _handlers(s: dict[str, object]) -> dict[str, Callable[[], None]]:
    return cast(dict[str, Callable[[], None]], s["handlers"])


def _dialog_kind(s: dict[str, object]) -> str | None:
    dialog = s["dialog"]
    if dialog is None:
        return None
    kind = cast(tuple[str, object], dialog)[0]
    return kind if kind in _dialog_keys(s) else None


def _dialog_open(s: dict[str, object]) -> bool:
    with _lock(s):
        return _dialog_kind(s) is not None


def _pick_action(s: dict[str, object], keys: list[BoundKey]) -> str | None:
    handlers = _handlers(s)
    focused = _focused_scope(s)
    for key in keys:
        if key.priority and _scope_name(key.scope) in (focused, "App") and key.action in handlers:
            return key.action
    for scope in (focused, "App"):
        for key in keys:
            if _scope_name(key.scope) == scope and key.action in handlers:
                return key.action
    return None


def _key_active(s: dict[str, object], keys: list[BoundKey]) -> bool:
    with _lock(s):
        return _dialog_kind(s) is not None or _pick_action(s, keys) is not None


def _press(s: dict[str, object], keys: list[BoundKey], event: KeyPressEvent) -> None:
    with _lock(s):
        kind = _dialog_kind(s)
        action = None if kind is not None else _pick_action(s, keys)
    if kind is not None:
        _dialog_keys(s)[kind](keys[0].key, event.data)
    elif action is not None:
        _handlers(s)[action]()


def _textual_name(event: KeyPressEvent) -> str:
    key = event.key_sequence[0].key
    names: dict[str, str] = {"c-m": "enter", "c-i": "tab", "c-h": "backspace", "s-tab": "shift+tab"}
    if isinstance(key, Keys):
        value = key.value
        if value in names:
            return names[value]
        if value.startswith("c-s-"):
            return "ctrl+shift+" + value[4:]
        if value.startswith("c-"):
            return "ctrl+" + value[2:]
        if value.startswith("s-"):
            return "shift+" + value[2:]
        return value
    text = event.data
    if text == " ":
        return "space"
    return text


def _dialog_any(s: dict[str, object], event: KeyPressEvent) -> None:
    with _lock(s):
        kind = _dialog_kind(s)
    if kind is not None:
        _dialog_keys(s)[kind](_textual_name(event), event.data)


def _register(kb: KeyBindings, s: dict[str, object], sequence: tuple[str, ...], keys: list[BoundKey]) -> None:
    handler: Callable[[KeyPressEvent], None] = lambda event: _press(s, keys, event)
    try:
        kb.add(*sequence, filter=Condition(lambda: _key_active(s, keys)))(handler)
    except ValueError:
        return


def _catalog_tabs(s: dict[str, object]) -> list[str]:
    settings = cast(HarlequinSettings, s["settings"])
    tabs = ["Databases"]
    if isinstance(settings.show_files, Some):
        tabs.append("Files")
    if isinstance(settings.show_s3, Some):
        tabs.append("S3")
    return tabs


def _has_catalog_tabs(s: dict[str, object]) -> bool:
    return len(_catalog_tabs(s)) > 1


def _catalog_tab_text(s: dict[str, object], windows: dict[str, Window]) -> StyleAndTextTuples:
    tabs = _catalog_tabs(s)
    with _lock(s):
        current = cast(str, s["catalog_tab"])
    active = tabs.index(current) if current in tabs else 0
    width = _win_size(windows["catalog"], _size(s)[0] // 4, 1)[0]
    return _fragments([render_tab_bar(CottList(values=tabs), active, width)])


def _catalog_text(s: dict[str, object], windows: dict[str, Window]) -> StyleAndTextTuples:
    cols, rows = _size(s)
    width, height = _win_size(windows["catalog"], cols // 4 - 2, rows - 4)
    keys: dict[str, tuple[str, str]] = {"Databases": ("catalog", "tree"), "Files": ("files", "files_tree"), "S3": ("s3", "s3_tree")}
    with _lock(s):
        entries_key, tree_key = keys.get(cast(str, s["catalog_tab"]), ("catalog", "tree"))
        entries = cast(list[CatalogEntry], s[entries_key])
        tree = cast(TreeState, s[tree_key])
        focused = isinstance(_layout(s).focus, Pane_Catalog)
        frame = render_tree(CottList(values=list(entries)), tree, width, height, focused)
        s[tree_key] = TreeState(expanded=tree.expanded, cursor=tree.cursor, first_row=frame.first_row)
    return _fragments(list(frame.lines))


def _buffer_count(s: dict[str, object]) -> int:
    with _lock(s):
        return len(_buffers(s))


def _buffer_tab_text(s: dict[str, object], editors: dict[int, Window]) -> StyleAndTextTuples:
    window = _editor_window(s, editors)
    with _lock(s):
        titles = [cast(str, item["title"]) for item in _buffers(s)]
        active = cast(int, s["active"])
    width = _win_size(window, _size(s)[0] * 3 // 4, 1)[0]
    return _fragments([render_tab_bar(CottList(values=titles), active, width)])


def _run_bar_text(s: dict[str, object], windows: dict[str, Window]) -> StyleAndTextTuples:
    context = cast(IdeContext, s["context"])
    width = _win_size(windows["run_bar"], _size(s)[0] * 3 // 4, 1)[0]
    with _lock(s):
        bar = cast(RunBar, s["run_bar"])
        connection = s["connection"]
        buffer = _active_buffer(s)
        focused = isinstance(_layout(s).focus, Pane_RunBar)
    transaction = connection.transaction_mode if isinstance(connection, Connection) else Nothing()
    document = buffer.document
    selection = ""
    if buffer.selection_state is not None:
        start, end = document.selection_range()
        selection = document.text[start:end]
    runnable = document.text.strip() != ""
    line = render_run_bar(bar, transaction, context.descriptor.implements_cancel, run_label(selection, True), runnable, focused, width)
    return _fragments([line])


def _current_result(s: dict[str, object]) -> ResultSet | None:
    results = cast(list[ResultSet], s["results"])
    if not results:
        return None
    index = min(max(cast(int, s["result_index"]), 0), len(results) - 1)
    return results[index]


def _results_frame_title(s: dict[str, object]) -> str:
    context = cast(IdeContext, s["context"])
    with _lock(s):
        state = cast(str, s["results_state"])
        result = _current_result(s)
    if state == "loading":
        return "Running Query"
    if state == "empty" or result is None:
        return "Query Results"
    return results_title(result, context.number_format)


def _result_count(s: dict[str, object]) -> int:
    with _lock(s):
        return len(cast(list[ResultSet], s["results"]))


def _results_tab_text(s: dict[str, object], windows: dict[str, Window]) -> StyleAndTextTuples:
    with _lock(s):
        count = len(cast(list[ResultSet], s["results"]))
        active = cast(int, s["result_index"])
    width = _win_size(windows["results"], _size(s)[0] * 3 // 4, 1)[0]
    labels = [f"Result {n + 1}" for n in range(count)]
    return _fragments([render_tab_bar(CottList(values=labels), active, width)])


def _results_text(s: dict[str, object], windows: dict[str, Window]) -> StyleAndTextTuples:
    context = cast(IdeContext, s["context"])
    cols, rows = _size(s)
    width, height = _win_size(windows["results"], cols * 3 // 4 - 2, rows // 2 - 2)
    with _lock(s):
        if cast(str, s["results_state"]) != "ready":
            return []
        grids = cast(list[ResultsGrid], s["grids"])
        if not grids:
            return []
        index = min(max(cast(int, s["result_index"]), 0), len(grids) - 1)
        grid = grids[index]
        if grid.result.row_count == 0:
            empty: StyleAndTextTuples = [("class:hq.muted", "Query Returned No Records")]
            return empty
        focused = isinstance(_layout(s).focus, Pane_Results)
        frame = render_grid(grid, width, height, focused, context.number_format)
        grids[index] = ResultsGrid(result=grid.result, cursor=grid.cursor, anchor=grid.anchor, first_row=frame.first_row, first_column=frame.first_column)
    return _fragments(list(frame.lines))


def _footer_text(s: dict[str, object]) -> StyleAndTextTuples:
    with _lock(s):
        bound_handle = cast(BoundKeySet, s["bound_handle"])
        scope_name = _focused_scope(s)
    scope: ActionScope
    if scope_name == "Catalog":
        scope = ActionScope_Catalog()
    elif scope_name == "Results":
        scope = ActionScope_Results()
    else:
        scope = ActionScope_Editor()
    hints = footer_hints(bound_handle, scope)
    return _fragments([render_footer(hints, _size(s)[0])])


def _dialog_width(s: dict[str, object]) -> int:
    return max(min(_size(s)[0] - 4, 100), 10)


def _offset_minutes() -> int:
    offset = datetime.datetime.now().astimezone().utcoffset()
    return 0 if offset is None else int(offset.total_seconds() // 60)


def _dialog_text(s: dict[str, object]) -> StyleAndTextTuples:
    with _lock(s):
        dialog = s["dialog"]
    if dialog is None:
        return []
    kind, model = cast(tuple[str, object], dialog)
    width = _dialog_width(s)
    height = max(_size(s)[1] - 6, 3)
    lines: list[StyledLine] = []
    if kind == "text" and isinstance(model, TextModal):
        lines = list(render_text_modal(model, width, height))
    elif kind == "input" and isinstance(model, InputModal):
        lines = list(render_input_modal(model, width))
    elif kind == "confirm" and isinstance(model, ConfirmModal):
        lines = list(render_confirm(model, width))
    elif kind == "menu" and isinstance(model, ContextMenu):
        lines = list(render_context_menu(model, width))
    elif kind == "export" and isinstance(model, ExportDialog):
        lines = list(render_export_dialog(model, width))
    elif kind == "history" and isinstance(model, tuple):
        pair = cast(tuple[object, object], model)
        screen = pair[0]
        if isinstance(screen, HistoryScreen) and isinstance(pair[1], list):
            records = cast(list[QueryRecord], pair[1])
            lines = list(render_history(screen, CottList(values=list(records)), width, height, _offset_minutes()))
    return _fragments(lines)


def _live_notifications(s: dict[str, object], now: int) -> list[Notification]:
    with _lock(s):
        notes = cast(list[Notification], s["notifications"])
        live = [note for note in notes if note.expires_at_ms > now]
        if len(live) != len(notes):
            notes[:] = live
    return live


def _has_notifications(s: dict[str, object]) -> bool:
    return bool(_live_notifications(s, int(time.monotonic() * 1000)))


def _notification_text(s: dict[str, object]) -> StyleAndTextTuples:
    now = int(time.monotonic() * 1000)
    live = _live_notifications(s, now)
    return _fragments(list(render_notifications(CottList(values=live), now, _NOTIFY_WIDTH)))


def _dialog_visible(s: dict[str, object]) -> bool:
    with _lock(s):
        return s["dialog"] is not None


def _bind(settings: HarlequinSettings, keymaps: CottList[KeyMap]) -> BoundKeySet:
    available: list[KeyMap] = [*builtin_keymaps(), *keymaps]
    result = bind_keymaps(CottList(values=available), settings.keymap_names)
    if isinstance(result, Ok):
        return result.value
    fallback = bind_keymaps(builtin_keymaps(), CottList(values=["vscode"]))
    if isinstance(fallback, Ok):
        return fallback.value
    raise RuntimeError(f"the builtin vscode keymap failed to bind: {fallback.error}")


def build_ide(settings: HarlequinSettings, context: IdeContext, keymaps: CottList[KeyMap]) -> IdeSession:
    bound_handle = _bind(settings, keymaps)
    if bound_handle.handle.tag != _BOUND_TAG:
        raise TypeError("expected a harlequin.bound_keys handle")
    bound = cast(tuple[BoundKey, ...], bound_handle.handle.unwrap())
    empty_tree = TreeState(expanded=CottList(values=[]), cursor=0, first_row=0)
    first = Buffer(multiline=True)
    s: dict[str, object] = {
        "lock": threading.RLock(),
        "settings": settings,
        "context": context,
        "bound_handle": bound_handle,
        "bound": bound,
        "connection": None,
        "running": False,
        "buffers": [{"title": "Tab 1", "buffer": first}],
        "active": 0,
        "tab_counter": 1,
        "layout": initial_layout(),
        "run_bar": new_run_bar(settings.limit),
        "results": [],
        "grids": [],
        "result_index": 0,
        "results_state": "empty",
        "catalog": [],
        "tree": empty_tree,
        "catalog_tab": "Databases",
        "files": [],
        "files_tree": empty_tree,
        "s3": [],
        "s3_tree": empty_tree,
        "completions": completion_set(builtin_completions()),
        "notifications": [],
        "dialog": None,
        "handlers": {},
        "dialog_keys": {},
        "on_exit": [],
        "on_crash": [],
    }
    windows: dict[str, Window] = {}
    editors: dict[int, Window] = {}
    windows["catalog"] = Window(content=FormattedTextControl(lambda: _catalog_text(s, windows), focusable=True))
    windows["run_bar"] = Window(content=FormattedTextControl(lambda: _run_bar_text(s, windows), focusable=True), height=1)
    windows["results"] = Window(content=FormattedTextControl(lambda: _results_text(s, windows), focusable=True))
    editor_window = _editor_window(s, editors)

    catalog = ConditionalContainer(
        Frame(
            HSplit([
                ConditionalContainer(Window(content=FormattedTextControl(lambda: _catalog_tab_text(s, windows)), height=1), filter=Condition(lambda: _has_catalog_tabs(s))),
                windows["catalog"],
            ]),
            title="Data Catalog",
            width=Dimension(weight=1),
        ),
        filter=Condition(lambda: _pane_visible(s, "Catalog")),
    )
    editor = ConditionalContainer(
        Frame(
            HSplit([
                ConditionalContainer(Window(content=FormattedTextControl(lambda: _buffer_tab_text(s, editors)), height=1), filter=Condition(lambda: _buffer_count(s) >= 2)),
                DynamicContainer(lambda: _editor_window(s, editors)),
            ]),
            title="Query Editor",
            height=Dimension(weight=1),
        ),
        filter=Condition(lambda: _pane_visible(s, "Editor")),
    )
    run_bar = ConditionalContainer(windows["run_bar"], filter=Condition(lambda: _pane_visible(s, "RunBar")))
    results = ConditionalContainer(
        Frame(
            HSplit([
                ConditionalContainer(Window(content=FormattedTextControl(lambda: _results_tab_text(s, windows)), height=1), filter=Condition(lambda: _result_count(s) >= 2)),
                windows["results"],
            ]),
            title=lambda: _results_frame_title(s),
            height=Dimension(weight=1),
        ),
        filter=Condition(lambda: _pane_visible(s, "Results")),
    )
    main = HSplit([editor, run_bar, results], width=Dimension(weight=3))
    footer = Window(content=FormattedTextControl(lambda: _footer_text(s)), height=1)
    root = FloatContainer(
        content=HSplit([VSplit([catalog, main]), footer]),
        floats=[
            Float(
                content=ConditionalContainer(
                    Frame(Window(content=FormattedTextControl(lambda: _dialog_text(s)), width=lambda: _dialog_width(s)), style="class:hq.dialog"),
                    filter=Condition(lambda: _dialog_visible(s)),
                )
            ),
            Float(
                bottom=1,
                right=1,
                content=ConditionalContainer(
                    Window(content=FormattedTextControl(lambda: _notification_text(s)), width=_NOTIFY_WIDTH, dont_extend_height=True),
                    filter=Condition(lambda: _has_notifications(s)),
                ),
            ),
        ],
    )

    kb = KeyBindings()
    groups: dict[tuple[str, ...], list[BoundKey]] = {}
    for key in bound:
        sequence = terminal_key_sequence(key.key)
        if isinstance(sequence, Some):
            groups.setdefault(tuple(sequence.value), []).append(key)
    priority_first = sorted(groups.items(), key=lambda item: 0 if any(k.priority for k in item[1]) else 1)
    for sequence_key, group in priority_first:
        _register(kb, s, sequence_key, group)
    dialog_filter = Condition(lambda: _dialog_open(s))
    dialog_handler: Callable[[KeyPressEvent], None] = lambda event: _dialog_any(s, event)
    kb.add(Keys.Any, filter=dialog_filter)(dialog_handler)
    for name in ("escape", "enter", "tab", "up", "down", "left", "right", "backspace", "delete", "home", "end", "pageup", "pagedown"):
        kb.add(name, filter=dialog_filter)(dialog_handler)

    rules = theme_style_rules(context.palette)
    style = Style.from_dict({rule.selector: rule.style for rule in rules})
    app: Application[None] = Application(
        layout=Layout(root, focused_element=editor_window),
        key_bindings=kb,
        style=style,
        full_screen=True,
        mouse_support=False,
        refresh_interval=0.5,
    )
    s["app"] = app
    s["kb"] = kb
    notify: Callable[[str | None, str, str], None] = lambda title, message, severity: _notify(s, title, message, severity)
    open_dialog: Callable[[str, object], None] = lambda kind, model: _open_dialog(s, kind, model)
    focus: Callable[[str], None] = lambda action: _focus(s, windows, editors, action)
    s["invalidate"] = lambda: app.invalidate()
    s["notify"] = notify
    s["open_dialog"] = open_dialog
    s["close_dialog"] = lambda: _close_dialog(s)
    s["focus"] = focus
    s["size"] = lambda: _size(s)
    return IdeSession(handle=Opaque(tag="harlequin.ide", value=s))
