from frogmouth.application_types import SidebarDock, SidebarDock_Left, SidebarDock_Right


def toggle_sidebar_dock(current: SidebarDock) -> SidebarDock:
    if current == SidebarDock_Left():
        return SidebarDock_Right()
    return SidebarDock_Left()
