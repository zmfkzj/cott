from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TimeRange:
    __hash__ = None
    start_ms: U64
    end_ms: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClipRequest:
    __hash__ = None
    duration_ms: U64
    ranges: CottList[TimeRange]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClipPlan:
    __hash__ = None
    ranges: CottList[TimeRange]
    total_ms: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClipRangeError_EmptyRanges:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClipRangeError_StartNotBeforeEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClipRangeError_PastDuration:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClipRangeError_TotalOverflow:
    pass

ClipRangeError: TypeAlias = Union[ClipRangeError_EmptyRanges, ClipRangeError_StartNotBeforeEnd, ClipRangeError_PastDuration, ClipRangeError_TotalOverflow]

"""Return the duration of one validated half-open time range in milliseconds.
The caller must establish that the range starts before it ends."""
"""Validate requested intervals in input order and build a clip plan.
Empty input is rejected first. Each range must start before it ends and
must not extend past the source duration. Valid ranges remain unchanged
and their durations are accumulated with checked U64 arithmetic."""
__all__ = ["ClipPlan", "ClipRangeError", "ClipRangeError_EmptyRanges", "ClipRangeError_PastDuration", "ClipRangeError_StartNotBeforeEnd", "ClipRangeError_TotalOverflow", "ClipRequest", "TimeRange"]
