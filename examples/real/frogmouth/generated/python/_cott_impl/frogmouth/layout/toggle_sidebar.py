from frogmouth.layout_types import Sidebar, Visibility_Hidden, Visibility_Shown


def toggle_sidebar(sidebar: Sidebar) -> Sidebar:
    if sidebar.visibility == Visibility_Shown():
        return Sidebar(visibility=Visibility_Hidden(), active=sidebar.active)
    return Sidebar(visibility=Visibility_Shown(), active=sidebar.active)
