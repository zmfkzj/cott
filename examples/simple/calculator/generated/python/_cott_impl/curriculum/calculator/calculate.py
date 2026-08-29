from cott_runtime import Err, F64, Ok, Result
from curriculum.calculator_types import (
    CalculatorError,
    CalculatorError_DivideByZero,
    CalculatorOp,
    CalculatorOp_Add,
    CalculatorOp_Divide,
    CalculatorOp_Multiply,
    CalculatorOp_Subtract,
)


def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]:
    match operator:
        case CalculatorOp_Add():
            return Ok(value=left + right)
        case CalculatorOp_Subtract():
            return Ok(value=left - right)
        case CalculatorOp_Multiply():
            return Ok(value=left * right)
        case CalculatorOp_Divide():
            if right == 0.0:
                return Err(error=CalculatorError_DivideByZero())
            return Ok(value=left / right)
