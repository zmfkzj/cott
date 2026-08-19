# assignment-rule

## Purpose
Applies `@rule` inheritance, contract refinement, and error deletion to a single parsing function.

## Key points
- `BaseAssignmentRule` guarantees that a successful `Assignment` has a non-empty name and declares the `MissingEquals` error.
- `StrictAssignmentRule` `override`s the name condition to require length 2 or greater, `delete`s the inherited `MissingEquals` error, then adds the non-empty value condition and the `EmptyName` error.
- `parse_assignment` uses `rule StrictAssignmentRule`; the Python implementation splits on the first `=`, trims both sides, then returns `EmptyName` when the name is one character or shorter or the value is empty.
