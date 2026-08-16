from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
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

"""Wrap a string key-value pair into a structured JsonValue object."""
"""Extract a string field value from a JSON object payload."""
__all__ = ["JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject"]
