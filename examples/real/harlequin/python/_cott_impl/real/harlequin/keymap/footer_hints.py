from typing import cast

from cott_runtime import CottList, Some

from real.harlequin.keymap import key_label
from real.harlequin.keymap_types import ActionScope, ActionScope_App, BoundKey, BoundKeySet, FooterHint


def _hints_for_scope(bound: tuple[BoundKey, ...], scope: ActionScope) -> list[FooterHint]:
    order: list[str] = []
    groups: dict[str, list[BoundKey]] = {}
    for item in bound:
        if not item.show or item.scope != scope:
            continue
        if item.action not in groups:
            order.append(item.action)
            groups[item.action] = []
        groups[item.action].append(item)
    hints: list[FooterHint] = []
    for action in order:
        keys = groups[action]
        first = keys[0]
        display = first.key_display
        if isinstance(display, Some):
            text = display.value
        else:
            text = "/".join(key_label(k.key) for k in keys)
        hints.append(FooterHint(key=text, description=first.description))
    return hints


def footer_hints(bound: BoundKeySet, focus: ActionScope) -> CottList[FooterHint]:
    handle = bound.handle
    items: tuple[BoundKey, ...] = ()
    if handle.tag == "harlequin.bound_keys":
        items = cast(tuple[BoundKey, ...], handle.unwrap())
    app = ActionScope_App()
    result = _hints_for_scope(items, app)
    if focus != app:
        result.extend(_hints_for_scope(items, focus))
    return CottList(values=result)
