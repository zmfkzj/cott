# json-transform

## Purpose
This v0.7 example wraps nonempty string key-value pairs in a JSON object, safely extracts a string field, and constructs a finite recursive `JsonChain`.

## Key points
- `wrap_scalar_json` is an explicit `async fn` whose awaited return is `JsonValue`; `key.len > 0` is required. Its Python binding is an exact `async def` with no synchronous bridge, constructing the JSON object from a `JsonString` inside a `FrozenMap`.
- `extract_string_field` remains synchronous: it returns `NotAnObject` when the value is not a JSON object, and returns `MissingField` containing the field name as a `Result` error when the field is absent or not a string.
- `JsonChain` is productively recursive: `End` terminates the `Link(value, next: Option[JsonChain])` chain.
- The executable example uses one `asyncio.run(main())`, awaits `wrap_scalar_json`, extracts `greeting`, preserves the existing success output from `{"greeting": "Hello Cott"}`, and prints `Recursive JSON chain: first` from a finite `Link` → `End` chain.
