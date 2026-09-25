# process-bar

## Purpose
The full-agent-generation fixture for `foo.bar`: validate a byte payload, pass its bytes through a pure processing stage, and build output that keeps the payload metadata. `tests/cli.rs` runs this contract with a fake agent that writes fixed implementations. This project holds the actual agent-generated output.

## Key points
- `process_bar` is the domain-named operation. Requirement `STAGES_COMPOSE_THROUGH_FACADES` specifies the root: it calls the public `validate_payload`, `process_payload_bytes` and `build_output` facades in that order, passes each stage's result to the next, and returns the first `Err` unchanged without calling later stages.
- Formal clauses fix every result except the text of the `InvalidPayload` reason. `validate_payload` returns `InvalidPayload` exactly when the payload has no bytes, and otherwise returns the payload unchanged. `process_payload_bytes` declares `errors complete` with no conditions, so it must succeed and return its input bytes; the options do not change the result. `build_output` copies its three arguments. `process_bar` declares `errors complete`: it returns `InvalidPayload` for empty bytes, and otherwise output carrying the input bytes, `declared_size` and `format`.
- `declared_size` is caller-supplied metadata. It is carried to the output and is not compared with the byte count.
- Scenario `process_bar_composes_stages` runs the root twice through the public facade. A two-byte payload (`Bytes("6869")`) must produce exactly that output, and an empty payload must return `InvalidPayload`. `STAGES_COMPOSE_THROUGH_FACADES` links to this scenario, which observes only the root's result. It cannot observe whether `process_bar` actually calls the other facades, so a monolithic `process_bar` that produces the same results would still verify.

## Evidence
`cott verify` certifies the current snapshot. Semantic coverage records all 12 clauses as `observed` (0 unobserved, 0 unknown, 0 trust declarations), from bounded automatic candidates plus the one scenario, not exhaustive checking. `cott requirements` reports `STAGES_COMPOSE_THROUGH_FACADES` as `observed` because both assertions of its linked scenario held. That status covers the two observed results only; the facade calls and call order the requirement states remain unchecked.
