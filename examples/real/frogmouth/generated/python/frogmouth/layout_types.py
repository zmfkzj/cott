from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""The navigation sidebar's panes, in tab order."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_Contents:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_Local:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_Bookmarks:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_History:
    pass

Pane: TypeAlias = Union[Pane_Contents, Pane_Local, Pane_Bookmarks, Pane_History]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Visibility_Shown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Visibility_Hidden:
    pass

Visibility: TypeAlias = Union[Visibility_Shown, Visibility_Hidden]

"""Whether the navigation sidebar is shown and which of its panes is active;
the active pane is remembered while the sidebar is hidden."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Sidebar:
    __hash__ = None
    visibility: Visibility
    active: Pane

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "visibility", _cott_validate_abi(self.visibility, Visibility, path="$.visibility"))
        if not _cott_validated_construction():
            object.__setattr__(self, "active", _cott_validate_abi(self.active, Pane, path="$.active"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CycleDirection_Previous:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CycleDirection_Next:
    pass

CycleDirection: TypeAlias = Union[CycleDirection_Previous, CycleDirection_Next]

"""Where keyboard focus is when Escape is pressed."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_AddressBar:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_Sidebar:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_Document:
    pass

Focus: TypeAlias = Union[Focus_AddressBar, Focus_Sidebar, Focus_Document]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EscapeAction_ClearAddress:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EscapeAction_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EscapeAction_FocusAddress:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EscapeAction_HideSidebarAndFocusAddress:
    pass

EscapeAction: TypeAlias = Union[EscapeAction_ClearAddress, EscapeAction_Quit, EscapeAction_FocusAddress, EscapeAction_HideSidebarAndFocusAddress]

"""The pane shortcuts (Ctrl+T, Ctrl+L, Ctrl+B, Ctrl+Y and the contents,
local, bookmarks and history commands) toggle: requesting the pane that
is already shown hides the sidebar, any other request shows the sidebar
with pane active."""
"""Show or hide the sidebar (Ctrl+N), keeping the active pane."""
"""Activate the neighbouring pane in tab order, wrapping around at both
ends: Next after History is Contents and Previous before Contents is
History. Visibility is unchanged."""
"""Escape backs out of the application step by step: from the document it
focuses the address bar, from the sidebar it also hides the sidebar, in
the address bar it clears non-empty text and otherwise quits."""
__all__ = ["CycleDirection", "CycleDirection_Next", "CycleDirection_Previous", "EscapeAction", "EscapeAction_ClearAddress", "EscapeAction_FocusAddress", "EscapeAction_HideSidebarAndFocusAddress", "EscapeAction_Quit", "Focus", "Focus_AddressBar", "Focus_Document", "Focus_Sidebar", "Pane", "Pane_Bookmarks", "Pane_Contents", "Pane_History", "Pane_Local", "Sidebar", "Visibility", "Visibility_Hidden", "Visibility_Shown"]
