from real.harlequin.ide import visible_panes
from real.harlequin.ide_types import LayoutState, Pane, Pane_Catalog, Pane_Editor, Pane_Results, Pane_RunBar


def _order(pane: Pane) -> int:
    if isinstance(pane, Pane_Catalog):
        return 0
    if isinstance(pane, Pane_Editor):
        return 1
    if isinstance(pane, Pane_RunBar):
        return 2
    return 3


def _pane_at(index: int) -> Pane:
    if index == 0:
        return Pane_Catalog()
    if index == 1:
        return Pane_Editor()
    if index == 2:
        return Pane_RunBar()
    return Pane_Results()


def _shows_editor(layout: LayoutState) -> bool:
    return _order(layout.focus) in (1, 2)


def _cycle(layout: LayoutState, step: int) -> LayoutState:
    visible = sorted(_order(p) for p in visible_panes(layout))
    if not visible:
        return layout
    current = _order(layout.focus)
    target = visible[0] if step > 0 else visible[-1]
    if step > 0:
        for index in visible:
            if index > current:
                target = index
                break
    else:
        for index in reversed(visible):
            if index < current:
                target = index
                break
    return LayoutState(focus=_pane_at(target), sidebar_hidden=layout.sidebar_hidden, full_screen=layout.full_screen)


def layout_action(layout: LayoutState, action: str) -> LayoutState:
    focus = layout.focus
    hidden = layout.sidebar_hidden
    full = layout.full_screen
    if action == "toggle_sidebar":
        new_hidden = not hidden
        new_focus: Pane = Pane_Editor() if new_hidden and _order(focus) == 0 else focus
        return LayoutState(focus=new_focus, sidebar_hidden=new_hidden, full_screen=full)
    if action == "toggle_full_screen":
        new_full = not full
        new_focus = Pane_Editor() if new_full and _order(focus) in (0, 2) else focus
        return LayoutState(focus=new_focus, sidebar_hidden=hidden, full_screen=new_full)
    if action == "focus_query_editor":
        leave = full and not _shows_editor(layout)
        return LayoutState(focus=Pane_Editor(), sidebar_hidden=hidden, full_screen=full and not leave)
    if action == "focus_results_viewer":
        leave = full and _shows_editor(layout)
        return LayoutState(focus=Pane_Results(), sidebar_hidden=hidden, full_screen=full and not leave)
    if action == "focus_data_catalog":
        return LayoutState(focus=Pane_Catalog(), sidebar_hidden=False, full_screen=False)
    if action == "focus_next":
        return _cycle(layout, 1)
    if action == "focus_previous":
        return _cycle(layout, -1)
    return layout
