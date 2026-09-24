# effects-selection

## Purpose

This feature project declares each built-in Cott effect on a typed public function whose implementation is agent-generated. The compiler owns scenario identities and all executable filesystem, HTTP, clock, and failure fixtures; the manifest does not declare fixture identities.

## Effect contracts

- `read_text` decodes the bytes returned by compiler-private `cott_runtime._cott_fixture_read` as UTF-8. Its declared errors are `InputMissing` and `OperationFailed`.
- `copy_text` calls `read_text` through the generated `curriculum.effects_selection` public facade, then publishes UTF-8 **bytes** through `_cott_fixture_replace` and returns the encoded byte count. Its failure scenario checks that the previous destination content remains observable after an injected `file.replace` failure.
- The pure public `text_result_is_ok`, `text_result_text`, and `copy_result_is_ok` facades make typed `Result` outcomes observable to finite scenarios without private inspection. Scenarios assert exact successful text, copy success or failure, and preserved destination text through these facades.
- `fetch_local` uses `_cott_fixture_http` only. Its local scenario checks UTF-8 decoding after a relative redirect, an eight-character response, an injected `http.read` timeout, and rejection of the conditional empty URL error.
- `clock_ns` converts `_cott_fixture_now` milliseconds to deterministic nanoseconds and its scenario reads the fixed clock twice.
- `store_and_load` (`database.read`, `database.write`), `sample_index` (`random`), and `exit_with_code` (`process.exit`) are typed trust declarations. There is no compatible fixture backend for them, so no scenario executes them.

## Run

After Cott generation, run `python app.py` from the Python project to list the public facades covered by compiler-owned scenarios. The app creates no files, servers, subprocesses, or wall-clock observations. Fixture scenarios run only through the compiler's isolated verification workflow.

## Selection scope

`cott.toml` selects no manifest bindings; every public Cott function is generated into `python/_cott_impl/curriculum/effects_selection/<function>.py`. `copy_text` retains the generated public facade as its only call boundary to `read_text`; no implementation imports a host path, endpoint, or clock. There is no hand-authored generation record.
