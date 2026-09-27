# https://github.com/tconbeer/harlequin

Clean-room Cott reimplementation pinned to Harlequin **v2.15.0** (upstream commit
`03b62a7d82baa5f2086e96c0ea9fec06bb89f86d`). It offers the full-screen
`harlequin` SQL IDE and the headless `hsql` command. Python callable implementations
are generated from `src/real/harlequin/*.cott`; the two small scripts in `python/`
launch the public generated facades. The upstream application distribution is **not**
a runtime dependency.

## Parity and boundaries

| Surface | Reimplementation | Deliberate boundary |
| --- | --- | --- |
| Terminal IDE | Prompt-toolkit full-screen editor, query bar, results grid, catalog tree, dialogs, key actions, themes, and query history | Uses prompt_toolkit rather than upstream Textual subclasses; terminal layout and visual styling are not pixel-identical. |
| Headless `hsql` | SQL command/file/stdin, formats, catalog/history/config modes, session protocol, diagnostic exit codes | Invoke `python/hsql_cli.py` directly; the package does not replace an upstream `hsql` installation. |
| Database drivers | DuckDB, SQLite, PostgreSQL, MySQL, ODBC, BigQuery, Trino, Databricks, ADBC, Cassandra, NebulaGraph, chDB | Twelve adapters are statically shipped; arbitrary third-party `harlequin.adapter` entry-point discovery is not available. External services need their actual endpoints and credentials. |
| Data and configuration | Arrow-backed query results, exports, SQL formatting, profile merge, keymaps, file browser, history, clipboard and SSH support | Capability depends on platform facilities (for example clipboard, SSH, ODBC drivers) and the locked SDK packages. |

The 17 modules divide the contract into `adapters` (connections, results, catalog
operations and cancellation); `sqltext`, `results`, `catalog`, `history`, `export`,
`files`, `style`, `keymap` and `ide` (models and rendering); `config`, `cli` and
`support` (profiles, arguments and host facilities); and `app`, `tools`, `main`
and `hsql` (interactive and headless composition). The shipped keymap covers
117 actions, and the theme catalog describes 20 themes.

A successful `cott verify` certifies that the **current generated snapshot** matches
its Cott contracts; it does not prove parity for external databases or the terminal
interface. Cott scenarios inspect contract-level behavior; external regressions run
`hsql` over real scratch SQLite and DuckDB files and exercise retained sessions,
transactions, disconnect rollback and query-history insert/read/update on a
scratch SQLite log. The PTY smoke exercises the IDE UI on those
local databases. Remote adapters, external SQL services, clipboard and SSH
integrations have not been exercised. Neither class of external test becomes
scenario evidence.

The verified snapshot records 143 observed contract clauses, 59 trusted
declarations, 0 unknown and 1 unobserved clause. `cott requirements` reports
`CONNECT_RETAINS_A_LIVE_SESSION` as unverified because it has no `checked_by`
linkage. The external retained-session regression exercises that behavior but
does not turn it into Cott requirement evidence.

The strict coverage policy selects 88 clauses across 43 callables, including
connection/query/result handling, transaction and cancellation errors, retained
session requests, history persistence, exports, file failures and core CLI/IDE
transformations. No `unobserved`, `trust_declaration` or `unknown` is allowed.
Sol regeneration and actual `verify` resolved 24 of the previous 42 policy
violations. The remaining 18 are trust declarations: 16 require a database
fixture backend and two require a private Unix-socket peer and interruption
control for `send_session_request`. The verifier certified the artifact snapshot
but exited nonzero on those strict-policy violations; deployment remains blocked.
External SQLite/DuckDB regressions do not replace the missing Cott observations.
The current compiler can also classify contract `proved` evidence as `observed`;
neither that status nor policy selection establishes execution of every branch.

The export facade scenario now writes every fetched row through the real SDK.
DuckDB export connections use `threads=1`: the default host-sized worker pool
aborted under the runner's process/thread limit. The bounded connection passed
the same sandbox constraints; no resource ceiling or coverage rule was relaxed.
Generated callbacks use explicit `Callable` annotations to satisfy the pinned
type checker without suppressions.

## Run

```sh
project=examples/real/harlequin
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model openai-codex/gpt-6-sol --target python -j 4 --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/hsql_cli.py" \
  --adapter sqlite :memory: --csv --command 'SELECT 42 AS answer'
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/harlequin_cli.py" \
  --adapter sqlite :memory:
```

The ignored `tests/harlequin_program.rs` deploys the verified snapshot into a Linux
sandbox and runs `tests/support/harlequin_program.py`. The separate
`tests/support/harlequin_sessions.py` checks retained SQLite/DuckDB sessions
and persistent query-history transitions through public adapter/history facades.
Run it with the same `PYTHONPATH` as above.

```sh
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" tests/support/harlequin_sessions.py
cargo test --test harlequin_program -- --ignored --nocapture
```

The manifest uses no implementation bindings.
