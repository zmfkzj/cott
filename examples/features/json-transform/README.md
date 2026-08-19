# json-transform

## Purpose
This example wraps string key-value pairs in a JSON object using Cott v0.1's `JsonValue` ABI and safely extracts a string field from an object.

## Key points
- `wrap_scalar_json` returns `JsonValue` under an `effects []` contract, and the Python binding constructs a JSON object from a `JsonString` inside a `FrozenMap`.
- `extract_string_field` returns `NotAnObject` when the value is not a JSON object, and returns `MissingField` containing the field name as a `Result` error when the field is absent or not a string.
- The executable example creates `{"greeting": "Hello Cott"}`, extracts `greeting`, and prints the success value.
