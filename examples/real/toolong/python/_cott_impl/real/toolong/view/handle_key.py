import dataclasses
from typing import Final

from cott_runtime import CottList, Nothing, Some
from real.toolong.keys import edit_input
from real.toolong.view import apply_action, viewer_layout
from real.toolong.keys_types import KeyEvent, TextInput
from real.toolong.model_types import TimeUnit_Day, TimeUnit_Hour, TimeUnit_Minute
from real.toolong.view_types import Focus_FindCase, Focus_FindInput, Focus_FindRegex, Focus_Lines, Focus_Panel, Focus_Tabs, Modal_Goto, Modal_Help, TabView, ViewerAction, ViewerAction_CloseGoto, ViewerAction_CloseHelp, ViewerAction_Dismiss, ViewerAction_DismissFind, ViewerAction_FocusNext, ViewerAction_FocusPrevious, ViewerAction_Goto, ViewerAction_Help, ViewerAction_HelpDown, ViewerAction_HelpEnd, ViewerAction_HelpHome, ViewerAction_HelpPageDown, ViewerAction_HelpPageUp, ViewerAction_HelpUp, ViewerAction_Navigate, ViewerAction_NextTab, ViewerAction_OpenLink, ViewerAction_PageDown, ViewerAction_PageUp, ViewerAction_PanelDown, ViewerAction_PanelEnd, ViewerAction_PanelHome, ViewerAction_PanelLeft, ViewerAction_PanelPageDown, ViewerAction_PanelPageUp, ViewerAction_PanelRight, ViewerAction_PanelUp, ViewerAction_PointerDown, ViewerAction_PointerUp, ViewerAction_PreviousTab, ViewerAction_Quit, ViewerAction_ScrollDown, ViewerAction_ScrollEnd, ViewerAction_ScrollHome, ViewerAction_ScrollLeft, ViewerAction_ScrollRight, ViewerAction_ScrollUp, ViewerAction_Select, ViewerAction_ShowFind, ViewerAction_ToggleCase, ViewerAction_ToggleLineNumbers, ViewerAction_ToggleRegex, ViewerAction_ToggleTail, ViewerRequest, ViewerRequest_Bell, ViewerRequest_Suggest, ViewerState, ViewerUpdate

_URL_AUTHOR: Final[str] = "https://www.willmcgugan.com"
_URL_TEXTUAL: Final[str] = "https://www.textualize.io/"
_URL_REPOSITORY: Final[str] = "https://github.com/Textualize/toolong"
_URL_LOGMERGER: Final[str] = "https://github.com/ptmcg/logmerger"


def _unchanged(viewer: ViewerState) -> ViewerUpdate:
    return ViewerUpdate(viewer=viewer, requests=CottList(values=[]))


def _replace_tab(viewer: ViewerState, tab: TabView) -> ViewerState:
    tabs: list[TabView] = []
    for index, existing in enumerate(viewer.tabs):
        tabs.append(tab if index == viewer.active else existing)
    return dataclasses.replace(viewer, tabs=CottList(values=tabs))


def _active_tab(viewer: ViewerState) -> TabView | None:
    for index, tab in enumerate(viewer.tabs):
        if index == viewer.active:
            return tab
    return None


def _with_pointer(tab: TabView, pointer: int | None) -> TabView:
    old = tab.pointer
    if isinstance(old, Some):
        old_value: int | None = old.value
    else:
        old_value = None
    if pointer is None:
        new_tab = dataclasses.replace(tab, pointer=Nothing(), show_panel=False)
    else:
        new_tab = dataclasses.replace(tab, pointer=Some(value=pointer))
    if old_value != pointer:
        new_tab = dataclasses.replace(new_tab, panel_scroll_x=0, panel_scroll_y=0)
    return new_tab


