# pair-tuple

## Purpose
This example uses Cott v0.2's variadic `Tuple` ABI and generic type parameters to create coordinate pairs and swap the order of their elements.

## Key points
- `make_coordinate_pair` creates `Tuple[I32, I32]` from two `I32` values; the Python binding uses the native immutable `tuple[I32, I32]` ABI.
- `swap_pair[A, B]` converts `Tuple[A, B]` to `Tuple[B, A]`, preserving the order of two distinct types with positional indexing.
- Both functions declare `effects []`; the executable example prints `(10, 20)` and the swapped `(20, 10)`.
