# stock-record

## Purpose
Demonstrates the separation between a calculation function requiring preconditions and a function that validates a raw record before delegating to it.

## Key points
- `value_record` assumes through `requires` that the price and shares are at least 0, and returns `ValuationOverflow` only for a non-finite multiplication result.
- `value_stock_record` validates the name, shares, and price before passing a valid `StockRecord` to `value_record`, and guarantees that a successful value is at least 0.
- The implementation's error precedence is empty name, negative shares, non-finite price, and negative price, followed by a valuation-overflow check.
