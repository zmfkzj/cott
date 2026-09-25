from cott_runtime import CottList, Err, F64, Ok, Result
from curriculum.fractional_range_values_types import FractionalRangeError, FractionalRangeError_NonFiniteInput, FractionalRangeError_OutputLimitExceeded, FractionalRangeError_StepDoesNotAdvance, MAX_F64, OutputLimit, PositiveStep


def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]:
    step_value = step.value
    if not (-MAX_F64 <= start <= MAX_F64) or not (-MAX_F64 <= stop <= MAX_F64) or step_value > MAX_F64:
        return Err(error=FractionalRangeError_NonFiniteInput())

    values: list[F64] = []
    count = limit.value
    index = 0
    while True:
        product = float(index) * step_value
        candidate = start + product
        if not candidate < stop:
            return Ok(value=CottList(values=values))
        if index == count:
            return Err(error=FractionalRangeError_OutputLimitExceeded())
        if values and candidate <= values[-1]:
            return Err(error=FractionalRangeError_StepDoesNotAdvance())
        values.append(candidate)
        index += 1
