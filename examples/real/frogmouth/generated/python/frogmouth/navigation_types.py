from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.model_types import Location, LocationKind, LocationKind_Http, LocationKind_Local

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationError_EmptyInput:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationError_UnsupportedScheme:
    __hash__ = None
    scheme: str

NavigationError: TypeAlias = Union[NavigationError_EmptyInput, NavigationError_UnsupportedScheme]

"""Classify address-bar input exactly as typed; it is not trimmed. A value
starting with "http://" or "https://" is an Http location whose target is the
value. Any other value containing "://" is UnsupportedScheme whose scheme is
the text before the first "://". Every other non-empty value is a Local
location: a value starting with "/" is the target unchanged; otherwise the
target is the text of working_directory, one "/" (omitted when that text
already ends with "/") and the value. Local targets are not normalized,
"~"-expanded or checked for existence. The browser passes the process's
absolute working directory."""
"""Address-bar text for a loaded location; reload passes it back to
frogmouth.navigation.resolve_location."""
__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_UnsupportedScheme"]
