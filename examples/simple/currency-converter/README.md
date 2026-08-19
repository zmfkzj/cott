# currency-converter

## Purpose
Convert currency amounts from an EUR-based exchange-rate list while handling input and rounding boundaries.

## Key points
- `ConversionRequest` combines the amount, source and destination currencies, and rates per EUR in one type contract; a `Rate` code must be exactly three uppercase ASCII letters.
- Validation checks finite, non-negative amounts; positive, finite rates; and source/destination rates with neither duplicates nor omissions in the specified error priority.
- The Python implementation divides by the source rate then multiplies by the destination rate, validates the complete rate list even for the same currency before rounding, and rounds cent ties to even.
