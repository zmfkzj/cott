from real.harlequin.ide_types import ContextMenu, ContextMenuOutcome_Choose, ContextMenuOutcome_Close, ContextMenuOutcome_Stay, ContextMenuStep


def context_menu_key(menu: ContextMenu, key: str) -> ContextMenuStep:
    items = list(menu.items)
    count = len(items)
    if key == "up" or key == "down":
        selected = menu.selected - 1 if key == "up" else menu.selected + 1
        selected = max(0, min(selected, count - 1))
        moved = ContextMenu(entry=menu.entry, items=menu.items, selected=selected)
        return ContextMenuStep(menu=moved, outcome=ContextMenuOutcome_Stay())
    if key == "enter":
        if menu.selected < count:
            return ContextMenuStep(menu=menu, outcome=ContextMenuOutcome_Choose(label=items[menu.selected]))
        return ContextMenuStep(menu=menu, outcome=ContextMenuOutcome_Stay())
    if key == "escape" or key == "full_stop":
        return ContextMenuStep(menu=menu, outcome=ContextMenuOutcome_Close())
    return ContextMenuStep(menu=menu, outcome=ContextMenuOutcome_Stay())
