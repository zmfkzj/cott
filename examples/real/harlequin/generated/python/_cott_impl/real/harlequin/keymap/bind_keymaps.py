from cott_runtime import CottList, Err, Nothing, Ok, Opaque, Result

from real.harlequin.keymap import harlequin_actions
from real.harlequin.keymap_types import (
    ActionScope,
    ActionScope_App,
    ActionScope_Catalog,
    ActionScope_ContextMenu,
    ActionScope_Editor,
    ActionScope_History,
    ActionScope_Results,
    ActionSpec,
    BoundKey,
    BoundKeySet,
    KeyMap,
    KeymapError,
    KeymapError_EmptyKey,
    KeymapError_UnknownAction,
    KeymapError_UnknownKeymap,
)


def _scope_rank(scope: ActionScope) -> int:
    if isinstance(scope, ActionScope_App):
        return 0
    if isinstance(scope, ActionScope_Editor):
        return 1
    if isinstance(scope, ActionScope_Catalog):
        return 2
    if isinstance(scope, ActionScope_ContextMenu):
        return 3
    if isinstance(scope, ActionScope_Results):
        return 4
    return 5


def _err(error: KeymapError) -> Result[BoundKeySet, KeymapError]:
    return Err(error=error)


def bind_keymaps(available: CottList[KeyMap], names: CottList[str]) -> Result[BoundKeySet, KeymapError]:
    specs: dict[str, ActionSpec] = {}
    for scope in (
        ActionScope_App(),
        ActionScope_Editor(),
        ActionScope_Catalog(),
        ActionScope_ContextMenu(),
        ActionScope_Results(),
        ActionScope_History(),
    ):
        for spec in harlequin_actions(scope):
            specs[spec.name] = spec

    keymaps: dict[str, KeyMap] = {}
    for keymap in available:
        keymaps[keymap.name] = keymap

    bound: dict[tuple[int, str], BoundKey] = {}
    quit_bound = False
    for name in names:
        keymap = keymaps.get(name)
        if keymap is None:
            return _err(KeymapError_UnknownKeymap(name=name))
        for binding in keymap.bindings:
            spec = specs.get(binding.action)
            if spec is None:
                return _err(KeymapError_UnknownAction(keymap=keymap.name, action=binding.action))
            if binding.action == "quit":
                quit_bound = True
            for raw in binding.keys.split(","):
                key = raw.strip().lower()
                if not key:
                    return _err(KeymapError_EmptyKey(keymap=keymap.name, action=binding.action))
                bound[(_scope_rank(spec.scope), key)] = BoundKey(
                    key=key,
                    action=spec.name,
                    scope=spec.scope,
                    description=spec.description,
                    show=spec.show,
                    priority=spec.priority,
                    key_display=binding.key_display,
                )

    if quit_bound:
        payload = tuple(bound.values())
    else:
        payload = (
            *bound.values(),
            BoundKey(
                key="ctrl+q",
                action="quit",
                scope=ActionScope_App(),
                description="Quit",
                show=True,
                priority=True,
                key_display=Nothing(),
            ),
        )
    return Ok(value=BoundKeySet(handle=Opaque(tag="harlequin.bound_keys", value=payload), count=len(payload)))
