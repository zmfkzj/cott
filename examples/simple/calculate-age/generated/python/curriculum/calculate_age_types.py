from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AgeSummary:
    __hash__ = None
    name: str
    years: I64
    months: I64
    days: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AgeError_NegativeAge:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AgeError_InvalidDate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AgeError_Overflow:
    pass

AgeError: TypeAlias = Union[AgeError_NegativeAge, AgeError_InvalidDate, AgeError_Overflow]

"""Calculate the elapsed Gregorian days for an age in whole years ending on the supplied date.

A February 29 anniversary falls on February 28 in a non-leap start year. Validation returns NegativeAge before InvalidDate, and InvalidDate before Overflow."""
"""Build an age summary from the Gregorian day count calculated by calculate_age_days.

On success, name is unchanged, years is age_years, months is age_years * 12, and days is the helper result. Helper errors are propagated unchanged."""
__all__ = ["AgeError", "AgeError_InvalidDate", "AgeError_NegativeAge", "AgeError_Overflow", "AgeSummary"]
