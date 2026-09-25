# assignment-rule

## Purpose
Composes a base rule, strengthens an obligation by override, and deletes a legacy error allowance in an access-code validator.

## Key points
- `BaseAccessCodeRule` requires a nonempty successful value and permits `LegacyFormat`; `StrictAccessCodeRule` overrides the minimum success length from one to four and deletes that error allowance.
- `validate_access_code` returns the original code unchanged when its length is at least four. It does not trim whitespace. Conditional errors and `errors complete` require `EmptyCode` for empty input, `TooShort` for the other shorter inputs, and success otherwise.
- Scenarios observe empty, short, and legacy-prefixed codes. They do not establish any separate whitespace-trimming behavior.
