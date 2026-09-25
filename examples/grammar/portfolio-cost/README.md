# portfolio-cost

## Purpose
Values a list of structs in order and reports the first failing holding through an error enum.

## Key points
- `Holding` has an `I64` share count and an `F64` price. `calculate_portfolio_cost` formally states that a successful total is finite and non-negative (`0.0 <= total <= MAX_F64`).
- The `doc` defines the total as shares times price accumulated from `0.0` in list order and fixes the error order: holdings in list order, and within a holding `NegativeShares`, then `NonFinitePrice`, then `NegativePrice`, with `TotalOverflow` reported at the holding whose product or running total is not finite. These conditions range over list elements, which clauses cannot quantify over, so all four errors remain unconditional.
- Scenarios observe an exact total, an earlier `NegativePrice` winning over a later `NegativeShares`, share validation before price validation, a product overflow, and a running-total overflow that precedes a later invalid holding. Both linked requirements are `observed`: bounded evidence for these inputs, not a proof for other portfolios.
- Unverified: scenarios cannot construct NaN or infinite prices and the automatic candidates contain none, so `NonFinitePrice` stays `unobserved` in semantic coverage. Other totals are checked only against the finite, non-negative bound.
