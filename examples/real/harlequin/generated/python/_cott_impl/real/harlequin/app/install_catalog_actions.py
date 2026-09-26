import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final, cast

from cott_runtime import UNIT, CottList, Err, Nothing, Ok, Some, Unit
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent

from real.harlequin.adapters import catalog_interactions, load_catalog_children, plan_interaction, run_scalar_query
from real.harlequin.adapters_types import Connection, InteractionPlan, InteractionPlan_Execute, InteractionPlan_InsertChildNames, InteractionPlan_InsertText, InteractionPlan_NewBuffer, InteractionPlan_NewBufferFromQuery
from real.harlequin.app_types import IdeSession
from real.harlequin.catalog import catalog_children, list_directory, list_s3, move_tree_cursor, replace_children, toggle_tree_node, tree_cursor_entry
from real.harlequin.catalog_types import CatalogEntry, FileTreeError_NotADirectory, S3Error_AccessDenied, S3Error_Unavailable, TreeMotion, TreeMotion_Down, TreeMotion_First, TreeMotion_Last, TreeMotion_PageDown, TreeMotion_PageUp, TreeMotion_Parent, TreeMotion_Up, TreeState
from real.harlequin.ide import confirm_key, context_menu, context_menu_key, error_modal
from real.harlequin.ide_types import ConfirmModal, ConfirmOutcome_Stay, ConfirmOutcome_Yes, ContextMenu, ContextMenuOutcome_Choose, ContextMenuOutcome_Stay, LayoutState, Pane_Catalog
from real.harlequin.keymap_types import ActionScope_Catalog, BoundKey
from real.harlequin.support import copy_to_clipboard

_TAG: Final[str] = "harlequin.ide"
_CATALOG_ERROR: Final[str] = "Catalog Error"
_CATALOG_HEADER: Final[str] = "Harlequin could not load your data catalog."
_INTERACTION_TITLE: Final[str] = "Data Catalog Interaction Error"
_INTERACTION_HEADER: Final[str] = "Harlequin could not execute an interaction from your data catalog."


def _lock(s: dict[str, object]) -> threading.RLock:
    return cast(threading.RLock, s["lock"])


def _invalidate(s: dict[str, object]) -> None:
    app: Any = s["app"]
    app.invalidate()


def _connection(s: dict[str, object]) -> Connection | None:
    raw = s.get("connection")
    if isinstance(raw, Connection):
        return raw
    return None


def _tab(s: dict[str, object]) -> str:
    return str(s.get("catalog_tab", "Databases"))


def _keys(tab: str) -> tuple[str, str]:
    if tab == "Files":
        return ("files", "files_tree")
    if tab == "S3":
        return ("s3", "s3_tree")
    return ("catalog", "tree")


def _entries(s: dict[str, object], key: str) -> list[CatalogEntry]:
    raw = s.get(key)
    if not isinstance(raw, list):
        return []
    return [item for item in cast(list[object], raw) if isinstance(item, CatalogEntry)]


def _tree(s: dict[str, object], key: str) -> TreeState:
    raw = s.get(key)
    if isinstance(raw, TreeState):
        return raw
    return TreeState(expanded=CottList(values=[]), cursor=0, first_row=0)


def _notify(s: dict[str, object], message: str, severity: str) -> None:
    fn = s.get("notify")
    if callable(fn):
        cast(Callable[[str | None, str, str], None], fn)(None, message, severity)


def _open_dialog(s: dict[str, object], kind: str, model: object) -> None:
    fn = s.get("open_dialog")
    if callable(fn):
        cast(Callable[[str, object], None], fn)(kind, model)


def _close_dialog(s: dict[str, object]) -> None:
    fn = s.get("close_dialog")
    if callable(fn):
        cast(Callable[[], None], fn)()


def _insert(s: dict[str, object], text: str) -> None:
    fn = s.get("insert_text")
    if callable(fn):
        cast(Callable[[str], None], fn)(text)


def _new_buffer(s: dict[str, object], text: str) -> None:
    fn = s.get("new_buffer")
    if callable(fn):
        cast(Callable[[str], None], fn)(text)


def _page_rows(s: dict[str, object]) -> int:
    app: Any = s["app"]
    window: Any = app.layout.current_window
    info = cast(object, window.render_info) if window is not None else None
    if info is not None:
        typed: Any = info
        height = cast(object, typed.window_height)
        if isinstance(height, int):
            return max(height, 1)
    fn = s.get("size")
    if callable(fn):
        size = cast(Callable[[], tuple[int, int]], fn)()
        return max(size[1] - 3, 1)
    return 1


def _move(s: dict[str, object], motion: TreeMotion) -> None:
    with _lock(s):
        entries_key, tree_key = _keys(_tab(s))
        s[tree_key] = move_tree_cursor(CottList(values=_entries(s, entries_key)), _tree(s, tree_key), motion, _page_rows(s))
    _invalidate(s)


