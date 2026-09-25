# json-transform

## Purpose
This v0.7 example wraps a nonempty string key-value pair in a `JsonValue` object, reads a string member back out, and constructs a finite recursive `JsonChain`.

## Key points
- `JsonValue` is Cott's fixed JSON tagged union. Contract clauses cannot match its variants, so the JSON shape is stated in `doc` and requirements. Scenarios can construct closed `JsonValue` literals such as `JsonValue.Object(value: Map("count": JsonValue.Integer(value: 7)))` and compare returned values with them.
- `wrap_scalar_json` is an explicit `async fn` that requires `key.len > 0`. Requirement `WRAPPED_OBJECT_HAS_ONE_STRING_MEMBER` states that the result is a JSON object whose only member maps `key` to the JSON string `value`.
- `extract_string_field` stays synchronous and returns `Result[StringField, JsonTransformError]`. The `StringField` receipt names the member that was read, so `ensures Result.Ok(found) => found.name == field` relates the success value to the request, and `MissingField` must carry `field`. Its `doc` fixes the rest: exact top-level key lookup, `NotAnObject` checked before `MissingField`, and `MissingField` for an absent or non-string member. Both errors are declared without conditions because clauses cannot inspect `JsonValue`; requirement `SHAPE_FAILURES_ARE_REPORTED` carries that failure mapping.
- Scenario `wrapped_member_round_trips` composes the two facades: it expects `wrap_scalar_json("greeting", "Hello Cott")` to equal exactly `JsonValue.Object(value: Map("greeting": JsonValue.String(value: "Hello Cott")))`, expects `"greeting"` to read back as `"Hello Cott"`, and expects `MissingField` for `"farewell"`.
- Scenario `shape_failures_are_reported` passes a JSON string payload and expects `NotAnObject`, then passes an object whose `count` member is a JSON integer and expects `MissingField`; the contract's `name == field` obligation checks the payload.
- `JsonChain` is productively recursive: `End` terminates the `Link(value, next: Option[JsonChain])` chain.
- The executable example uses one `asyncio.run(main())`, awaits `wrap_scalar_json`, prints the extracted `text` of `greeting`, and prints `Recursive JSON chain: first` from a finite `Link` → `End` chain.

## Evidence
- The scenario and bounded runner cases observe every clause of both callables; semantic coverage records no `unobserved`, `unknown` or `trust declaration` clause.
- `WRAPPED_OBJECT_HAS_ONE_STRING_MEMBER` is `observed` through the exact-object assertion for one input pair; that is bounded evidence, not a check of every key and value.
- `SHAPE_FAILURES_ARE_REPORTED` is `observed` through `shape_failures_are_reported`, which covers one non-object payload (a JSON string) and one non-string member (a JSON integer). Other non-object variants and member types are not exercised by a scenario.
