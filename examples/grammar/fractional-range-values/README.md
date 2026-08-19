# fractional-range-values

## Purpose
Constructs a finite half-open floating-point range using a constrained real-valued step and an output limit.

## Key points
- `PositiveStep` represents an `F64` greater than 0, and `OutputLimit` represents a `U32` from 1 through 10000, using `where` constraints.
- `build_bounded_range` first rejects non-finite `start`, `stop`, or `step` with `NonFiniteInput`; for finite inputs, it returns a `List[F64]` including the start and excluding the stop when `start < stop`, or an empty list when `start >= stop`.
- The implementation calculates each candidate as `start + index * step` and returns distinct errors for non-finite input, a step that does not advance after rounding, and exceeding the limit.
