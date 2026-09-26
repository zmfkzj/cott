from dataclasses import replace

from cott_runtime import CottList, Nothing, Option, Some, U64
from real.toolong.view import viewer_layout
from real.toolong.view_types import Notification, Severity, Severity_Error, TabView, ViewerEvent, ViewerEvent_Breaks, ViewerEvent_Complete, ViewerEvent_Found, ViewerEvent_Jumped, ViewerEvent_Loaded, ViewerEvent_Notify, ViewerEvent_OpenFailed, ViewerEvent_PanelSize, ViewerEvent_Progress, ViewerEvent_Resize, ViewerEvent_Suggestion, ViewerEvent_Tailed, ViewerEvent_Tick, ViewerEvent_Widths, ViewerLayout, ViewerRequest, ViewerRequest_Bell, ViewerState, ViewerUpdate


def _layout_for(viewer: ViewerState, index: int) -> ViewerLayout:
    return viewer_layout(replace(viewer, active=index))


def _clamp(value: int, high: int) -> int:
    return max(0, min(value, max(0, high)))


def _max_scroll_y(tab: TabView, layout: ViewerLayout) -> int:
    return max(0, tab.line_count - layout.text.height)


def _max_scroll_x(tab: TabView, layout: ViewerLayout) -> int:
    extra = layout.gutter if (isinstance(tab.pointer, Some) or tab.line_numbers) else 0
    return max(0, tab.content_width + extra - layout.text.width)


def _clamp_panel(tab: TabView, layout: ViewerLayout) -> TabView:
    panel = layout.panel
    if isinstance(panel, Some):
        rows = tab.panel_lines - max(0, panel.value.height - 2)
        cols = tab.panel_width - max(0, panel.value.width - 6)
        return replace(tab, panel_scroll_y=_clamp(tab.panel_scroll_y, rows), panel_scroll_x=_clamp(tab.panel_scroll_x, cols))
    else:
        return tab


def _clamp_all(tab: TabView, layout: ViewerLayout) -> TabView:
    tab = replace(tab, scroll_y=_clamp(tab.scroll_y, _max_scroll_y(tab, layout)), scroll_x=_clamp(tab.scroll_x, _max_scroll_x(tab, layout)))
    return _clamp_panel(tab, layout)


def _set_pointer(tab: TabView, pointer: Option[U64]) -> TabView:
    new: Option[U64]
    if isinstance(pointer, Some) and tab.line_count > 0:
        new = Some(value=_clamp(pointer.value, tab.line_count - 1))
    else:
        new = Nothing()
    if new != tab.pointer:
        tab = replace(tab, pointer=new, panel_scroll_x=0, panel_scroll_y=0)
    if isinstance(new, Some):
        return tab
    else:
        return replace(tab, show_panel=False)


