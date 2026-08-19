# calculator

## Purpose
Apply arithmetic operations and exponentiation to two binary64 values while distinguishing floating-point errors.

## Key points
- `CalculatorOp` limits operations to addition, subtraction, multiplication, division, and exponentiation, returning either a result or `CalculatorError` in `Result`.
- Validation rejects NaN/infinity, division by signed zero, a negative exponent of zero, and a non-integer exponent of a negative base in that order.
- The Python implementation converts infinite results from finite inputs and `math.pow` overflow to `Overflow`, while retaining underflow and signed zero as valid results.
