from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.fractional_range_values_types import FractionalRangeError as FractionalRangeError, FractionalRangeError_NonFiniteInput as FractionalRangeError_NonFiniteInput, FractionalRangeError_OutputLimitExceeded as FractionalRangeError_OutputLimitExceeded, FractionalRangeError_StepDoesNotAdvance as FractionalRangeError_StepDoesNotAdvance, OutputLimit as OutputLimit, PositiveStep as PositiveStep
"""Constructs an ascending finite sequence of binary64 values. The start is
included when start is less than stop; stop is always excluded. If start is
greater than or equal to stop, the result is an empty list.

The function first rejects a non-finite start, stop, or step with
NonFiniteInput. Each candidate is computed directly as start plus index
times step, with binary64 round-to-nearest, ties-to-even after the
multiplication and addition. A candidate equal to or above stop ends the
sequence. A candidate that does not exceed the preceding rounded value
produces StepDoesNotAdvance. After limit values, the next candidate is
checked only for termination; if it is still below stop,
OutputLimitExceeded takes precedence."""
def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]: ...

__all__ = ["FractionalRangeError", "FractionalRangeError_NonFiniteInput", "FractionalRangeError_OutputLimitExceeded", "FractionalRangeError_StepDoesNotAdvance", "OutputLimit", "PositiveStep", "build_bounded_range"]