def _cursor_entry(s: dict[str, object]) -> CatalogEntry | None:
    entries_key, tree_key = _keys(_tab(s))
    found = tree_cursor_entry(CottList(values=_entries(s, entries_key)), _tree(s, tree_key))
    if isinstance(found, Some):
        return found.value
    return None


def _find(entries: list[CatalogEntry], entry_id: str) -> CatalogEntry | None:
    for entry in entries:
        if entry.id == entry_id:
            return entry
    return None


def _fetch_children(s: dict[str, object], tab: str, entry: CatalogEntry) -> list[CatalogEntry] | str:
    if tab == "Files":
        listed = list_directory(Path(entry.id), Some(value=entry.id), entry.depth + 1)
        if isinstance(listed, Ok):
            return list(listed.value)
        error = listed.error
        if isinstance(error, FileTreeError_NotADirectory):
            return f"{error.path} is not a directory."
        return f"Could not read {error.path}: {error.message}"
    if tab == "S3":
        s3 = list_s3(entry.id, Some(value=entry.id), entry.depth + 1)
        if isinstance(s3, Ok):
            return list(s3.value)
        s3_error = s3.error
        if isinstance(s3_error, S3Error_Unavailable):
            return s3_error.message
        if isinstance(s3_error, S3Error_AccessDenied):
            return f"Access denied to {s3_error.target}."
        return f"{s3_error.target}: {s3_error.message}"
    with _lock(s):
        connection = _connection(s)
    if connection is None:
        return "There is no open connection."
    loaded = load_catalog_children(connection, entry)
    if isinstance(loaded, Ok):
        return list(loaded.value)
    return loaded.error.message


def _load_worker(s: dict[str, object], tab: str, entry: CatalogEntry, insert_names: bool) -> None:
    result = _fetch_children(s, tab, entry)
    entries_key = _keys(tab)[0]
    with _lock(s):
        if isinstance(result, str):
            _open_dialog(s, "text", error_modal(_CATALOG_ERROR, _CATALOG_HEADER, result))
        else:
            merged = replace_children(CottList(values=_entries(s, entries_key)), entry.id, CottList(values=result))
            s[entries_key] = list(merged)
            if insert_names:
                children = catalog_children(merged, Some(value=entry.id))
                _insert(s, ", ".join(child.query_name for child in children))
    _invalidate(s)


def _start_load(s: dict[str, object], tab: str, entry: CatalogEntry, insert_names: bool) -> None:
    threading.Thread(target=lambda: _load_worker(s, tab, entry, insert_names), daemon=True).start()


def _toggle(s: dict[str, object]) -> None:
    with _lock(s):
        tab = _tab(s)
        entries_key, tree_key = _keys(tab)
        entries = _entries(s, entries_key)
        toggled = toggle_tree_node(CottList(values=entries), _tree(s, tree_key))
        s[tree_key] = toggled.tree
        target = toggled.load_children
        entry = _find(entries, target.value) if isinstance(target, Some) else None
    if entry is not None:
        _start_load(s, tab, entry, False)
    _invalidate(s)


def _insert_name(s: dict[str, object]) -> None:
    with _lock(s):
        entry = _cursor_entry(s)
        if entry is not None:
            _insert(s, entry.query_name)
    _invalidate(s)


def _copy_name(s: dict[str, object]) -> None:
    with _lock(s):
        entry = _cursor_entry(s)
    if entry is None:
        return
    copied = copy_to_clipboard(entry.query_name)
    with _lock(s):
        if isinstance(copied, Err):
            _notify(s, copied.error.message, "error")
    _invalidate(s)


def _show_menu(s: dict[str, object]) -> None:
    with _lock(s):
        entry = _cursor_entry(s)
        if entry is not None:
            connection = _connection(s)
            if _tab(s) == "Databases" and connection is not None:
                _open_dialog(s, "menu", context_menu(entry, catalog_interactions(connection.adapter, entry)))
            else:
                _open_dialog(s, "menu", context_menu(entry, CottList(values=[])))
    _invalidate(s)


def _menu_key(s: dict[str, object], state: dict[str, object], key: str) -> None:
    with _lock(s):
        dialog = s.get("dialog")
        if not isinstance(dialog, tuple):
            return
        model = cast(tuple[object, object], dialog)[1]
        if not isinstance(model, ContextMenu):
            return
        step = context_menu_key(model, key)
        outcome = step.outcome
        if isinstance(outcome, ContextMenuOutcome_Stay):
            _open_dialog(s, "menu", step.menu)
        elif isinstance(outcome, ContextMenuOutcome_Choose):
            _close_dialog(s)
            _choose(s, state, step.menu.entry, outcome.label)
        else:
            _close_dialog(s)
    _invalidate(s)


