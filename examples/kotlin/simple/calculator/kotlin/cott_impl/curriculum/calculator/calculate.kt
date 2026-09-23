package cott_impl.curriculum.calculator

internal fun calculate(left: kotlin.Double, `operator`: curriculum.calculator.CalculatorOp, right: kotlin.Double): cott_runtime.CottResult<kotlin.Double, curriculum.calculator.CalculatorError> {
    return when (`operator`) {
        curriculum.calculator.CalculatorOp.Add -> cott_runtime.Ok(left + right)
        curriculum.calculator.CalculatorOp.Subtract -> cott_runtime.Ok(left - right)
        curriculum.calculator.CalculatorOp.Multiply -> cott_runtime.Ok(left * right)
        curriculum.calculator.CalculatorOp.Divide -> {
            if (right == 0.0) {
                cott_runtime.Err(curriculum.calculator.CalculatorError.DivideByZero)
            } else {
                cott_runtime.Ok(left / right)
            }
        }
    }
}
