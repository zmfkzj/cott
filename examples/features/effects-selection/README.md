# effects-selection

## Purpose

This feature project declares each built-in Cott effect on a typed public function whose implementation is agent-generated. The compiler owns the scenario identities and every executable filesystem, HTTP, clock, and failure fixture; the manifest declares no fixture identities and no bindings. Scenarios observe results with pattern assertions and read the resulting state back through a public facade.

## Contracts

- `read_text` (`file.read`) returns a `FileText` pairing the strictly decoded UTF-8 text with its source path (`file.path == source`). An absent source is `InputMissing` carrying that path; other read failures and invalid UTF-8 are `OperationFailed`.
- `copy_text` (`file.read`, `file.write`) returns a `CopyReceipt` naming the destination and the number of UTF-8 bytes written, not characters. A `read_text` error is returned unchanged (an `InputMissing` payload is the source path) and leaves the destination untouched. Requirement `COPY_IS_ATOMIC` states that a failed replacement returns `OperationFailed` and keeps the previous destination bytes; `COPY_READS_THROUGH_READ_TEXT` states that the source is read only through the public `read_text` facade.
- `fetch_local` (`network`) returns a `PageText` pairing the UTF-8 text of the final response with the requested URL. Redirects are followed. The empty URL is a conditional `OperationFailed`; transport failures, timeouts, statuses outside 200-299, and invalid UTF-8 are `OperationFailed`.
- `clock_ns` (`clock`) reads the fixture clock in nanoseconds: the fixture is configured in milliseconds, so `start_ms: 17` reads as `17000000`, and reading does not advance the clock.
- `store_and_load` (`database.read`, `database.write`), `sample_index` (`random`), and `exit_with_code` (`process.exit`) have no fixture backend, so no scenario can call them. Their clauses (`stored == value`, `requires limit > 0`, `result < limit`) remain trust declarations, and nothing rejects an implementation that echoes `value`, always returns index 0, or exits with another status: requirements `STORED_VALUE_IS_READ_BACK`, `SAMPLE_IS_SEEDED`, and `EXIT_STATUS_IS_CODE` stay `unverified`.

## Evidence

- `filesystem_copy` reads `café`, copies it and asserts `bytes_written == 5` (UTF-8 bytes, not the 4 characters), reads the destination back, then copies from an absent source, asserts `InputMissing`, and reads the unchanged destination back. Finally it reads a file holding the single byte `0xff` and asserts `OperationFailed`, which rejects lenient decoding.
- `filesystem_replace_failure` injects a `disk_full` failure at `file.replace`, asserts `OperationFailed`, and reads the previous destination text back. It is the check linked to `COPY_IS_ATOMIC`.
- `local_http` follows a relative redirect to a UTF-8 body, asserts an error for an injected `http.read` timeout, and calls the empty URL so the facade boundary observes the conditional error.
- `deterministic_clock` reads the clock twice and asserts `17000000` both times.

With `runtime_validation = "boundary"`, each scenario call also checks the facade's clauses. The last Python `cott verify` recorded all four scenarios as test observations; the isolated-loopback sandbox was available, so `local_http` is not `unobserved`. Semantic coverage is `observed=11 trust_declaration=4`: every `read_text`, `copy_text`, and `fetch_local` clause is observed, and the four `store_and_load` and `sample_index` clauses stay trust declarations. Requirements: `COPY_IS_ATOMIC` is `observed` through `filesystem_replace_failure`; the other four are `unverified`. Observations are bounded evidence, not proofs.

`COPY_READS_THROUGH_READ_TEXT` has no linked check and stays `unverified`.

## Kotlin mirror

`examples/kotlin/features/effects-selection` carries the same contract. The Kotlin runner has no `http` or `failure` fixture backend, so `local_http` and `filesystem_replace_failure` stay unexecuted there and `COPY_IS_ATOMIC` stays `unverified`. Its last `cott verify` passed `filesystem_copy` and `deterministic_clock` and recorded semantic coverage `observed=7 unknown=8`: every `read_text` clause and the `copy_text` success, `InputMissing`-payload, and `InputMissing` clauses are observed, while the `copy_text` `OperationFailed` allowance and every `fetch_local`, `store_and_load`, and `sample_index` clause are `unknown`, because the Kotlin runner reports effectful clauses no executed scenario reaches as `unknown` rather than as trust declarations. All five requirements are `unverified` there. Kotlin reads the fixture clock through `CottRuntime.fixtureClockNs`, which already returns nanoseconds, while the Python adapter returns milliseconds that the implementation converts; the contract is the same.

## Run

After generation, run `python app.py` from the Python project to list the public facades that the fixture scenarios exercise. The app creates no files, servers, subprocesses, or wall-clock observations; fixture scenarios run only through the compiler's isolated verification workflow.
