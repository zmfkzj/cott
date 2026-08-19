# parse-assignment

## Purpose
Declares a `Result` parsing contract with success conditions and explicit errors.

## Key points
- `ensures` guarantees that a successful `Assignment` has a `name` length greater than 0 and declares `MissingEquals` and `EmptyName` as function errors.
- The implementation uses only the first `=` as a delimiter and trims only leading and trailing whitespace from the name and value, preserving subsequent `=` characters and whitespace within fields.
- It returns `MissingEquals` when there is no delimiter and `EmptyName` when the trimmed name is empty; an empty value itself is valid.
