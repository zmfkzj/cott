# random-password-generator

## Purpose
Create reproducible passwords from a supplied list of integer draws instead of external randomness.

## Key points
- Length is limited to 1–128, and `required_password_draws` calculates the exact number of draws required: `2n + floor(n / 2) - 1`.
- The Python implementation determines the counts of letters, digits, and special characters from the length, selects character sets using each draw's modulo, then applies a Fisher-Yates shuffle.
- Length errors become `InvalidLength` before draw length is considered, and insufficient draws become `InsufficientDraws` in `Result` before indexing.
