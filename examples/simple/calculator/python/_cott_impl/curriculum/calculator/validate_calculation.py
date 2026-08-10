import math

from cott_runtime import Err, F64, Ok, Result, UNIT, Unit
from curriculum.calculator_types import (
    CalculatorError,
    CalculatorError_DivideByZero,
    CalculatorError_NonFinite,
    CalculatorError_PowerDomain,
    CalculatorOp,
    CalculatorOp_Divide,
    CalculatorOp_Power,
)


def validate_calculation(left: F64, operator: CalculatorOp, right: F64) -> Result[Unit, CalculatorError]:
    if not math.isfinite(left) or not math.isfinite(right):
        return Err(error=CalculatorError_NonFinite())
    if isinstance(operator, CalculatorOp_Divide) and right == 0.0:
        return Err(error=CalculatorError_DivideByZero())
    if isinstance(operator, CalculatorOp_Power):
        if (left == 0.0 and right < 0.0) or (left < 0.0 and not right.is_integer()):
            return Err(error=CalculatorError_PowerDomain())
    return Ok(value=UNIT)
