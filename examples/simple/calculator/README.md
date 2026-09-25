# calculator

## Purpose
Pair a conditional error with a compact arithmetic operation.

## Key points
- `CalculatorOp` selects addition, subtraction, multiplication, or division; the success clause specifies the corresponding arithmetic result.
- `DivideByZero` is required when division is selected with a zero divisor; the remaining successful branches are checked against the declared result relation.
- Verification records bounded clause observations, not a proof of arithmetic correctness. This lesson declares no scenarios or separate composition root.
