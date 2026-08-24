from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.clip_ranges_types import ClipPlan as ClipPlan, ClipRangeError as ClipRangeError, ClipRangeError_EmptyRanges as ClipRangeError_EmptyRanges, ClipRangeError_PastDuration as ClipRangeError_PastDuration, ClipRangeError_StartNotBeforeEnd as ClipRangeError_StartNotBeforeEnd, ClipRangeError_TotalOverflow as ClipRangeError_TotalOverflow, ClipRequest as ClipRequest, TimeRange as TimeRange
"""Return the duration of one validated half-open time range in milliseconds.
The caller must establish that the range starts before it ends."""
def range_duration_ms(range: TimeRange) -> U64: ...

"""Validate requested intervals in input order and build a clip plan.
Empty input is rejected first. Each range must start before it ends and
must not extend past the source duration. Valid ranges remain unchanged
and their durations are accumulated with checked U64 arithmetic."""
def plan_clip_ranges(request: ClipRequest) -> Result[ClipPlan, ClipRangeError]: ...

__all__ = ["ClipPlan", "ClipRangeError", "ClipRangeError_EmptyRanges", "ClipRangeError_PastDuration", "ClipRangeError_StartNotBeforeEnd", "ClipRangeError_TotalOverflow", "ClipRequest", "TimeRange", "plan_clip_ranges", "range_duration_ms"]
