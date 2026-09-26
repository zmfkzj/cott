from typing import Final

from frogmouth.layout_types import CycleDirection, CycleDirection_Next, CycleDirection_Previous, Pane, Pane_Bookmarks, Pane_Contents, Pane_History, Pane_Local, Sidebar

_PANE_COUNT: Final[int] = 4


def _pane_index(pane: Pane) -> int:
    match pane:
        case Pane_Contents():
            return 0
        case Pane_Local():
            return 1
        case Pane_Bookmarks():
            return 2
        case Pane_History():
            return 3


def _pane_at(index: int) -> Pane:
    if index == 0:
        return Pane_Contents()
    if index == 1:
        return Pane_Local()
    if index == 2:
        return Pane_Bookmarks()
    return Pane_History()


def _step(direction: CycleDirection) -> int:
    match direction:
        case CycleDirection_Next():
            return 1
        case CycleDirection_Previous():
            return -1


def cycle_pane(sidebar: Sidebar, direction: CycleDirection) -> Sidebar:
    index = (_pane_index(sidebar.active) + _step(direction)) % _PANE_COUNT
    return Sidebar(visibility=sidebar.visibility, active=_pane_at(index))
