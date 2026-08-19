# decimal-binary

## Purpose
Convert between non-negative I64 decimal numbers and binary strings.

## Key points
- The `Conversion` and `ConversionResult` tagged enums distinguish decimal-to-binary and binary-to-decimal requests and results through one entry point.
- Decimal conversion returns `"0"` for 0 and the shortest binary representation without leading zeros for other values; negatives produce `NegativeDecimal`.
- The Python implementation first validates the entire binary string as ASCII `0`/`1`, so invalid characters take precedence over overflow; if more than 63 effective digits remain after removing leading zeros, it returns `Overflow`.
