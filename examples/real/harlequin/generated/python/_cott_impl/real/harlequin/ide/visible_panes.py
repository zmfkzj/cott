from cott_runtime import CottList
from real.harlequin.ide_types import LayoutState, Pane, Pane_Catalog, Pane_Editor, Pane_Results, Pane_RunBar


def visible_panes(layout: LayoutState) -> CottList[Pane]:
    if layout.full_screen:
        if isinstance(layout.focus, (Pane_Editor, Pane_RunBar)):
            return CottList(values=[Pane_Editor(), Pane_RunBar()])
        return CottList(values=[Pane_Results()])
    panes: list[Pane] = []
    if not layout.sidebar_hidden:
        panes.append(Pane_Catalog())
    panes.extend([Pane_Editor(), Pane_RunBar(), Pane_Results()])
    return CottList(values=panes)
