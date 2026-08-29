from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.application_types import SIDEBAR_DOCK_LEFT as SIDEBAR_DOCK_LEFT, SIDEBAR_DOCK_RIGHT as SIDEBAR_DOCK_RIGHT, SIDEBAR_HELP as SIDEBAR_HELP, SIDEBAR_HIDDEN as SIDEBAR_HIDDEN, SIDEBAR_HISTORY as SIDEBAR_HISTORY, SidebarDock as SidebarDock, SidebarDock_Left as SidebarDock_Left, SidebarDock_Right as SidebarDock_Right, SidebarMode as SidebarMode, SidebarMode_Bookmarks as SidebarMode_Bookmarks, SidebarMode_Help as SidebarMode_Help, SidebarMode_Hidden as SidebarMode_Hidden, SidebarMode_History as SidebarMode_History
def toggle_sidebar(current: SidebarMode, requested: SidebarMode) -> SidebarMode: ...

def toggle_sidebar_dock(current: SidebarDock) -> SidebarDock: ...

"""Parse an optional initial location argument."""
def parse_initial_location(arguments: CottList[str]) -> Option[str]: ...

"""Resolve the application state storage path."""
def resolve_state_path(platform_name: str, home: Path, app_data: Option[str], xdg_data_home: Option[str]) -> Path: ...

__all__ = ["SIDEBAR_DOCK_LEFT", "SIDEBAR_DOCK_RIGHT", "SIDEBAR_HELP", "SIDEBAR_HIDDEN", "SIDEBAR_HISTORY", "SidebarDock", "SidebarDock_Left", "SidebarDock_Right", "SidebarMode", "SidebarMode_Bookmarks", "SidebarMode_Help", "SidebarMode_Hidden", "SidebarMode_History", "parse_initial_location", "resolve_state_path", "toggle_sidebar", "toggle_sidebar_dock"]
