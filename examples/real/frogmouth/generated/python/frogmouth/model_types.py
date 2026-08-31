from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Local:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Http:
    pass

LocationKind: TypeAlias = Union[LocationKind_Local, LocationKind_Http]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Location:
    __hash__ = None
    kind: LocationKind
    target: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, LocationKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "target", _cott_validate_abi(self.target, str, path="$.target"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Document:
    __hash__ = None
    location: Location
    title: str
    markdown: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "location", _cott_validate_abi(self.location, Location, path="$.location"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "markdown", _cott_validate_abi(self.markdown, str, path="$.markdown"))

__all__ = ["Document", "Location", "LocationKind", "LocationKind_Http", "LocationKind_Local"]
