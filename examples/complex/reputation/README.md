# reputation

## Purpose
Accumulate reputation events in input order to calculate a nonnegative final reputation.

## Key points
- Upvotes, downvotes, and accepted answers map to fixed changes of `+10`, `-2`, and `+15`, respectively.
- Reject a negative starting reputation first, then check for exceeding the `I32` upper bound and becoming negative after each event; return `ReputationOverflow` or `WouldBecomeNegative` at the first violation.
