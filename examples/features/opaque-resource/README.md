# opaque-resource

## Purpose
This example uses Cott v0.1's tagged `Opaque["client_session"]` ABI to distinguish a raw connection ID as a client-session handle.

## Key points
- `wrap_handle` returns `HandleError.InvalidHandle` when `raw_id == 0`; otherwise, it creates an opaque handle tagged `client_session` as a successful `Result` value.
- The Python binding represents this type as `Opaque[Literal["client_session"]]`, so `extract_handle_id` accepts only handles with the same tag and extracts the inner `U64` ID.
- `extract_handle_id` declares an `ensures` contract that its result is greater than 0 and `effects []`; the executable example wraps ID `42` and prints it again.
