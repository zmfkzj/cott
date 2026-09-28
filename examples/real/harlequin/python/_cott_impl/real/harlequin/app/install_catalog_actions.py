import threading
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, cast

from cott_runtime import CottList, Nothing, Ok, Some, Unit
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent

from real.harlequin.adapters import catalog_interactions, load_catalog_children, plan_interaction, run_scalar_query
from real.harlequin.adapters_types import Connection, InteractionPlan, InteractionPlan_Execute, InteractionPlan_InsertChildNames, InteractionPlan_InsertText, InteractionPlan_NewBuffer, InteractionPlan_NewBufferFromQuery
from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.catalog import catalog_children, list_directory, list_s3, move_tree_cursor, replace_children, toggle_tree_node, tree_cursor_entry
from real.harlequin.catalog_types import CatalogEntry, FileTreeError, FileTreeError_NotADirectory, S3Error, S3Error_AccessDenied, S3Error_Unavailable, TreeMotion, TreeMotion_Down, TreeMotion_First, TreeMotion_Last, TreeMotion_PageDown, TreeMotion_PageUp, TreeMotion_Parent, TreeMotion_Up, TreeState
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.ide import confirm_key, context_menu, context_menu_key, error_modal
from real.harlequin.ide_types import ConfirmModal, ConfirmOutcome_Stay, ConfirmOutcome_Yes, ContextMenu, ContextMenuOutcome_Choose, ContextMenuOutcome_Stay, LayoutState, Pane_Catalog
from real.harlequin.keymap_types import ActionScope_App, ActionScope_Catalog, BoundKey
from real.harlequin.support import copy_to_clipboard


def _lock(state: dict[str, object]) -> AbstractContextManager[object]:
    return cast(AbstractContextManager[object], state["lock"])


def _invalidate(state: dict[str, object]) -> None:
    app: Any = state["app"]
    app.invalidate()


def _connection(state: dict[str, object]) -> Connection | None:
    connection = state["connection"]
    return connection if isinstance(connection, Connection) else None


def _tab_keys(tab: str) -> tuple[str, str]:
    if tab == "Files":
        return "files", "files_tree"
    if tab == "S3":
        return "s3", "s3_tree"
    return "catalog", "tree"


def _entries(state: dict[str, object], key: str) -> list[CatalogEntry]:
    return cast(list[CatalogEntry], state[key])


def _tree(state: dict[str, object], key: str) -> TreeState:
    return cast(TreeState, state[key])


def _notify(state: dict[str, object], title: str | None, message: str, severity: str) -> None:
    service = state.get("notify")
    if service is not None:
        cast(Callable[[str | None, str, str], None], service)(title, message, severity)


def _open_dialog(state: dict[str, object], kind: str, model: object) -> None:
    service = state.get("open_dialog")
    if service is not None:
        cast(Callable[[str, object], None], service)(kind, model)


def _close_dialog(state: dict[str, object]) -> None:
    service = state.get("close_dialog")
    if service is not None:
        cast(Callable[[], None], service)()


def _insert(state: dict[str, object], text: str) -> None:
    service = state.get("insert_text")
    if service is not None:
        cast(Callable[[str], None], service)(text)


def _new_buffer(state: dict[str, object], text: str) -> None:
    service = state.get("new_buffer")
    if service is not None:
        cast(Callable[[str], None], service)(text)


def _catalog_error(state: dict[str, object], message: str) -> None:
    _open_dialog(state, "text", error_modal("Catalog Error", "Harlequin could not load your data catalog.", message))


def _interaction_error(state: dict[str, object], message: str) -> None:
    _open_dialog(state, "text", error_modal("Data Catalog Interaction Error", "Harlequin could not execute an interaction from your data catalog.", message))


def _configured_tabs(state: dict[str, object]) -> list[str]:
    settings = cast(HarlequinSettings, state["settings"])
    tabs = ["Databases"]
    if isinstance(settings.show_files, Some):
        tabs.append("Files")
    if isinstance(settings.show_s3, Some):
        tabs.append("S3")
    return tabs


def _page_rows(state: dict[str, object]) -> int:
    app: Any = state["app"]
    window: Any = app.layout.current_window
    if window is not None:
        info: Any = window.render_info
        if info is not None:
            height: object = info.window_height
            if isinstance(height, int):
                return max(height, 1)
    service = state.get("size")
    if service is not None:
        _, rows = cast(Callable[[], tuple[int, int]], service)()
        return max(rows - 3 - int(len(_configured_tabs(state)) > 1), 1)
    return 1


def _move(state: dict[str, object], motion: TreeMotion) -> None:
    with _lock(state):
        entries_key, tree_key = _tab_keys(cast(str, state["catalog_tab"]))
        state[tree_key] = move_tree_cursor(CottList(values=_entries(state, entries_key)), _tree(state, tree_key), motion, _page_rows(state))
    _invalidate(state)


