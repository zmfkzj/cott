from frogmouth.layout_types import EscapeAction, EscapeAction_ClearAddress, EscapeAction_FocusAddress, EscapeAction_HideSidebarAndFocusAddress, EscapeAction_Quit, Focus, Focus_AddressBar, Focus_Sidebar


def escape_action(focus: Focus, address: str) -> EscapeAction:
    if isinstance(focus, Focus_AddressBar):
        if address != "":
            return EscapeAction_ClearAddress()
        return EscapeAction_Quit()
    if isinstance(focus, Focus_Sidebar):
        return EscapeAction_HideSidebarAndFocusAddress()
    return EscapeAction_FocusAddress()
