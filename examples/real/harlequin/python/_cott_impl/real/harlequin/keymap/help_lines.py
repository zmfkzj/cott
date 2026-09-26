from typing import cast

from cott_runtime import CottList

from real.harlequin.keymap import key_label
from real.harlequin.keymap_types import ActionScope, ActionScope_App, ActionScope_Catalog, ActionScope_ContextMenu, ActionScope_Editor, ActionScope_Results, BoundKey, BoundKeySet


def _scope_index(scope: ActionScope) -> int:
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


def help_lines(bound: BoundKeySet) -> CottList[str]:
    headings = ["Application", "Query Editor", "Data Catalog", "Data Catalog Context Menu", "Results Viewer", "Query History"]
    items: tuple[BoundKey, ...] = ()
    if bound.handle.tag == "harlequin.bound_keys":
        items = cast(tuple[BoundKey, ...], bound.handle.unwrap())
    groups: list[dict[str, tuple[list[str], str]]] = [{} for _ in headings]
    for item in items:
        group = groups[_scope_index(item.scope)]
        entry = group.get(item.action)
        if entry is None:
            group[item.action] = ([key_label(item.key)], item.description)
        else:
            entry[0].append(key_label(item.key))
    lines: list[str] = []
    for index, heading in enumerate(headings):
        group = groups[index]
        if not group:
            continue
        lines.append(heading)
        for labels, description in group.values():
            lines.append(", ".join(labels).ljust(24) + description)
        lines.append("")
    return CottList(values=lines)
