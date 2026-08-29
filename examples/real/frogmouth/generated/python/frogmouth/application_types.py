from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarMode_Hidden:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarMode_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarMode_History:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarMode_Bookmarks:
    pass

SidebarMode: TypeAlias = Union[SidebarMode_Hidden, SidebarMode_Help, SidebarMode_History, SidebarMode_Bookmarks]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarDock_Left:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarDock_Right:
    pass

SidebarDock: TypeAlias = Union[SidebarDock_Left, SidebarDock_Right]

"""Parse an optional initial location argument."""
"""Resolve the application state storage path."""
SIDEBAR_HIDDEN: Final[SidebarMode] = SidebarMode_Hidden()

SIDEBAR_HELP: Final[SidebarMode] = SidebarMode_Help()

SIDEBAR_HISTORY: Final[SidebarMode] = SidebarMode_History()

SIDEBAR_DOCK_LEFT: Final[SidebarDock] = SidebarDock_Left()

SIDEBAR_DOCK_RIGHT: Final[SidebarDock] = SidebarDock_Right()

__all__ = ["SIDEBAR_DOCK_LEFT", "SIDEBAR_DOCK_RIGHT", "SIDEBAR_HELP", "SIDEBAR_HIDDEN", "SIDEBAR_HISTORY", "SidebarDock", "SidebarDock_Left", "SidebarDock_Right", "SidebarMode", "SidebarMode_Bookmarks", "SidebarMode_Help", "SidebarMode_Hidden", "SidebarMode_History"]
