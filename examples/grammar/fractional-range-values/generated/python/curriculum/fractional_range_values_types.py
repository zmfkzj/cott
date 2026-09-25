from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
MAX_F64: Final[F64] = 179769313486231570000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PositiveStep:
    value: F64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, F64, path="$.value"))
        if not (_cott_contract_condition(((self.value > 0)), "curriculum.fractional_range_values.PositiveStep", "refinement")):
            raise CottContractViolation("PositiveStep refinement failed", symbol="curriculum.fractional_range_values.PositiveStep", phase="refinement", span={"end_byte":134,"end_column":21,"end_line":6,"start_byte":124,"start_column":11,"start_line":6}, expected="true", actual="false")

    __hash__ = None
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputLimit:
    value: U64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, U64, path="$.value"))
        if not (_cott_contract_condition(((1 <= self.value <= 10000)), "curriculum.fractional_range_values.OutputLimit", "refinement")):
            raise CottContractViolation("OutputLimit refinement failed", symbol="curriculum.fractional_range_values.OutputLimit", phase="refinement", span={"end_byte":189,"end_column":29,"end_line":9,"start_byte":171,"start_column":11,"start_line":9}, expected="true", actual="false")

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
__all__ = ["FractionalRangeError", "FractionalRangeError_NonFiniteInput", "FractionalRangeError_OutputLimitExceeded", "FractionalRangeError_StepDoesNotAdvance", "MAX_F64", "OutputLimit", "PositiveStep"]
