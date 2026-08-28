# json-transform

## Purpose
This example wraps string key-value pairs in a JSON object using Cott v0.3's `JsonValue` ABI and safely extracts a string field from an object.

## Key points
- `wrap_scalar_json` is an explicit `async fn` whose awaited return is `JsonValue`; its Python binding is an exact `async def` with no synchronous bridge, constructing the JSON object from a `JsonString` inside a `FrozenMap`.
- `extract_string_field` remains synchronous: it returns `NotAnObject` when the value is not a JSON object, and returns `MissingField` containing the field name as a `Result` error when the field is absent or not a string.
- The executable example uses one `asyncio.run(main())`, awaits `wrap_scalar_json`, then extracts `greeting` and prints the unchanged success value from `{"greeting": "Hello Cott"}`.
