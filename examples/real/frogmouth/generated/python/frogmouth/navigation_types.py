from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from frogmouth.model_types import Location

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

"""Return LocationKind.Http for HTTP(S); otherwise return an absolute LocationKind.Local path."""
__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_UnsupportedScheme"]
