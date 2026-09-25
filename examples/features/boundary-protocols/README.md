# boundary-protocols

## Purpose
This executable boundary-mode example keeps a client-session identity opaque, projects one external Python type, and drives synchronous and asynchronous protocol lifecycles.

## Cott surface
- `ConnectionId` is a `U64` newtype refined by `where self > 0`, so a zero ID cannot be constructed. `HandleBundle.handle` is exactly `Opaque["client_session"]`, and the contract `doc` fixes its payload as the ID's `U64` value. `wrap_handle` builds the bundle (`ensures result.raw_id == raw_id`); `extract_handle_id` is the explicit target-side adaptation that reads the payload back into a `ConnectionId`.
- `TextBuffer` is a semantic external Cott type, projected only by `"curriculum.boundary_protocols.TextBuffer" = "io:StringIO"` in `[target.python.external_types]`.
- `adapt_unknown(Any) -> Unknown` deliberately crosses the dynamic boundary and returns the value itself. The app narrows the returned `Unknown` with `isinstance` before reading its dictionary value.
- `iter_lines` and `echo_values` keep the synchronous `Iterator` and `Generator[Any, Unknown, U64]` protocols. The `doc` defines a line (terminated by LF, CR or CRLF, terminator excluded) and the generator's return value (the number of yielded values).
- `async_lines` accepts and returns `AsyncIterator[Str]`; `echo_async` accepts and returns `AsyncGenerator[Any, Unknown]`. Both hand the caller's protocol object back.

All functions declare `effects []`.

## Evidence
- Scenario `handle_round_trips_id` passes `wrap_handle(ConnectionId(42))` to `extract_handle_id` and checks that the same ID comes back. It is the linked check for requirement `HANDLE_ROUND_TRIPS_ID`. It observes the returned value for one ID, not which field the implementation read.
- The contract runner cannot construct opaque, external or protocol inputs and records no lifecycle observations for these callables. Their requirements `RETURNS_SAME_VALUE`, `YIELDS_LINES_LAZILY`, `ECHOES_EACH_VALUE_ONCE`, `RETURNS_SUPPLIED_ITERATOR` and `RETURNS_SUPPLIED_GENERATOR` stay `unverified`.
- The app output below is checked by the repository test `tests/examples.rs`. That is a program regression, not Cott evidence.

## Expected output
```text
Wrapped raw id: 42
Extracted handle id: 42
Narrowed unknown: explicit
Lines: alpha,beta
Generator return count: 2
Generated values: first,7
Async lines: gamma,delta
Async iterator completed
Async generated values: first,7
Async generator completed
Async generator closed twice
```

The app explicitly calls `__anext__` and `asend`, observes `StopAsyncIteration`, and calls `aclose` twice while `runtime_validation = "boundary"` is configured.
