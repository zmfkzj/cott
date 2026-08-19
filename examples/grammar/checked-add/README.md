# checked-add

## Purpose
Connects a return integer type wider than its inputs and a result-range contract to an external Python implementation.

## Key points
- `checked_add` accepts two `I32` values and returns `I64`, declaring with `ensures` the exact possible-sum range from `-4294967296` through `4294967294`.
- In this range, adding two signed 32-bit integers cannot overflow `I64`, so there are no declared errors.
- The implementation mapping in `cott.toml` connects the function to `cott_bindings.curriculum.checked_add.checked_add:checked_add`, and the Python binding adds the two arguments unchanged.
