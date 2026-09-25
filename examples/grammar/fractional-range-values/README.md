# fractional-range-values

## Purpose
Builds a bounded half-open floating-point range from refined inputs: a positive `F64` step and an output limit.

## Key points
- `PositiveStep` wraps an `F64` greater than 0, and `OutputLimit` wraps a `U64` from 1 through 10000. Both are `where` refinements checked at the facade boundary.
- `build_bounded_range` formally states that a successful list has at most `limit` values and is empty exactly when `start >= stop`, and that a NaN or infinite `start`, `stop` or `step` returns `NonFiniteInput`. `MAX_F64` is the largest finite binary64 value used by that condition.
- The `doc` defines each value as `start + index * step`, rounded once after the multiplication and once after the addition. `StepDoesNotAdvance` and `OutputLimitExceeded` depend on every candidate, which clauses cannot quantify over, so they remain unconditional errors described in `doc` and backed by scenarios and two linked requirements.
- Scenarios observe the exact list for step `0.1` (a running sum would return 11 values ending in `0.9999999999999999`), a limit that is met exactly versus exceeded, and a stalled step at 2^53 where the limit takes precedence. Both requirements are `observed`: bounded evidence for these inputs, not a proof for other ranges.
- Unverified: scenarios cannot construct NaN or infinity and the automatic candidates contain none, so the `NonFiniteInput` clause stays `unknown` in semantic coverage and is enforced only by the facade's runtime check on real calls.