def _cursor_entry(state: dict[str, object]) -> CatalogEntry | None:
    entries_key, tree_key = _tab_keys(cast(str, state["catalog_tab"]))
    selected = tree_cursor_entry(CottList(values=_entries(state, entries_key)), _tree(state, tree_key))
    return selected.value if isinstance(selected, Some) else None


def _find(entries: list[CatalogEntry], entry_id: str) -> CatalogEntry | None:
    for entry in entries:
        if entry.id == entry_id:
            return entry
    return None


def _file_error(error: FileTreeError) -> str:
    if isinstance(error, FileTreeError_NotADirectory):
        return f"{error.path} is not a directory."
    return f"Could not read {error.path}: {error.message}"


def _s3_error(error: S3Error) -> str:
    if isinstance(error, S3Error_Unavailable):
        return error.message
    if isinstance(error, S3Error_AccessDenied):
        return f"Access denied to {error.target}."
    return f"{error.target}: {error.message}"


def _fetch_children(state: dict[str, object], tab: str, entry: CatalogEntry) -> CottList[CatalogEntry] | str:
    if tab == "Files":
        listed = list_directory(Path(entry.id), Some(value=entry.id), entry.depth + 1)
        if isinstance(listed, Ok):
            return listed.value
        return _file_error(listed.error)
    if tab == "S3":
        listed_s3 = list_s3(entry.id, Some(value=entry.id), entry.depth + 1)
        if isinstance(listed_s3, Ok):
            return listed_s3.value
        return _s3_error(listed_s3.error)
    with _lock(state):
        connection = _connection(state)
    if connection is None:
        return "There is no open connection."
    loaded = load_catalog_children(connection, entry)
    if isinstance(loaded, Ok):
        return loaded.value
    return loaded.error.message


def _load_worker(state: dict[str, object], tab: str, entry: CatalogEntry, insert_names: bool) -> None:
    result = _fetch_children(state, tab, entry)
    entries_key, _ = _tab_keys(tab)
    names: str | None = None
    with _lock(state):
        if isinstance(result, str):
            _catalog_error(state, result)
        else:
            entries = _entries(state, entries_key)
            if _find(entries, entry.id) is not None:
                merged = replace_children(CottList(values=entries), entry.id, result)
                state[entries_key] = list(merged)
                if insert_names:
                    children = catalog_children(merged, Some(value=entry.id))
                    names = ", ".join(child.query_name for child in children)
    if names is not None:
        _insert(state, names)
    _invalidate(state)


def _start_load(state: dict[str, object], tab: str, entry: CatalogEntry, insert_names: bool) -> None:
    threading.Thread(target=lambda: _load_worker(state, tab, entry, insert_names), daemon=True).start()


def _toggle(state: dict[str, object]) -> None:
    with _lock(state):
        tab = cast(str, state["catalog_tab"])
        entries_key, tree_key = _tab_keys(tab)
        entries = _entries(state, entries_key)
        toggled = toggle_tree_node(CottList(values=entries), _tree(state, tree_key))
        state[tree_key] = toggled.tree
        requested = toggled.load_children
        entry = _find(entries, requested.value) if isinstance(requested, Some) else None
    if entry is not None:
        _start_load(state, tab, entry, False)
    _invalidate(state)


def _insert_name(state: dict[str, object]) -> None:
    with _lock(state):
        entry = _cursor_entry(state)
    if entry is not None:
        _insert(state, entry.query_name)
        _invalidate(state)


def _copy_name(state: dict[str, object]) -> None:
    with _lock(state):
        entry = _cursor_entry(state)
    if entry is None:
        return
    copied = copy_to_clipboard(entry.query_name)
    if not isinstance(copied, Ok):
        with _lock(state):
            _notify(state, None, copied.error.message, "error")
        _invalidate(state)


def _show_menu(state: dict[str, object]) -> None:
    with _lock(state):
        entry = _cursor_entry(state)
        if entry is not None:
            context = cast(IdeContext, state["context"])
            _open_dialog(state, "menu", context_menu(entry, catalog_interactions(context.descriptor.kind, entry)))
    if entry is not None:
        _invalidate(state)


def _query_buffer_worker(state: dict[str, object], sql: str, failure: str) -> None:
    with _lock(state):
        connection = _connection(state)
    result = run_scalar_query(connection, sql) if connection is not None else None
    if isinstance(result, Ok) and isinstance(result.value, Some):
        _new_buffer(state, result.value.value)
    elif result is None or isinstance(result, Ok):
        _notify(state, None, failure, "error")
    else:
        _notify(state, None, f"{failure}: {result.error.message}", "error")
    _invalidate(state)