def _goto_line(viewer: ViewerState, value: str) -> ViewerState:
    tab = _active_tab(viewer)
    if tab is None:
        return viewer
    try:
        number = int(value)
    except ValueError:
        return _replace_tab(viewer, _with_pointer(tab, None))
    if tab.line_count == 0:
        return _replace_tab(viewer, _with_pointer(tab, None))
    pointer = min(max(number - 1, 0), tab.line_count - 1)
    tab = _with_pointer(tab, pointer)
    page = viewer_layout(viewer).text.height
    max_scroll = max(0, tab.line_count - page)
    scroll = min(max(pointer - page // 2, 0), max_scroll)
    return _replace_tab(viewer, dataclasses.replace(tab, scroll_y=scroll))


def _help_action(name: str) -> ViewerAction | None:
    if name == "escape":
        return ViewerAction_CloseHelp()
    if name == "a":
        return ViewerAction_OpenLink(url=_URL_AUTHOR)
    if name == "t":
        return ViewerAction_OpenLink(url=_URL_TEXTUAL)
    if name == "r":
        return ViewerAction_OpenLink(url=_URL_REPOSITORY)
    if name == "l":
        return ViewerAction_OpenLink(url=_URL_LOGMERGER)
    if name == "up":
        return ViewerAction_HelpUp()
    if name == "down":
        return ViewerAction_HelpDown()
    if name == "pageup":
        return ViewerAction_HelpPageUp()
    if name == "pagedown":
        return ViewerAction_HelpPageDown()
    if name == "home":
        return ViewerAction_HelpHome()
    if name == "end":
        return ViewerAction_HelpEnd()
    return None


def _lines_action(name: str) -> ViewerAction | None:
    if name == "escape":
        return ViewerAction_Dismiss()
    if name in ("up", "k"):
        return ViewerAction_ScrollUp()
    if name in ("down", "j"):
        return ViewerAction_ScrollDown()
    if name == "left":
        return ViewerAction_ScrollLeft()
    if name == "right":
        return ViewerAction_ScrollRight()
    if name == "home":
        return ViewerAction_ScrollHome()
    if name == "end":
        return ViewerAction_ScrollEnd()
    if name == "pageup":
        return ViewerAction_PageUp()
    if name == "pagedown":
        return ViewerAction_PageDown()
    if name == "enter":
        return ViewerAction_Select()
    if name == "m":
        return ViewerAction_Navigate(steps=1, unit=TimeUnit_Minute())
    if name == "M":
        return ViewerAction_Navigate(steps=-1, unit=TimeUnit_Minute())
    if name == "h":
        return ViewerAction_Navigate(steps=1, unit=TimeUnit_Hour())
    if name == "H":
        return ViewerAction_Navigate(steps=-1, unit=TimeUnit_Hour())
    if name == "d":
        return ViewerAction_Navigate(steps=1, unit=TimeUnit_Day())
    if name == "D":
        return ViewerAction_Navigate(steps=-1, unit=TimeUnit_Day())
    return None


def _panel_action(name: str) -> ViewerAction | None:
    if name == "up":
        return ViewerAction_PanelUp()
    if name == "down":
        return ViewerAction_PanelDown()
    if name == "left":
        return ViewerAction_PanelLeft()
    if name == "right":
        return ViewerAction_PanelRight()
    if name == "home":
        return ViewerAction_PanelHome()
    if name == "end":
        return ViewerAction_PanelEnd()
    if name == "pageup":
        return ViewerAction_PanelPageUp()
    if name == "pagedown":
        return ViewerAction_PanelPageDown()
    return None


def _common_action(viewer: ViewerState, name: str) -> ViewerAction | None:
    focus = viewer.focus
    if isinstance(focus, Focus_Lines):
        found = _lines_action(name)
        if found is not None:
            return found
    elif isinstance(focus, Focus_Panel):
        found = _panel_action(name)
        if found is not None:
            return found
    elif isinstance(focus, Focus_Tabs):
        if name == "left":
            return ViewerAction_PreviousTab()
        if name == "right":
            return ViewerAction_NextTab()
    elif isinstance(focus, Focus_FindCase):
        if name in ("enter", "space"):
            return ViewerAction_ToggleCase()
    elif isinstance(focus, Focus_FindRegex):
        if name in ("enter", "space"):
            return ViewerAction_ToggleRegex()
    if isinstance(focus, (Focus_FindInput, Focus_FindCase, Focus_FindRegex)):
        if name == "escape":
            return ViewerAction_DismissFind()
        if name in ("down", "j"):
            return ViewerAction_PointerDown()
        if name in ("up", "k"):
            return ViewerAction_PointerUp()
    if not isinstance(focus, Focus_Tabs):
        if name == "ctrl+t":
            return ViewerAction_ToggleTail()
        if name == "ctrl+l":
            return ViewerAction_ToggleLineNumbers()
        if name in ("ctrl+f", "slash"):
            return ViewerAction_ShowFind()
        if name == "ctrl+g":
            return ViewerAction_Goto()
    if name == "f1":
        return ViewerAction_Help()
    if name == "tab":
        return ViewerAction_FocusNext()
    if name == "shift+tab":
        return ViewerAction_FocusPrevious()
    return None


def _find_input_key(viewer: ViewerState, key: KeyEvent) -> ViewerUpdate | None:
    tab = _active_tab(viewer)
    if tab is None:
        return None
    edit = edit_input(tab.find_input, key, viewer.suggestion, False)
    if not edit.handled:
        return None
    requests: list[ViewerRequest] = []
    if edit.bell:
        requests.append(ViewerRequest_Bell())
    tab = dataclasses.replace(tab, find_input=edit.input)
    state = viewer
    if edit.changed:
        state = dataclasses.replace(state, suggestion="")
        value = edit.input.value
        if value == "":
            tab = _with_pointer(tab, None)
        else:
            requests.append(ViewerRequest_Suggest(tab=viewer.active, value=value))
    if edit.submitted:
        tab = dataclasses.replace(tab, show_panel=not tab.show_panel)
    return ViewerUpdate(viewer=_replace_tab(state, tab), requests=CottList(values=requests))


def _goto_key(viewer: ViewerState, current: TextInput, key: KeyEvent) -> ViewerUpdate:
    edit = edit_input(current, key, "", True)
    if edit.handled:
        requests: list[ViewerRequest] = []
        if edit.bell:
            requests.append(ViewerRequest_Bell())
        state = dataclasses.replace(viewer, modal=Modal_Goto(input=edit.input))
        if edit.changed:
            state = _goto_line(state, edit.input.value)
        return ViewerUpdate(viewer=state, requests=CottList(values=requests))
    if key.key == "escape":
        return apply_action(viewer, ViewerAction_CloseGoto())
    return _unchanged(viewer)


def handle_key(viewer: ViewerState, key: KeyEvent) -> ViewerUpdate:
    name = key.key
    if name == "ctrl+c":
        return apply_action(viewer, ViewerAction_Quit())
    modal = viewer.modal
    if isinstance(modal, Modal_Help):
        action = _help_action(name)
        if action is None:
            return _unchanged(viewer)
        return apply_action(viewer, action)
    if isinstance(modal, Modal_Goto):
        return _goto_key(viewer, modal.input, key)
    if isinstance(viewer.focus, Focus_FindInput):
        update = _find_input_key(viewer, key)
        if update is not None:
            return update
    action = _common_action(viewer, name)
    if action is None:
        return _unchanged(viewer)
    return apply_action(viewer, action)
