# process-bar

## Purpose
Show the observed full-generation composition: validate a byte payload, process its bytes purely, and preserve its metadata in output.

## Key points
- `process_bar` preserves the distinct generated `foo.bar` facade graph: `validate_payload -> process_payload_bytes -> build_output`.
- Every function in that graph is pure. Validation and declared processing `Err` values propagate unchanged; an empty payload produces `InvalidPayload`.
- `build_output` receives the processed bytes and the validated payload's original size and format.
