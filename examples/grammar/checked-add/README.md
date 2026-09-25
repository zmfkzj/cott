# checked-add

## Purpose
Shows a wider result type and boundary observations for a manifest-bound Python addition.

## Key points
- `checked_add` accepts two `I32` values and returns `I64`. Its `ensures` clauses bound every returned value to `-4294967296` through `4294967294`; those bounds alone do not establish that the value is the sum.
- A scenario observes the exact results at both extreme input pairs, rejecting a constant or 32-bit-wrapped implementation at those inputs. Other input pairs are not exhaustively checked for exact addition.
- `cott.toml` retains the manifest-owned Python binding `cott_bindings.curriculum.checked_add.checked_add:checked_add`; no error variant is declared.
