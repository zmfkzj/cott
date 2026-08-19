# stock-input-validation

## Purpose
Connects `newtype`s with `where` constraints to raw stock-input validation and structure construction.

## Key points
- `StockName`, `Shares`, and `Price` use `where` to represent a non-empty string, an integer of at least 0, and a real number of at least 0, respectively.
- On success, `validate_stock_input` returns a `StockInput` composed of the three nominal types.
- The implementation returns the first error in this order: empty name, negative shares, NaN or infinite price, negative price; names containing only whitespace and negative-zero prices are allowed.
