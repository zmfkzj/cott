from cott_runtime import CottList
from real.toolong.view_types import Focus_FindCase, Focus_FindInput, Focus_FindRegex, Focus_Tabs, FooterKey, Modal_Help, ViewerAction_Goto, ViewerAction_Help, ViewerAction_OpenLink, ViewerAction_PointerDown, ViewerAction_PointerUp, ViewerAction_ShowFind, ViewerAction_ToggleLineNumbers, ViewerAction_ToggleTail, ViewerState


def footer_keys(viewer: ViewerState) -> CottList[FooterKey]:
    if isinstance(viewer.modal, Modal_Help):
        return CottList(values=[
            FooterKey(key="a", display="A", description="Author", action=ViewerAction_OpenLink(url="https://www.willmcgugan.com")),
            FooterKey(key="t", display="T", description="Textual", action=ViewerAction_OpenLink(url="https://www.textualize.io/")),
            FooterKey(key="r", display="R", description="Repository", action=ViewerAction_OpenLink(url="https://github.com/Textualize/toolong")),
            FooterKey(key="l", display="L", description="Logmerger", action=ViewerAction_OpenLink(url="https://github.com/ptmcg/logmerger")),
        ])
    keys: list[FooterKey] = [FooterKey(key="f1", display="f1", description="Help", action=ViewerAction_Help())]
    focus = viewer.focus
    if not isinstance(focus, Focus_Tabs):
        index = int(viewer.active)
        can_tail = False
        position = 0
        for tab in viewer.tabs:
            if position == index:
                can_tail = tab.can_tail
            position += 1
        if can_tail:
            keys.append(FooterKey(key="ctrl+t", display="^t", description="Tail", action=ViewerAction_ToggleTail()))
        keys.append(FooterKey(key="ctrl+l", display="^l", description="Line nos.", action=ViewerAction_ToggleLineNumbers()))
        if not isinstance(focus, Focus_FindInput):
            keys.append(FooterKey(key="ctrl+f", display="^f", description="Find", action=ViewerAction_ShowFind()))
        keys.append(FooterKey(key="ctrl+g", display="^g", description="Go to", action=ViewerAction_Goto()))
    if isinstance(focus, (Focus_FindInput, Focus_FindCase, Focus_FindRegex)):
        keys.append(FooterKey(key="down", display="↓", description="Next", action=ViewerAction_PointerDown()))
        keys.append(FooterKey(key="up", display="↑", description="Previous", action=ViewerAction_PointerUp()))
    return CottList(values=keys)
