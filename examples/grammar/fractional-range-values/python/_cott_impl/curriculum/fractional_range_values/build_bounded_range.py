from math import isfinite

from cott_runtime import CottList, Err, F64, Ok, Result
from curriculum.fractional_range_values_types import FractionalRangeError, FractionalRangeError_NonFiniteInput, FractionalRangeError_OutputLimitExceeded, FractionalRangeError_StepDoesNotAdvance, OutputLimit, PositiveStep


def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]:
    if not (isfinite(start) and isfinite(stop) and isfinite(step.value)):
        return Err(error=FractionalRangeError_NonFiniteInput())
    if start >= stop:
        return Ok(value=CottList(values=[]))

    values: list[F64] = []
    for index in range(limit.value + 1):
        product = index * step.value
        candidate = start + product
        if candidate >= stop:
            return Ok(value=CottList(values=values))
        if index == limit.value:
            return Err(error=FractionalRangeError_OutputLimitExceeded())
        if values and candidate <= values[-1]:
            return Err(error=FractionalRangeError_StepDoesNotAdvance())
        values.append(candidate)

    return Err(error=FractionalRangeError_OutputLimitExceeded())
