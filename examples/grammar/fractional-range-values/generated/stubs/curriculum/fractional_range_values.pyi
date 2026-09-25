from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.fractional_range_values_types import FractionalRangeError as FractionalRangeError, FractionalRangeError_NonFiniteInput as FractionalRangeError_NonFiniteInput, FractionalRangeError_OutputLimitExceeded as FractionalRangeError_OutputLimitExceeded, FractionalRangeError_StepDoesNotAdvance as FractionalRangeError_StepDoesNotAdvance, MAX_F64 as MAX_F64, OutputLimit as OutputLimit, PositiveStep as PositiveStep
"""Returns, in ascending order, the candidates start + index * step for
index = 0, 1, 2, ... that lie below stop. Each candidate is computed from
its own index: the index is converted to binary64, multiplied by step, and
start is added, each operation rounded to nearest, ties to even, with no
fused multiply-add and no running sum. The first candidate at or above stop
ends the sequence and is excluded, so the result is empty when start is at
or above stop.

A candidate below stop that does not exceed the preceding value returns
StepDoesNotAdvance. At most limit values are returned: when the candidate
after the limit-th value is still below stop, OutputLimitExceeded is
returned, even if that candidate also fails to advance."""
def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]: ...

__all__ = ["FractionalRangeError", "FractionalRangeError_NonFiniteInput", "FractionalRangeError_OutputLimitExceeded", "FractionalRangeError_StepDoesNotAdvance", "MAX_F64", "OutputLimit", "PositiveStep", "build_bounded_range"]
