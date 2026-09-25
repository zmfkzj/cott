# stock-record

## Purpose
Separates a calculation that requires valid input from a function that validates a raw record and delegates to it.

## Key points
- `value_record` puts non-negative shares and price in `requires`, so a violation is the caller's contract error rather than a `Result`. It returns `ValuationOverflow` when the product is not finite, and a successful value is formally finite and non-negative (`0.0 <= value <= MAX_F64`).
- `value_stock_record` states its validation as conditional errors in priority order: `EmptyName` for an empty name, `NegativeShares`, `NonFinitePrice` for a NaN or infinite price, then `NegativePrice`. `ValuationOverflow` stays unconditional because the product of an `I64` and an `F64` cannot be written in a clause.
- Its `doc` and a requirement state the delegation: a valid record is valued by calling the public `value_record` facade, and that result is returned unchanged. Scenarios observe `value_record` on a concrete record and on an overflowing one, that `value_stock_record` returns the same result for both, and a record whose first failing condition is `NegativePrice`. Both requirements are `observed` for these inputs.
- Unverified: Cott observes only equal results, not that the implementation actually calls the facade. Scenarios cannot construct NaN or infinite prices, so the `NonFinitePrice` condition stays `unknown` in semantic coverage and is enforced only by the facade's runtime check on real calls.
