import dataclasses
from typing import cast

from cott_runtime import CottList, Nothing, Some
from real.toolong.help import help_markdown, help_title
from real.toolong.keys_types import TextInput
from real.toolong.view import viewer_layout
from real.toolong.view_types import Focus, Focus_FindCase, Focus_FindInput, Focus_FindRegex, Focus_Lines, Focus_Panel, Focus_Tabs, Modal_Closed, Modal_Goto, Modal_Help, Notification, Severity, Severity_Error, Severity_Information, Severity_Warning, TabView, ViewerAction, ViewerAction_CloseGoto, ViewerAction_CloseHelp, ViewerAction_Dismiss, ViewerAction_DismissFind, ViewerAction_FocusNext, ViewerAction_FocusPrevious, ViewerAction_Goto, ViewerAction_Help, ViewerAction_HelpDown, ViewerAction_HelpEnd, ViewerAction_HelpHome, ViewerAction_HelpPageDown, ViewerAction_HelpPageUp, ViewerAction_HelpUp, ViewerAction_Navigate, ViewerAction_NextTab, ViewerAction_OpenLink, ViewerAction_PageDown, ViewerAction_PageUp, ViewerAction_PanelDown, ViewerAction_PanelHome, ViewerAction_PanelLeft, ViewerAction_PanelPageDown, ViewerAction_PanelPageUp, ViewerAction_PanelRight, ViewerAction_PanelUp, ViewerAction_PointerDown, ViewerAction_PointerUp, ViewerAction_PreviousTab, ViewerAction_Quit, ViewerAction_ScrollDown, ViewerAction_ScrollEnd, ViewerAction_ScrollHome, ViewerAction_ScrollLeft, ViewerAction_ScrollRight, ViewerAction_ScrollUp, ViewerAction_Select, ViewerAction_ShowFind, ViewerAction_Tail, ViewerAction_ToggleCase, ViewerAction_ToggleLineNumbers, ViewerAction_ToggleRegex, ViewerAction_ToggleTail, ViewerRequest, ViewerRequest_CancelScan, ViewerRequest_FindNext, ViewerRequest_Navigate, ViewerRequest_OpenLink, ViewerRequest_Quit, ViewerState, ViewerUpdate


def _sat(value: int) -> int:
    return value if value > 0 else 0


def _clamp(value: int, high: int) -> int:
    return min(max(value, 0), _sat(high))


def _ptr(tab: TabView) -> int | None:
    pointer = tab.pointer
    if isinstance(pointer, Some):
        return int(pointer.value)
    else:
        return None


def _set_pointer(tab: TabView, new: int | None) -> TabView:
    old = _ptr(tab)
    if new is not None:
        new = None if tab.line_count == 0 else _clamp(new, tab.line_count - 1)
    if new is None:
        tab = dataclasses.replace(tab, pointer=Nothing(), show_panel=False)
    else:
        tab = dataclasses.replace(tab, pointer=Some(value=new))
    if new != old:
        tab = dataclasses.replace(tab, panel_scroll_x=0, panel_scroll_y=0)
    return tab


def _max_y(tab: TabView, page: int) -> int:
    return _sat(tab.line_count - page)


def _max_x(tab: TabView, gutter: int, text_width: int) -> int:
    extra = gutter if (_ptr(tab) is not None or tab.line_numbers) else 0
    return _sat(tab.content_width + extra - text_width)


def _set_y(tab: TabView, value: int, page: int) -> TabView:
    return dataclasses.replace(tab, scroll_y=_clamp(value, _max_y(tab, page)))


