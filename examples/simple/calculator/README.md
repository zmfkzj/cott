# calculator

## Purpose
Pair a conditional error with a compact arithmetic operation.

## Key points
- `CalculatorOp` selects addition, subtraction, multiplication, or division.
- `calculate` declares `DivideByZero` only when the selected operation divides by zero.
- The durable Python implementation follows the same branch before returning the selected arithmetic result.
