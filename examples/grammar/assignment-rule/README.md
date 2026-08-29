# assignment-rule

## Purpose
Compose, override, and delete rule clauses for an access-code validator.

## Key points
- `BaseAccessCodeRule` declares the legacy-format and empty-code errors.
- `StrictAccessCodeRule` overrides the empty-code clause with a false condition, deletes the legacy-format clause, and adds `TooShort`.
- `validate_access_code` applies the composed rule and trims codes before rejecting values shorter than four characters.
