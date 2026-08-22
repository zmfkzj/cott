# opaque-resource

## Purpose
This executable witness keeps a client-session ID opaque inside a `HandleBundle`, while also showing an external type and iterator/generator boundaries.

## Cott surface
- `Opaque["client_session"]` is nested in `HandleBundle.handle`. `wrap_handle` rejects only `raw_id == 0` with `HandleError.InvalidHandle`; otherwise it returns `Result[HandleBundle, HandleError]`. `extract_handle_id` consumes that bundle and returns its positive ID.
- `TextBuffer` is a semantic external Cott type. Its Python projection is configured separately as `"curriculum.opaque_resource.TextBuffer" = "io:StringIO"` in `[target.python.external_types]`; the Cott source has no backend path. This example does not claim structural or deep runtime validation of external objects.
- `iter_lines(TextBuffer) -> Iterator[Str]` returns lines lazily and removes each yielded line's trailing line ending. The iterator is not eagerly consumed at the binding boundary.
- `echo_values(Iterator[Any]) -> Generator[Any, Unknown, U64]` yields every input `Any`, ignores values sent back through its `Unknown` send channel, then returns the `U64` number of yielded values. Its element values are not deeply validated at the lazy boundary.

All four functions declare `effects []`. The only declared error is `HandleError.InvalidHandle` from `wrap_handle`.

## Expected output
```text
Extracted handle id: 42
Lines: alpha,beta
Generated values: first,7
Generator return count: 2
```
