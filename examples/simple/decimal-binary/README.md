# decimal-binary

## Purpose
Convert between nonnegative I64 decimal values and binary strings through two leaves and a tagged composition.

## Key points
- `decimal_to_binary` specifies `NegativeDecimal` for negative inputs and relates zero to `"0"`; its doc specifies shortest ASCII binary text for every other nonnegative value.
- `binary_to_decimal` documents nonempty ASCII input, leading zeros, and invalid-character priority over the 63-significant-digit overflow limit. Those input-wide decisions cannot be expressed as conditional errors here and remain declared errors with scenario evidence.
- `convert_binary_decimal` specifies the selected public conversion facade, the matching result variant, and unchanged error propagation in its doc and linked requirement.
- Scenarios observe concrete zero, six, leading zeros, I64 maximum, overflow, invalid-before-overflow, and both composed routes with their errors. All three requirements are observed in this verified snapshot, not proved; untested inputs and the internal facade-call duty are not exhaustively established.
