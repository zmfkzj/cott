# effects-selection

## Purpose

This feature project maps each built-in Cott effect to a typed binding. The compiler owns v0.8 scenario identities and all executable filesystem, HTTP, clock, and failure fixtures; the manifest does not declare fixture identities.

## Effect contracts

- `read_text` reads UTF-8 through the compiler-private `cott_runtime._cott_fixture_read` adapter. A missing fixture file becomes `InputMissing`; decoding and injected fixture failures become `OperationFailed`.
- `copy_text` calls `read_text` through the generated `curriculum.effects_selection` public facade, then uses `_cott_fixture_replace` for atomic replacement. Its failure scenario proves that the previous destination content remains observable after an injected `file.replace` failure.
- The pure public `text_result_is_ok`, `text_result_text`, and `copy_result_is_ok` facades make typed `Result` outcomes observable to finite scenarios without private inspection. Scenarios assert exact successful text, copy success or failure, and preserved destination text through these facades.
- `fetch_local` uses `_cott_fixture_http` only. Its local scenario proves UTF-8 decoding after a relative redirect, an eight-character response, an injected `http.read` timeout, and rejection of the conditional empty URL error.
- `clock_ns` converts `_cott_fixture_now` milliseconds to deterministic nanoseconds and its scenario reads the fixed clock twice.
- `store_and_load` (`database.read`, `database.write`), `sample_index` (`random`), and `exit_with_code` (`process.exit`) are typed trust declarations. v0.8 has no compatible fixture backend for them, so no scenario executes them.

## Run

After Cott generation, run `python app.py` from the Python project to list the public facades covered by compiler-owned scenarios. The app creates no files, servers, subprocesses, or wall-clock observations. Fixture scenarios run only through the compiler's isolated verification workflow.

## Selection scope

`cott.toml` maps every public Cott function to its exact typed local binding. `copy_text` retains the generated public facade as its only call boundary to `read_text`; no binding imports a host path, endpoint, or clock. There is no `_cott_impl` source or hand-authored generation record.