def _center(tab: TabView, layout: ViewerLayout) -> TabView:
    pointer = tab.pointer
    if isinstance(pointer, Some):
        page = layout.text.height
        return replace(tab, scroll_y=_clamp(pointer.value - page // 2, _max_scroll_y(tab, layout)))
    else:
        return tab


def _tail_on(tab: TabView, layout: ViewerLayout) -> TabView:
    if tab.tail:
        return tab
    tab = replace(tab, tail=True, pending_lines=0)
    if not tab.merged:
        tab = replace(tab, line_count=max(1, tab.break_count))
    tab = _set_pointer(tab, Nothing())
    return replace(tab, scroll_y=_max_scroll_y(tab, layout))


def _notify(viewer: ViewerState, title: str, message: str, severity: Severity) -> ViewerState:
    note = Notification(title=title, message=message, severity=severity, expires_ms=viewer.now_ms + 5000)
    return replace(viewer, notifications=CottList(values=[n for n in viewer.notifications] + [note]))


def _event_tab(event: ViewerEvent, tab: TabView, layout: ViewerLayout, requests: list[ViewerRequest], notes: list[str]) -> TabView:
    page = layout.text.height
    if isinstance(event, ViewerEvent_Progress):
        tab = replace(tab, scan_message=event.message, scan_progress=event.progress)
    elif isinstance(event, ViewerEvent_Breaks):
        tab = replace(tab, break_count=event.count, loading=False)
        if not tab.merged:
            tab = replace(tab, line_count=max(1, event.count))
    elif isinstance(event, ViewerEvent_Complete):
        count = event.count if tab.merged else max(1, event.count)
        tab = replace(tab, break_count=event.count, line_count=count, loading=False, scan_running=False, scan_tint=False, scan_message="")
        tab = _tail_on(tab, layout)
    elif isinstance(event, ViewerEvent_Tailed):
        if not tab.tail:
            tab = replace(tab, pending_lines=max(0, event.before - tab.line_count + 1))
        tab = replace(tab, loading=False, break_count=event.after)
        if tab.tail or event.before == 0:
            tab = replace(tab, line_count=max(1, event.after))
        if tab.tail:
            tab = replace(tab, scroll_y=_max_scroll_y(tab, layout))
    elif isinstance(event, ViewerEvent_OpenFailed):
        notes.append(event.message)
        tab = replace(tab, loading=False, scan_running=False)
    elif isinstance(event, ViewerEvent_Loaded):
        tab = replace(tab, loading=False)
    elif isinstance(event, ViewerEvent_Widths):
        tab = replace(tab, content_width=max(tab.content_width, event.width))
    elif isinstance(event, ViewerEvent_PanelSize):
        tab = replace(tab, panel_lines=event.lines, panel_width=event.width)
        tab = _clamp_panel(tab, layout)
    elif isinstance(event, ViewerEvent_Found):
        if event.invalid_regex:
            notes.append("Regex is invalid!")
        line = event.line
        if isinstance(line, Some):
            tab = _center(_set_pointer(tab, Some(value=line.value)), layout)
        else:
            requests.append(ViewerRequest_Bell())
            pointer = tab.pointer
            if isinstance(pointer, Some) and (pointer.value < tab.scroll_y or pointer.value > tab.scroll_y + page - 1):
                tab = _center(tab, layout)
    elif isinstance(event, ViewerEvent_Jumped):
        line = event.line
        if isinstance(line, Some):
            tab = _center(_set_pointer(tab, Some(value=line.value)), layout)
        else:
            requests.append(ViewerRequest_Bell())
    return tab


def apply_event(viewer: ViewerState, event: ViewerEvent) -> ViewerUpdate:
    requests: list[ViewerRequest] = []
    if isinstance(event, ViewerEvent_Tick):
        kept = [n for n in viewer.notifications if n.expires_ms > event.now_ms]
        viewer = replace(viewer, now_ms=event.now_ms, notifications=CottList(values=kept))
    elif isinstance(event, ViewerEvent_Resize):
        viewer = replace(viewer, width=event.width, height=event.height)
        clamped: list[TabView] = []
        for index, tab in enumerate(viewer.tabs):
            clamped.append(_clamp_all(tab, _layout_for(viewer, index)))
        viewer = replace(viewer, tabs=CottList(values=clamped))
    elif isinstance(event, ViewerEvent_Notify):
        viewer = _notify(viewer, event.title, event.message, event.severity)
    elif isinstance(event, ViewerEvent_Suggestion):
        for index, tab in enumerate(viewer.tabs):
            if index == viewer.active and tab.find_input.value == event.value:
                viewer = replace(viewer, suggestion=event.suggestion)
    else:
        notes: list[str] = []
        updated: list[TabView] = []
        for index, tab in enumerate(viewer.tabs):
            if index == event.tab:
                tab = _event_tab(event, tab, _layout_for(viewer, index), requests, notes)
            updated.append(tab)
        viewer = replace(viewer, tabs=CottList(values=updated))
        for message in notes:
            viewer = _notify(viewer, "", message, Severity_Error())
    return ViewerUpdate(viewer=viewer, requests=CottList(values=requests))
