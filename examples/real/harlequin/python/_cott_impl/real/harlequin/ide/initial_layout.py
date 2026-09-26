from real.harlequin.ide_types import LayoutState, Pane_Editor


def initial_layout() -> LayoutState:
    return LayoutState(focus=Pane_Editor(), sidebar_hidden=False, full_screen=False)