def _execute_worker(state: dict[str, object], plan: InteractionPlan_Execute) -> None:
    with _lock(state):
        connection = _connection(state)
    if connection is None:
        with _lock(state):
            _interaction_error(state, "There is no open connection.")
        _invalidate(state)
        return
    result = run_scalar_query(connection, plan.sql)
    with _lock(state):
        if isinstance(result, Ok):
            _notify(state, None, plan.success, "information")
        else:
            _interaction_error(state, result.error.message)
    _invalidate(state)
    if isinstance(result, Ok) and plan.refresh:
        with _lock(state):
            service = state.get("refresh_catalog")
        if service is not None:
            cast(Callable[[], None], service)()


def _start_execute(state: dict[str, object], plan: InteractionPlan_Execute) -> None:
    threading.Thread(target=lambda: _execute_worker(state, plan), daemon=True).start()


def _apply_plan(state: dict[str, object], local: dict[str, object], plan: InteractionPlan) -> None:
    if isinstance(plan, InteractionPlan_InsertText):
        _insert(state, plan.text)
    elif isinstance(plan, InteractionPlan_InsertChildNames):
        with _lock(state):
            entries = _entries(state, "catalog")
            parent = _find(entries, plan.parent)
            if parent is None:
                return
            if parent.loaded:
                names = ", ".join(child.query_name for child in catalog_children(CottList(values=entries), Some(value=parent.id)))
            else:
                names = None
        if names is None:
            _start_load(state, "Databases", parent, True)
        else:
            _insert(state, names)
    elif isinstance(plan, InteractionPlan_NewBuffer):
        _new_buffer(state, plan.text)
    elif isinstance(plan, InteractionPlan_NewBufferFromQuery):
        threading.Thread(target=lambda: _query_buffer_worker(state, plan.sql, plan.failure), daemon=True).start()
    else:
        confirm = plan.confirm
        if isinstance(confirm, Some):
            modal = ConfirmModal(prompt=confirm.value, yes_selected=False)
            local["pending"] = (plan, modal)
            _open_dialog(state, "confirm", modal)
        else:
            _start_execute(state, plan)


def _choose(state: dict[str, object], local: dict[str, object], entry: CatalogEntry, label: str) -> None:
    with _lock(state):
        context = cast(IdeContext, state["context"])
        entries_key, _ = _tab_keys(cast(str, state["catalog_tab"]))
        children = catalog_children(CottList(values=_entries(state, entries_key)), Some(value=entry.id))
    planned = plan_interaction(context.descriptor.kind, entry, label, children)
    if isinstance(planned, Some):
        _apply_plan(state, local, planned.value)


def _dialog_model(state: dict[str, object], kind: str) -> object | None:
    raw = state.get("dialog")
    if isinstance(raw, tuple):
        pair = cast(tuple[object, ...], raw)
        if len(pair) == 2 and pair[0] == kind:
            return pair[1]
    return None


def _menu_key(state: dict[str, object], local: dict[str, object], key: str, text: str) -> None:
    chosen: tuple[CatalogEntry, str] | None = None
    with _lock(state):
        model = _dialog_model(state, "menu")
        if not isinstance(model, ContextMenu):
            return
        step = context_menu_key(model, key)
        if isinstance(step.outcome, ContextMenuOutcome_Stay):
            _open_dialog(state, "menu", step.menu)
        elif isinstance(step.outcome, ContextMenuOutcome_Choose):
            _close_dialog(state)
            chosen = (step.menu.entry, step.outcome.label)
        else:
            _close_dialog(state)
    if chosen is not None:
        _choose(state, local, chosen[0], chosen[1])
    _invalidate(state)


def _confirm_key(state: dict[str, object], local: dict[str, object], key: str, text: str) -> None:
    accepted: InteractionPlan_Execute | None = None
    previous: object | None = None
    with _lock(state):
        pending = local.get("pending")
        model = _dialog_model(state, "confirm")
        if isinstance(pending, tuple):
            pair = cast(tuple[object, ...], pending)
            if len(pair) == 2 and isinstance(pair[0], InteractionPlan_Execute) and isinstance(pair[1], ConfirmModal) and model is pair[1]:
                plan = pair[0]
                step = confirm_key(pair[1], key)
                if isinstance(step.outcome, ConfirmOutcome_Stay):
                    local["pending"] = (plan, step.modal)
                    _open_dialog(state, "confirm", step.modal)
                else:
                    local["pending"] = None
                    _close_dialog(state)
                    if isinstance(step.outcome, ConfirmOutcome_Yes):
                        accepted = plan
            else:
                local["pending"] = None
                previous = local.get("previous_confirm")
        else:
            previous = local.get("previous_confirm")
    if previous is not None:
        cast(Callable[[str, str], None], previous)(key, text)
    if accepted is not None:
        _start_execute(state, accepted)
    _invalidate(state)


