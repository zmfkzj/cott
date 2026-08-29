from math import isfinite

from cott_runtime import CottList, Err, F64, Ok, Result
from curriculum.fractional_range_values_types import (
    FractionalRangeError,
    FractionalRangeError_NonFiniteInput,
    FractionalRangeError_OutputLimitExceeded,
    FractionalRangeError_StepDoesNotAdvance,
    OutputLimit,
    PositiveStep,
)


def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]:
    step_value = step.value
    if not (isfinite(start) and isfinite(stop) and isfinite(step_value)):
        return Err(error=FractionalRangeError_NonFiniteInput())

    values: list[F64] = []
    index = 0
    previous = start
    while True:
        candidate = start + index * step_value
        if candidate >= stop:
            return Ok(value=CottList(values=values))
        if index == limit.value:
            return Err(error=FractionalRangeError_OutputLimitExceeded())
        if index != 0 and candidate <= previous:
            return Err(error=FractionalRangeError_StepDoesNotAdvance())
        values.append(candidate)
        previous = candidate
        index += 1
