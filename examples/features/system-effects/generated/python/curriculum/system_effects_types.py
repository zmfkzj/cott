from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SystemError_PathNotFound:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SystemError_AccessDenied:
    __hash__ = None
    reason: str

SystemError: TypeAlias = Union[SystemError_PathNotFound, SystemError_AccessDenied]

"""Validate and inspect a system file path target."""
"""Format an environment variable value or use the fallback string."""
__all__ = ["SystemError", "SystemError_AccessDenied", "SystemError_PathNotFound"]
