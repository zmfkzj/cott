from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Assignment:
    __hash__ = None
    name: str
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ParseAssignmentError_MissingEquals:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ParseAssignmentError_EmptyName:
    pass

ParseAssignmentError: TypeAlias = Union[ParseAssignmentError_MissingEquals, ParseAssignmentError_EmptyName]

"""Base rule for assignments requiring non-empty name."""
class BaseAssignmentRule:
    pass

"""Strict rule inheriting from BaseAssignmentRule with overridden name constraint, deleted error, and added non-empty value constraint."""
class StrictAssignmentRule(BaseAssignmentRule):
    pass

"""Parses one assignment without I/O or mutation following strict rules."""
__all__ = ["Assignment", "BaseAssignmentRule", "ParseAssignmentError", "ParseAssignmentError_EmptyName", "ParseAssignmentError_MissingEquals", "StrictAssignmentRule"]
