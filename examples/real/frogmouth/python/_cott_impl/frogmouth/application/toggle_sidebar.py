from frogmouth.application_types import SidebarMode, SidebarMode_Hidden


def toggle_sidebar(current: SidebarMode, requested: SidebarMode) -> SidebarMode:
    if current == requested:
        return SidebarMode_Hidden()
    return requested