def _choose(s: dict[str, object], state: dict[str, object], entry: CatalogEntry, label: str) -> None:
    connection = _connection(s)
    if connection is None or _tab(s) != "Databases":
        if label == "Insert Name at Cursor":
            _insert(s, entry.query_name)
        return
    children = catalog_children(CottList(values=_entries(s, "catalog")), Some(value=entry.id))
    planned = plan_interaction(connection.adapter, entry, label, children)
    if isinstance(planned, Some):
        _apply_plan(s, state, entry, planned.value)


def _apply_plan(s: dict[str, object], state: dict[str, object], entry: CatalogEntry, plan: InteractionPlan) -> None:
    if isinstance(plan, InteractionPlan_InsertText):
        _insert(s, plan.text)
    elif isinstance(plan, InteractionPlan_InsertChildNames):
        entries = _entries(s, "catalog")
        parent = _find(entries, plan.parent) or entry
        if parent.expandable and not parent.loaded:
            _start_load(s, "Databases", parent, True)
        else:
            children = catalog_children(CottList(values=entries), Some(value=parent.id))
            _insert(s, ", ".join(child.query_name for child in children))
    elif isinstance(plan, InteractionPlan_NewBuffer):
        _new_buffer(s, plan.text)
    elif isinstance(plan, InteractionPlan_NewBufferFromQuery):
        sql = plan.sql
        failure = plan.failure
        threading.Thread(target=lambda: _query_buffer_worker(s, sql, failure), daemon=True).start()
    else:
        _plan_execute(s, state, plan)


def _plan_execute(s: dict[str, object], state: dict[str, object], plan: InteractionPlan_Execute) -> None:
    confirm = plan.confirm
    if isinstance(confirm, Some):
        state["pending"] = plan
        _open_dialog(s, "confirm", ConfirmModal(prompt=confirm.value, yes_selected=False))
    else:
        _start_execute(s, plan)


def _start_execute(s: dict[str, object], plan: InteractionPlan_Execute) -> None:
    threading.Thread(target=lambda: _execute_worker(s, plan), daemon=True).start()


def _query_buffer_worker(s: dict[str, object], sql: str, failure: str) -> None:
    with _lock(s):
        connection = _connection(s)
    result = run_scalar_query(connection, sql) if connection is not None else None
    with _lock(s):
        if isinstance(result, Ok) and isinstance(result.value, Some):
            _new_buffer(s, result.value.value)
        else:
            _notify(s, failure, "error")
    _invalidate(s)


def _execute_worker(s: dict[str, object], plan: InteractionPlan_Execute) -> None:
    with _lock(s):
        connection = _connection(s)
    if connection is None:
        with _lock(s):
            _open_dialog(s, "text", error_modal(_INTERACTION_TITLE, _INTERACTION_HEADER, "There is no open connection."))
        _invalidate(s)
        return
    result = run_scalar_query(connection, plan.sql)
    refresh: object = None
    with _lock(s):
        if isinstance(result, Ok):
            _notify(s, plan.success, "information")
            if plan.refresh:
                refresh = s.get("refresh_catalog")
        else:
            _open_dialog(s, "text", error_modal(_INTERACTION_TITLE, _INTERACTION_HEADER, result.error.message))
    if callable(refresh):
        cast(Callable[[], None], refresh)()
    _invalidate(s)


def _confirm_key(s: dict[str, object], state: dict[str, object], key: str) -> None:
    with _lock(s):
        dialog = s.get("dialog")
        if not isinstance(dialog, tuple):
            return
        model = cast(tuple[object, object], dialog)[1]
        if not isinstance(model, ConfirmModal):
            return
        step = confirm_key(model, key)
        outcome = step.outcome
        if isinstance(outcome, ConfirmOutcome_Stay):
            _open_dialog(s, "confirm", step.modal)
        else:
            _close_dialog(s)
            pending = state.get("pending")
            state["pending"] = None
            if isinstance(outcome, ConfirmOutcome_Yes) and isinstance(pending, InteractionPlan_Execute):
                _start_execute(s, pending)
    _invalidate(s)


def _configured_tabs(s: dict[str, object]) -> list[str]:
    settings: Any = s["settings"]
    tabs = ["Databases"]
    if isinstance(cast(object, settings.show_files), Some):
        tabs.append("Files")
    if isinstance(cast(object, settings.show_s3), Some):
        tabs.append("S3")
    return tabs


