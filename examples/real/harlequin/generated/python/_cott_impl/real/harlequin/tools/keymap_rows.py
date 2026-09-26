from cott_runtime import CottList, Nothing, Some

from real.harlequin.keymap import harlequin_actions
from real.harlequin.keymap_types import ActionScope, ActionScope_App, ActionScope_Catalog, ActionScope_ContextMenu, ActionScope_Editor, ActionScope_History, ActionScope_Results, ActionSpec, KeyMap
from real.harlequin.tools_types import KeyRow


def _scope_title(scope: ActionScope) -> str:
    if isinstance(scope, ActionScope_App):
        return "App"
    if isinstance(scope, ActionScope_Editor):
        return "Code Editor"
    if isinstance(scope, ActionScope_Catalog):
        return "Data Catalog"
    if isinstance(scope, ActionScope_ContextMenu):
        return "Context Menu"
    if isinstance(scope, ActionScope_Results):
        return "Results Viewer"
    return "History Screen"


def _position(action: ActionSpec) -> int:
    return action.position


def keymap_rows(available: CottList[KeyMap], active: CottList[str]) -> CottList[KeyRow]:
    """Build one editor row per action, merging keys from the active keymaps in order."""
    scopes: list[ActionScope] = [
        ActionScope_App(),
        ActionScope_Editor(),
        ActionScope_Catalog(),
        ActionScope_ContextMenu(),
        ActionScope_Results(),
        ActionScope_History(),
    ]
    actions: list[ActionSpec] = []
    for scope in scopes:
        for action in harlequin_actions(scope):
            actions.append(action)
    actions.sort(key=lambda action: _position(action))
    keys_by_action: dict[str, set[str]] = {action.name: set() for action in actions}
    displays: dict[str, str] = {}
    keymaps: dict[str, KeyMap] = {}
    for keymap in available:
        if keymap.name not in keymaps:
            keymaps[keymap.name] = keymap
    for name in active:
        keymap = keymaps.get(name)
        if keymap is None:
            continue
        for binding in keymap.bindings:
            keys = keys_by_action.get(binding.action)
            if keys is None:
                continue
            for piece in binding.keys.split(","):
                key = piece.strip()
                if key:
                    keys.add(key)
            display = binding.key_display
            if isinstance(display, Some) and display.value:
                displays[binding.action] = display.value
    rows: list[KeyRow] = []
    for action in actions:
        rows.append(
            KeyRow(
                action=action.name,
                title=f"{_scope_title(action.scope)}: {action.description}",
                keys=CottList(values=sorted(keys_by_action[action.name])),
                key_display=Some(value=displays[action.name]) if action.name in displays else Nothing(),
            )
        )
    return CottList(values=rows)
