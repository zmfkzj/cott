import math

from cott_runtime import Err, F64, Ok, Result
from curriculum.calculator_types import (
    CalculatorError,
    CalculatorError_DivideByZero,
    CalculatorError_NonFinite,
    CalculatorError_Overflow,
    CalculatorError_PowerDomain,
    CalculatorOp,
    CalculatorOp_Add,
    CalculatorOp_Divide,
    CalculatorOp_Multiply,
    CalculatorOp_Power,
    CalculatorOp_Subtract,
)


def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]:
    if not math.isfinite(left) or not math.isfinite(right):
        return Err(error=CalculatorError_NonFinite())
    if isinstance(operator, CalculatorOp_Divide) and right == 0.0:
        return Err(error=CalculatorError_DivideByZero())
    if isinstance(operator, CalculatorOp_Power):
        if (left == 0.0 and right < 0.0) or (left < 0.0 and not right.is_integer()):
            return Err(error=CalculatorError_PowerDomain())

    try:
        if isinstance(operator, CalculatorOp_Add):
            result = left + right
        elif isinstance(operator, CalculatorOp_Subtract):
            result = left - right
        elif isinstance(operator, CalculatorOp_Multiply):
            result = left * right
        elif isinstance(operator, CalculatorOp_Divide):
            result = left / right
        else:
            result = math.pow(left, right)
    except OverflowError:
        return Err(error=CalculatorError_Overflow())

    if not math.isfinite(result):
        return Err(error=CalculatorError_Overflow())
    return Ok(value=result)
