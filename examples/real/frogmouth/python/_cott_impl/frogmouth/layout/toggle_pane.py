from frogmouth.layout_types import Pane, Sidebar, Visibility_Hidden, Visibility_Shown


def toggle_pane(sidebar: Sidebar, pane: Pane) -> Sidebar:
    if isinstance(sidebar.visibility, Visibility_Shown) and sidebar.active == pane:
        return Sidebar(visibility=Visibility_Hidden(), active=pane)
    return Sidebar(visibility=Visibility_Shown(), active=pane)
