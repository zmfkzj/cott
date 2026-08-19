# pair-tuple

## Purpose
This example uses Cott v0.1's two-element `Tuple` ABI and generic type parameters to create coordinate pairs and swap the order of their elements.

## Key points
- `make_coordinate_pair` creates `Tuple[I32, I32]` from two `I32` values; in the Python binding, it is represented by `CottTuple2` with `first` and `second` fields.
- `swap_pair[A, B]` converts `Tuple[A, B]` to `Tuple[B, A]`, so the Python implementation also places `second` first and `first` last to preserve the order of two distinct types.
- Both functions declare `effects []`; the executable example prints `(10, 20)` and the swapped `(20, 10)`.
