from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.layout_types import CycleDirection as CycleDirection, CycleDirection_Next as CycleDirection_Next, CycleDirection_Previous as CycleDirection_Previous, EscapeAction as EscapeAction, EscapeAction_ClearAddress as EscapeAction_ClearAddress, EscapeAction_FocusAddress as EscapeAction_FocusAddress, EscapeAction_HideSidebarAndFocusAddress as EscapeAction_HideSidebarAndFocusAddress, EscapeAction_Quit as EscapeAction_Quit, Focus as Focus, Focus_AddressBar as Focus_AddressBar, Focus_Document as Focus_Document, Focus_Sidebar as Focus_Sidebar, Pane as Pane, Pane_Bookmarks as Pane_Bookmarks, Pane_Contents as Pane_Contents, Pane_History as Pane_History, Pane_Local as Pane_Local, Sidebar as Sidebar, Visibility as Visibility, Visibility_Hidden as Visibility_Hidden, Visibility_Shown as Visibility_Shown
"""The pane shortcuts (Ctrl+T, Ctrl+L, Ctrl+B, Ctrl+Y and the contents,
local, bookmarks and history commands) toggle: requesting the pane that
is already shown hides the sidebar, any other request shows the sidebar
with pane active."""
def toggle_pane(sidebar: Sidebar, pane: Pane) -> Sidebar: ...

"""Show or hide the sidebar (Ctrl+N), keeping the active pane."""
def toggle_sidebar(sidebar: Sidebar) -> Sidebar: ...

"""Activate the neighbouring pane in tab order, wrapping around at both
ends: Next after History is Contents and Previous before Contents is
History. Visibility is unchanged."""
def cycle_pane(sidebar: Sidebar, direction: CycleDirection) -> Sidebar: ...

"""Escape backs out of the application step by step: from the document it
focuses the address bar, from the sidebar it also hides the sidebar, in
the address bar it clears non-empty text and otherwise quits."""
def escape_action(focus: Focus, address: str) -> EscapeAction: ...

__all__ = ["CycleDirection", "CycleDirection_Next", "CycleDirection_Previous", "EscapeAction", "EscapeAction_ClearAddress", "EscapeAction_FocusAddress", "EscapeAction_HideSidebarAndFocusAddress", "EscapeAction_Quit", "Focus", "Focus_AddressBar", "Focus_Document", "Focus_Sidebar", "Pane", "Pane_Bookmarks", "Pane_Contents", "Pane_History", "Pane_Local", "Sidebar", "Visibility", "Visibility_Hidden", "Visibility_Shown", "cycle_pane", "escape_action", "toggle_pane", "toggle_sidebar"]
