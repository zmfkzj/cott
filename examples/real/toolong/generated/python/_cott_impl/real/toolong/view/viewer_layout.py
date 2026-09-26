from cott_runtime import Nothing, Option, Some
from real.toolong.model_types import Rect
from real.toolong.view_types import TabView, ViewerLayout, ViewerState


def _sub(a: int, b: int) -> int:
    return a - b if a > b else 0


def viewer_layout(viewer: ViewerState) -> ViewerLayout:
    w = viewer.width
    h = viewer.height
    footer = Rect(x=0, y=_sub(h, 1), width=w, height=1 if h > 0 else 0)
    count = 0
    tab: TabView | None = None
    for candidate in viewer.tabs:
        if count == viewer.active:
            tab = candidate
        count += 1
    empty = Rect(x=0, y=0, width=0, height=0)
    if tab is None:
        return ViewerLayout(tabs=Nothing(), find=Nothing(), lines_box=empty, text=empty, panel=Nothing(), footer=footer, gutter=0)
    top = 0
    tabs_rect: Option[Rect] = Nothing()
    if count > 1:
        tabs_rect = Some(value=Rect(x=0, y=0, width=w, height=3))
        top = 3
    find_rect: Option[Rect] = Nothing()
    if tab.show_find:
        find_rect = Some(value=Rect(x=0, y=top, width=w, height=4))
        top += 4
    body_height = _sub(_sub(h, 1), top)
    panel_rect: Option[Rect] = Nothing()
    if tab.show_panel:
        half = w // 2
        panel_rect = Some(value=Rect(x=w - half, y=top, width=half, height=body_height))
        lines_box = Rect(x=0, y=top, width=w - half, height=body_height)
    else:
        lines_box = Rect(x=0, y=top, width=w, height=body_height)
    text = Rect(x=lines_box.x + 1, y=lines_box.y + 1, width=_sub(lines_box.width, 4), height=_sub(lines_box.height, 3))
    gutter = 0
    if tab.line_numbers:
        gutter = len(str(tab.scroll_y + text.height + 1)) + 1
    if isinstance(tab.pointer, Some):
        gutter += 3
    else:
        gutter += 0
    return ViewerLayout(tabs=tabs_rect, find=find_rect, lines_box=lines_box, text=text, panel=panel_rect, footer=footer, gutter=gutter)
