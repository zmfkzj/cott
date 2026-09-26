import pathlib

from cott_runtime import CottList, Nothing, U16
from real.toolong.keys_types import TextInput
from real.toolong.model_types import TabPlan
from real.toolong.view_types import Focus_Lines, Modal_Closed, TabView, ViewerState


def _tab_view(plan: TabPlan) -> TabView:
    names: list[str] = []
    for path in plan.paths:
        names.append(pathlib.PurePath(path).name)
    return TabView(
        title=plan.title,
        file_names=CottList(values=names),
        merged=plan.merged,
        can_tail=not plan.merged,
        tail=False,
        scroll_x=0,
        scroll_y=0,
        pointer=Nothing(),
        line_numbers=False,
        show_panel=False,
        panel_scroll_x=0,
        panel_scroll_y=0,
        panel_lines=0,
        panel_width=0,
        show_find=False,
        find_input=TextInput(value="", cursor=0),
        case_sensitive=False,
        regex=False,
        break_count=0,
        line_count=0,
        content_width=0,
        pending_lines=0,
        loading=True,
        scan_running=True,
        scan_tint=True,
        scan_message="",
        scan_progress=0.0,
    )


def initial_viewer(plans: CottList[TabPlan], width: U16, height: U16) -> ViewerState:
    tabs: list[TabView] = []
    for plan in plans:
        tabs.append(_tab_view(plan))
    return ViewerState(
        tabs=CottList(values=tabs),
        active=0,
        focus=Focus_Lines(),
        modal=Modal_Closed(),
        notifications=CottList(values=[]),
        suggestion="",
        width=width,
        height=height,
        now_ms=0,
    )
