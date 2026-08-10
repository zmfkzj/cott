from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PositiveStep:
    value: F64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, F64, path="$.value"))
        if not ((self.value > 0)):
            raise CottContractViolation("PositiveStep refinement failed", symbol="curriculum.fractional_range_values.PositiveStep", phase="refinement", span={"end_byte":89,"end_column":21,"end_line":4,"start_byte":79,"start_column":11,"start_line":4}, expected="true", actual="false")

    __hash__ = None
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputLimit:
    value: U32

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, U32, path="$.value"))
        if not ((1 <= self.value <= 10000)):
            raise CottContractViolation("OutputLimit refinement failed", symbol="curriculum.fractional_range_values.OutputLimit", phase="refinement", span={"end_byte":144,"end_column":29,"end_line":7,"start_byte":126,"start_column":11,"start_line":7}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FractionalRangeError_NonFiniteInput:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FractionalRangeError_StepDoesNotAdvance:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FractionalRangeError_OutputLimitExceeded:
    pass

FractionalRangeError: TypeAlias = Union[FractionalRangeError_NonFiniteInput, FractionalRangeError_StepDoesNotAdvance, FractionalRangeError_OutputLimitExceeded]

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
__all__ = ["FractionalRangeError", "FractionalRangeError_NonFiniteInput", "FractionalRangeError_OutputLimitExceeded", "FractionalRangeError_StepDoesNotAdvance", "OutputLimit", "PositiveStep"]