def _root_worker(state: dict[str, object], tab: str) -> None:
    with _lock(state):
        settings = cast(HarlequinSettings, state["settings"])
        files = settings.show_files
        s3_target = settings.show_s3
    roots: CottList[CatalogEntry] | None = None
    message = ""
    if tab == "Files":
        if not isinstance(files, Some):
            return
        listed = list_directory(Path(files.value).expanduser(), Nothing(), 0)
        if isinstance(listed, Ok):
            roots = listed.value
        else:
            message = _file_error(listed.error)
    else:
        if not isinstance(s3_target, Some):
            return
        listed_s3 = list_s3(s3_target.value, Nothing(), 0)
        if isinstance(listed_s3, Ok):
            roots = listed_s3.value
        else:
            message = _s3_error(listed_s3.error)
    entries_key, _ = _tab_keys(tab)
    with _lock(state):
        if roots is None:
            _catalog_error(state, message)
        else:
            state[entries_key] = list(roots)
    _invalidate(state)


def _switch_tab(state: dict[str, object], local: dict[str, object], step: int) -> None:
    with _lock(state):
        tabs = _configured_tabs(state)
        current = cast(str, state["catalog_tab"])
        tab = tabs[(tabs.index(current) + step) % len(tabs)]
        state["catalog_tab"] = tab
        shown = cast(set[str], local["shown"])
        first = tab != "Databases" and tab not in shown
        shown.add(tab)
    if first:
        threading.Thread(target=lambda: _root_worker(state, tab), daemon=True).start()
    _invalidate(state)


def _fallback_available(state: dict[str, object], key: str) -> bool:
    with _lock(state):
        layout = state["layout"]
        if not isinstance(layout, LayoutState) or not isinstance(layout.focus, Pane_Catalog) or layout.sidebar_hidden or layout.full_screen or state["dialog"] is not None:
            return False
        bindings = cast(tuple[BoundKey, ...], state["bound"])
        handlers = cast(dict[str, Callable[[], None]], state["handlers"])
        for binding in bindings:
            if binding.key == key and isinstance(binding.scope, (ActionScope_App, ActionScope_Catalog)) and binding.action in handlers:
                return False
        return True


def _bind_motion(state: dict[str, object], key: str, motion: TreeMotion) -> None:
    kb = cast(KeyBindings, state["kb"])
    callback: Callable[[KeyPressEvent], None] = lambda event: _move(state, motion)
    kb.add(key, filter=Condition(lambda: _fallback_available(state, key)))(callback)


def install_catalog_actions(session: IdeSession) -> Unit:
    handle = session.handle
    if handle.tag != "harlequin.ide":
        return Unit()
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return Unit()
    state = cast(dict[str, object], raw)
    handlers_raw = state.get("handlers")
    dialog_keys_raw = state.get("dialog_keys")
    if not isinstance(handlers_raw, dict) or not isinstance(dialog_keys_raw, dict):
        return Unit()
    handlers = cast(dict[str, Callable[[], None]], handlers_raw)
    dialog_keys = cast(dict[str, Callable[[str, str], None]], dialog_keys_raw)
    with _lock(state):
        local: dict[str, object] = {"pending": None, "shown": {"Databases"}, "previous_confirm": dialog_keys.get("confirm")}
        menu_callback: Callable[[str, str], None] = lambda key, text: _menu_key(state, local, key, text)
        confirm_callback: Callable[[str, str], None] = lambda key, text: _confirm_key(state, local, key, text)
        handlers["data_catalog.cursor_up"] = lambda: _move(state, TreeMotion_Up())
        handlers["data_catalog.cursor_down"] = lambda: _move(state, TreeMotion_Down())
        handlers["data_catalog.toggle_node"] = lambda: _toggle(state)
        handlers["data_catalog.select_cursor"] = lambda: _toggle(state)
        handlers["data_catalog.insert_name"] = lambda: _insert_name(state)
        handlers["data_catalog.copy_name"] = lambda: _copy_name(state)
        handlers["data_catalog.show_context_menu"] = lambda: _show_menu(state)
        handlers["data_catalog.next_tab"] = lambda: _switch_tab(state, local, 1)
        handlers["data_catalog.previous_tab"] = lambda: _switch_tab(state, local, -1)
        dialog_keys["menu"] = menu_callback
        dialog_keys["confirm"] = confirm_callback
        for key, motion in (("pageup", TreeMotion_PageUp()), ("pagedown", TreeMotion_PageDown()), ("home", TreeMotion_First()), ("end", TreeMotion_Last()), ("left", TreeMotion_Parent())):
            _bind_motion(state, key, motion)
    return Unit()