def _center(tab: TabView, page: int) -> TabView:
    pointer = _ptr(tab)
    if pointer is None:
        return tab
    return _set_y(tab, pointer - page // 2, page)


def _tail_on(tab: TabView, page: int) -> TabView:
    if tab.tail:
        return tab
    tab = dataclasses.replace(tab, tail=True, pending_lines=0)
    if not tab.merged:
        tab = dataclasses.replace(tab, line_count=max(1, tab.break_count))
    tab = dataclasses.replace(tab, scroll_y=_max_y(tab, page))
    return _set_pointer(tab, None)


def _tail_off(tab: TabView) -> TabView:
    if not tab.tail:
        return tab
    return dataclasses.replace(tab, tail=False, pending_lines=0)


def _advance(tab: TabView, direction: int, page: int, active: int, requests: list[ViewerRequest]) -> TabView:
    old = _ptr(tab)
    if old is not None:
        start = old + direction
    elif direction > 0:
        start = int(tab.scroll_y)
    else:
        start = int(tab.scroll_y) + page - 1
    if tab.show_find:
        requests.append(ViewerRequest_FindNext(tab=active, start=start, direction=direction))
        return tab
    if 0 <= start <= tab.line_count - 1:
        tab = _set_pointer(tab, start)
    elif old is None or old == 0:
        tab = _set_pointer(tab, int(tab.scroll_y))
    else:
        tab = _set_pointer(tab, old)
    pointer = _ptr(tab)
    if old is not None and pointer is not None and not (tab.scroll_y <= pointer <= tab.scroll_y + page - 1):
        tab = _center(tab, page)
    return tab


def _notify(notes: list[Notification], now: int, title: str, message: str, severity: Severity) -> None:
    notes.append(Notification(title=title, message=message, severity=severity, expires_ms=now + 5000))


def _focus_chain(tab: TabView, tab_count: int) -> list[Focus]:
    chain: list[Focus] = []
    if tab_count > 1:
        chain.append(Focus_Tabs())
    chain.append(Focus_Lines())
    if tab.show_panel:
        chain.append(Focus_Panel())
    if tab.show_find:
        chain.extend([Focus_FindInput(), Focus_FindCase(), Focus_FindRegex()])
    return chain


def _help_content_height(viewer: ViewerState) -> int:
    return _sat(_sat(viewer.height - 9) - 2)


def _help_max(viewer: ViewerState) -> int:
    content_w = _sat(_sat(viewer.width - 16) - 4)
    total = 0
    for _line in help_title(content_w):
        total += 1
    payload: object = help_markdown(content_w).unwrap()
    if not isinstance(payload, tuple):
        raise TypeError("help markdown payload is not a tuple")
    lines = cast(tuple[object, ...], payload)
    total += len(lines)
    return _sat(total - _help_content_height(viewer))


def apply_action(viewer: ViewerState, action: ViewerAction) -> ViewerUpdate:
    requests: list[ViewerRequest] = []
    notes: list[Notification] = [note for note in viewer.notifications]
    now = int(viewer.now_ms)
    help_actions = (ViewerAction_HelpUp, ViewerAction_HelpDown, ViewerAction_HelpPageUp, ViewerAction_HelpPageDown, ViewerAction_HelpHome, ViewerAction_HelpEnd)
    if isinstance(action, ViewerAction_Quit):
        requests.append(ViewerRequest_Quit())
        return ViewerUpdate(viewer=viewer, requests=CottList(values=requests))
    if isinstance(action, ViewerAction_Help):
        return ViewerUpdate(viewer=dataclasses.replace(viewer, modal=Modal_Help(scroll=0)), requests=CottList(values=requests))
    if isinstance(action, ViewerAction_CloseHelp):
        return ViewerUpdate(viewer=dataclasses.replace(viewer, modal=Modal_Closed()), requests=CottList(values=requests))
    if isinstance(action, ViewerAction_OpenLink):
        _notify(notes, now, "Link", "Opening " + action.url, Severity_Information())
        requests.append(ViewerRequest_OpenLink(url=action.url))
        return ViewerUpdate(viewer=dataclasses.replace(viewer, notifications=CottList(values=notes)), requests=CottList(values=requests))
    if isinstance(action, help_actions):
        current = viewer.modal
        if not isinstance(current, Modal_Help):
            return ViewerUpdate(viewer=viewer, requests=CottList(values=requests))
        scroll = int(current.scroll)
        high = _help_max(viewer)
        if isinstance(action, ViewerAction_HelpUp):
            scroll -= 1
        elif isinstance(action, ViewerAction_HelpDown):
            scroll += 1
        elif isinstance(action, ViewerAction_HelpPageUp):
            scroll -= _help_content_height(viewer)
        elif isinstance(action, ViewerAction_HelpPageDown):
            scroll += _help_content_height(viewer)
        elif isinstance(action, ViewerAction_HelpHome):
            scroll = 0
        else:
            scroll = high
        return ViewerUpdate(viewer=dataclasses.replace(viewer, modal=Modal_Help(scroll=_clamp(scroll, high))), requests=CottList(values=requests))

    tabs: list[TabView] = [item for item in viewer.tabs]
    active = int(viewer.active)
    if len(tabs) == 0 or active >= len(tabs):
        return ViewerUpdate(viewer=viewer, requests=CottList(values=requests))
    tab = tabs[active]
    layout = viewer_layout(viewer)
    page = int(layout.text.height)
    gutter = int(layout.gutter)
    text_width = int(layout.text.width)
    focus = viewer.focus
    modal = viewer.modal
    pointer = _ptr(tab)

    if isinstance(action, ViewerAction_CloseGoto):
        modal = Modal_Closed()
    elif isinstance(action, ViewerAction_Goto):
        value = str((pointer if pointer is not None else int(tab.scroll_y)) + 1)
        modal = Modal_Goto(input=TextInput(value=value, cursor=len(value)))
    elif isinstance(action, (ViewerAction_FocusNext, ViewerAction_FocusPrevious)):
        chain = _focus_chain(tab, len(tabs))
        index = -1
        position = 0
        for item in chain:
            if item == focus:
                index = position
            position += 1
        if isinstance(action, ViewerAction_FocusNext):
            focus = chain[0] if index < 0 else chain[(index + 1) % len(chain)]
        else:
            focus = chain[-1] if index < 0 else chain[(index - 1) % len(chain)]
    elif isinstance(action, (ViewerAction_PreviousTab, ViewerAction_NextTab)):
        step = -1 if isinstance(action, ViewerAction_PreviousTab) else 1
        active = (active + step) % len(tabs)
    elif isinstance(action, ViewerAction_ScrollUp):
        if pointer is None:
            tab = _set_y(tab, tab.scroll_y - 1, page)
        else:
            tab = _advance(tab, -1, page, active, requests)
        tab = _tail_off(tab)
    elif isinstance(action, ViewerAction_ScrollDown):
        if pointer is None:
            tab = _set_y(tab, tab.scroll_y + 1, page)
        else:
            tab = _advance(tab, 1, page, active, requests)
    elif isinstance(action, (ViewerAction_ScrollLeft, ViewerAction_ScrollRight)):
        step = -1 if isinstance(action, ViewerAction_ScrollLeft) else 1
        tab = dataclasses.replace(tab, scroll_x=_clamp(tab.scroll_x + step, _max_x(tab, gutter, text_width)))
    elif isinstance(action, ViewerAction_ScrollHome):
        if pointer is not None:
            tab = _set_pointer(tab, 0)
        tab = _tail_off(_set_y(tab, 0, page))
    elif isinstance(action, ViewerAction_ScrollEnd):
        if pointer is not None:
            tab = _set_pointer(tab, int(tab.line_count))
        if tab.scroll_y == _max_y(tab, page):
            tab = _tail_on(tab, page)
        else:
            tab = _tail_off(dataclasses.replace(tab, scroll_y=_max_y(tab, page)))
    elif isinstance(action, (ViewerAction_PageDown, ViewerAction_PageUp)):
        step = page if isinstance(action, ViewerAction_PageDown) else -page
        if pointer is None:
            tab = _set_y(tab, tab.scroll_y + step, page)
        else:
            tab = _center(_set_pointer(tab, pointer + step), page)
        tab = _tail_off(tab)
    elif isinstance(action, ViewerAction_Select):
        if pointer is None:
            tab = _set_pointer(tab, int(tab.scroll_y))
        else:
            tab = dataclasses.replace(tab, show_panel=not tab.show_panel)
    elif isinstance(action, ViewerAction_Dismiss):
        if tab.scan_running:
            requests.append(ViewerRequest_CancelScan(tab=active))
            _notify(notes, now, "", "Stopped scanning. Some lines may not be available.", Severity_Warning())
        elif tab.show_find:
            tab = _set_pointer(dataclasses.replace(tab, show_find=False), None)
            focus = Focus_Lines()
        elif tab.show_panel:
            tab = dataclasses.replace(tab, show_panel=False)
        else:
            tab = _set_pointer(tab, None)
    elif isinstance(action, ViewerAction_Navigate):
        start = pointer if pointer is not None else int(tab.scroll_y)
        requests.append(ViewerRequest_Navigate(tab=active, from_line=start, steps=action.steps, unit=action.unit))
    elif isinstance(action, ViewerAction_ToggleTail):
        if not tab.can_tail:
            _notify(notes, now, "Tail", "Can't tail merged files", Severity_Error())
        elif tab.tail:
            tab = _tail_off(tab)
        else:
            tab = _tail_on(tab, page)
    elif isinstance(action, ViewerAction_Tail):
        tab = _tail_on(tab, page)
    elif isinstance(action, ViewerAction_ToggleLineNumbers):
        tab = dataclasses.replace(tab, line_numbers=not tab.line_numbers)
    elif isinstance(action, ViewerAction_ShowFind):
        if not (tab.show_find and isinstance(focus, Focus_FindInput)):
            tab = dataclasses.replace(tab, show_find=True)
            focus = Focus_FindInput()
    elif isinstance(action, ViewerAction_DismissFind):
        tab = _set_pointer(dataclasses.replace(tab, show_find=False), None)
        focus = Focus_Lines()
    elif isinstance(action, ViewerAction_PointerDown):
        tab = _advance(tab, 1, page, active, requests)
    elif isinstance(action, ViewerAction_PointerUp):
        tab = _advance(tab, -1, page, active, requests)
    elif isinstance(action, ViewerAction_ToggleCase):
        tab = dataclasses.replace(tab, case_sensitive=not tab.case_sensitive)
    elif isinstance(action, ViewerAction_ToggleRegex):
        tab = dataclasses.replace(tab, regex=not tab.regex)
    else:
        panel = layout.panel
        if isinstance(panel, Some):
            panel_h = int(panel.value.height)
            panel_w = int(panel.value.width)
        else:
            panel_h = 0
            panel_w = 0
        content_h = _sat(panel_h - 2)
        max_rows = _sat(tab.panel_lines - content_h)
        max_cols = _sat(tab.panel_width - _sat(panel_w - 6))
        py = int(tab.panel_scroll_y)
        px = int(tab.panel_scroll_x)
        if isinstance(action, ViewerAction_PanelUp):
            py -= 1
        elif isinstance(action, ViewerAction_PanelDown):
            py += 1
        elif isinstance(action, ViewerAction_PanelLeft):
            px -= 1
        elif isinstance(action, ViewerAction_PanelRight):
            px += 1
        elif isinstance(action, ViewerAction_PanelPageUp):
            py -= content_h
        elif isinstance(action, ViewerAction_PanelPageDown):
            py += content_h
        elif isinstance(action, ViewerAction_PanelHome):
            py = 0
        else:
            py = max_rows
        tab = dataclasses.replace(tab, panel_scroll_x=_clamp(px, max_cols), panel_scroll_y=_clamp(py, max_rows))

    if not tab.show_panel and isinstance(focus, Focus_Panel):
        focus = Focus_Lines()
    tabs[int(viewer.active)] = tab
    result = dataclasses.replace(viewer, tabs=CottList(values=tabs), active=active, focus=focus, modal=modal, notifications=CottList(values=notes))
    return ViewerUpdate(viewer=result, requests=CottList(values=requests))
