from math import isfinite
from cott_runtime import CottList, F64, Ok, Err, Result
from curriculum.fractional_range_values_types import FractionalRangeError, FractionalRangeError_NonFiniteInput, FractionalRangeError_OutputLimitExceeded, FractionalRangeError_StepDoesNotAdvance, OutputLimit, PositiveStep


def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]:
    step_value: float = step.value
    if not isfinite(start) or not isfinite(stop) or not isfinite(step_value):
        return Err(error=FractionalRangeError_NonFiniteInput())
    if start >= stop:
        return Ok(value=CottList(values=[]))

    values: list[float] = []
    previous: float = start
    index: int = 0
    while index < limit.value:
        candidate: float = start + index * step_value
        if candidate >= stop:
            return Ok(value=CottList(values=values))
        if index > 0 and candidate <= previous:
            return Err(error=FractionalRangeError_StepDoesNotAdvance())
        values.append(candidate)
        previous = candidate
        index += 1

    next_candidate: float = start + index * step_value
    if next_candidate >= stop:
        return Ok(value=CottList(values=values))
    return Err(error=FractionalRangeError_OutputLimitExceeded())
