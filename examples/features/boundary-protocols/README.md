# boundary-protocols

## Purpose
This executable boundary-mode witness keeps a client-session identity opaque, projects one external Python type, and drives synchronous and asynchronous protocol lifecycles.

## Cott surface
- `HandleBundle.handle` is exactly `Opaque["client_session"]`. `wrap_handle` rejects only zero and, on success, exposes the accepted nonzero raw ID as `HandleBundle.raw_id`; `extract_handle_id` is the explicit target-side adaptation that unwraps the opaque identity.
- `TextBuffer` is a semantic external Cott type, projected only by `"curriculum.boundary_protocols.TextBuffer" = "io:StringIO"` in `[target.python.external_types]`.
- `adapt_unknown(Any) -> Unknown` deliberately crosses the dynamic boundary. The app narrows the returned `Unknown` with `isinstance` before reading its dictionary value.
- `iter_lines` and `echo_values` retain the synchronous `Iterator` and `Generator[Any, Unknown, U64]` protocols. The generator returns its yielded count after completion.
- `async_lines` accepts and returns `AsyncIterator[Str]`; `echo_async` accepts and returns `AsyncGenerator[Any, Unknown]`. Their bindings are identity `async def` wrappers over caller-supplied protocol objects.

All functions declare `effects []`; `HandleError.InvalidHandle` is the only declared error.

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

The app explicitly calls `__anext__`, `asend`, observes `StopAsyncIteration`, and calls `aclose` twice while `runtime_validation = "boundary"` is configured.
