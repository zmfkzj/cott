# validated-stock

## Purpose
Places range-validated nominal types at the input boundary, narrowing the error domain of subsequent calculation to overflow alone.

## Key points
- The `where` constraints on `StockName`, `Shares`, and `Price` express a non-empty name, shares of at least 0, and a price no greater than the finite binary64 maximum, respectively.
- `Stock` consists only of these three `newtype`s; a constructor-validation failure is a contract violation, not a `ValuationError` from `value_stock`.
- `value_stock` multiplies shares and price once, returns `Overflow` if it becomes infinite, and otherwise returns a value from 0 through the binary64 maximum.
