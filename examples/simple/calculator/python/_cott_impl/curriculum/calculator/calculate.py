from cott_runtime import F64, Err, Ok, Result
from curriculum.calculator_types import CalculatorError, CalculatorError_DivideByZero, CalculatorOp, CalculatorOp_Add, CalculatorOp_Divide, CalculatorOp_Multiply, CalculatorOp_Subtract


def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]:
    if isinstance(operator, CalculatorOp_Add):
        return Ok(value=left + right)
    if isinstance(operator, CalculatorOp_Subtract):
        return Ok(value=left - right)
    if isinstance(operator, CalculatorOp_Multiply):
        return Ok(value=left * right)
    assert isinstance(operator, CalculatorOp_Divide)
    if right == 0.0:
        return Err(error=CalculatorError_DivideByZero())
    return Ok(value=left / right)