def _root_worker(s: dict[str, object], tab: str) -> None:
    settings: Any = s["settings"]
    message = ""
    roots: list[CatalogEntry] = []
    if tab == "Files":
        option = cast(object, settings.show_files)
        target = str(cast(object, option.value)) if isinstance(option, Some) else "."
        listed = list_directory(Path(target), Nothing(), 0)
        if isinstance(listed, Ok):
            roots = list(listed.value)
        elif isinstance(listed.error, FileTreeError_NotADirectory):
            message = f"{listed.error.path} is not a directory."
        else:
            message = f"Could not read {listed.error.path}: {listed.error.message}"
    else:
        option = cast(object, settings.show_s3)
        target = str(cast(object, option.value)) if isinstance(option, Some) else "all"
        s3 = list_s3(target, Nothing(), 0)
        if isinstance(s3, Ok):
            roots = list(s3.value)
        elif isinstance(s3.error, S3Error_Unavailable):
            message = s3.error.message
        elif isinstance(s3.error, S3Error_AccessDenied):
            message = f"Access denied to {s3.error.target}."
        else:
            message = f"{s3.error.target}: {s3.error.message}"
    entries_key = _keys(tab)[0]
    with _lock(s):
        if message:
            _open_dialog(s, "text", error_modal(_CATALOG_ERROR, _CATALOG_HEADER, message))
        else:
            s[entries_key] = roots
    _invalidate(s)


def _switch_tab(s: dict[str, object], state: dict[str, object], step: int) -> None:
    with _lock(s):
        tabs = _configured_tabs(s)
        current = _tab(s)
        index = tabs.index(current) if current in tabs else 0
        tab = tabs[(index + step) % len(tabs)]
        s["catalog_tab"] = tab
        shown = cast(set[str], state["shown"])
        first = tab != "Databases" and tab not in shown
        shown.add(tab)
    if first:
        threading.Thread(target=lambda: _root_worker(s, tab), daemon=True).start()
    _invalidate(s)


def _catalog_focused(s: dict[str, object]) -> bool:
    layout = s.get("layout")
    return isinstance(layout, LayoutState) and isinstance(layout.focus, Pane_Catalog) and not layout.sidebar_hidden and s.get("dialog") is None


def _key_is_bound(s: dict[str, object], key: str) -> bool:
    raw = s.get("bound")
    if not isinstance(raw, tuple):
        return False
    for item in cast(tuple[object, ...], raw):
        if isinstance(item, BoundKey) and item.key == key and isinstance(item.scope, ActionScope_Catalog):
            return True
    return False


def _motion_event(s: dict[str, object], motion: TreeMotion, event: KeyPressEvent) -> None:
    del event
    _move(s, motion)


def _bind_motion(s: dict[str, object], key: str, motion: TreeMotion) -> None:
    kb = cast(KeyBindings, s["kb"])
    cast(Callable[[Callable[[KeyPressEvent], None]], object], kb.add(key, filter=Condition(lambda: _catalog_focused(s))))(lambda event: _motion_event(s, motion, event))


def install_catalog_actions(session: IdeSession) -> Unit:
    handle = session.handle
    if handle.tag != _TAG:
        return UNIT
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return UNIT
    s = cast(dict[str, object], raw)
    state: dict[str, object] = {"pending": None, "shown": set[str]()}
    handlers_raw = s.get("handlers")
    dialog_keys_raw = s.get("dialog_keys")
    if not isinstance(handlers_raw, dict) or not isinstance(dialog_keys_raw, dict):
        return UNIT
    handlers = cast(dict[str, Callable[[], None]], handlers_raw)
    dialog_keys = cast(dict[str, Callable[[str, str], None]], dialog_keys_raw)
    with _lock(s):
        handlers["data_catalog.cursor_up"] = lambda: _move(s, TreeMotion_Up())
        handlers["data_catalog.cursor_down"] = lambda: _move(s, TreeMotion_Down())
        handlers["data_catalog.toggle_node"] = lambda: _toggle(s)
        handlers["data_catalog.select_cursor"] = lambda: _toggle(s)
        handlers["data_catalog.insert_name"] = lambda: _insert_name(s)
        handlers["data_catalog.copy_name"] = lambda: _copy_name(s)
        handlers["data_catalog.show_context_menu"] = lambda: _show_menu(s)
        handlers["data_catalog.next_tab"] = lambda: _switch_tab(s, state, 1)
        handlers["data_catalog.previous_tab"] = lambda: _switch_tab(s, state, -1)
        dialog_keys["menu"] = lambda key, text: _menu_key(s, state, key)
        dialog_keys["confirm"] = lambda key, text: _confirm_key(s, state, key)
        motions: list[tuple[str, TreeMotion]] = [
            ("pageup", TreeMotion_PageUp()),
            ("pagedown", TreeMotion_PageDown()),
            ("home", TreeMotion_First()),
            ("end", TreeMotion_Last()),
            ("left", TreeMotion_Parent()),
        ]
        for key, motion in motions:
            if not _key_is_bound(s, key):
                _bind_motion(s, key, motion)
    return UNIT
