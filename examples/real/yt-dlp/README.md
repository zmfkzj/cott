# https://github.com/yt-dlp/yt-dlp

A clean-room Cott reimplementation of a direct-media retrieval CLI. Its public
contracts model CLI input, HTTP(S) discovery, selection, transfers, rendering,
post-processing, and updates.
It is not a complete upstream extractor/plugin or command-line compatibility layer.

## Run

```sh
project=examples/real/yt-dlp
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" URL
```

Archives contain this client's plain media ids, one UTF-8 line per entry; they
are not upstream yt-dlp's extractor-key/id archive format. Plugin input is a
declarative text manifest (`extractor:NAME` or `postprocessor:NAME`), never
dynamically imported Python code.

The explicit updater API installs the official upstream `yt-dlp` release asset
at the caller's target, not a release of this Cott reimplementation. It verifies
the official HTTPS SHA-256 manifest before descriptor-relative atomic replacement.
`Check` does not replace the file; `Never` performs no update work.

## Requirement and program evidence

`execute` now specifies discovery, selection, planning, real transfer and rendering.
The CLI uses the documented Download defaults; other simulation modes are selected
through the typed `ExecutionRequest` API, not an invented `--simulate` flag.
`Path(".")` disables archive I/O and presentation logging.

`src/real/yt_dlp.cott` includes a reusable nested `ExecutionRequest` test value and
a scenario that checks network/input validation and exact rendered output without
public builder helpers. This scenario does **not** exercise `execute` or `run`.
Their `random` / `process.exit` effects have no current Cott scenario fixture backend.

```sh
cott requirements --project examples/real/yt-dlp --format json
cargo test --test yt_dlp_program -- --ignored --nocapture
```

The external program regression deploys the current verified snapshot, then runs
real generated facades and `app.py` with only isolated loopback HTTP and scratch
filesystem access. It checks discovered report content, exact downloaded bytes,
declared failures and CLI output/exit status. Separate compiler-bound, type-valid
defect fixtures reproduce empty reports, wrong content, unjustified errors and
skipped execution. These fixtures are not verified example implementations.
Unavailable sandbox capability fails closed; there is no host-network fallback.
Results are labeled `external_program_regression`, never Cott scenario evidence.
The three unlinked normative requirements therefore remain `unverified` in
`cott requirements`, even when this independent regression succeeds.
