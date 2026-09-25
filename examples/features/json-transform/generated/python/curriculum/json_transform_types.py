from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonChain_End:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonChain_Link:
    __hash__ = None
    value: str
    next: Option[JsonChain]

JsonChain: TypeAlias = Union[JsonChain_End, JsonChain_Link]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonTransformError_NotAnObject:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonTransformError_MissingField:
    __hash__ = None
    field_name: str

JsonTransformError: TypeAlias = Union[JsonTransformError_NotAnObject, JsonTransformError_MissingField]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StringField:
    __hash__ = None
    name: str
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

"""Wrap one string member into a JSON object."""
"""Read the top-level member of a JSON object whose key equals `field` exactly
(no case folding, normalization or nested lookup). A payload that is not a
JSON object fails with `NotAnObject`, checked first. An object without that
member, or whose member is not a JSON string, fails with
`MissingField(field_name: field)`. Otherwise the result's `name` is `field`
and its `text` is the member's string value. Contract clauses cannot inspect
`JsonValue` structure, so both failures are declared without conditions."""
__all__ = ["JsonChain", "JsonChain_End", "JsonChain_Link", "JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject", "StringField"]
