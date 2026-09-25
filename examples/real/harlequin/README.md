# https://github.com/tconbeer/harlequin

A clean-room Cott reimplementation of the Harlequin SQL client. Its public boundary is
generated from `core`, `catalog` and `render`; it does not depend on the upstream
application distribution. It does not reimplement Harlequin's full-screen Textual
interface, plugin-based adapter discovery, file browser or upstream export engine: the
program is a line-oriented `sql>` client, or a one-shot `--query-file` run, over the
library facades below.

## What the contracts specify

- `core`: command-line options (`parse_cli`), the `.harlequin.toml` format
  (`load_configuration`), pure connection planning in which command-line options override
  the selected profile (`resolve_profile`), adapter descriptors and endpoint formats for
  DuckDB, SQLite, PostgreSQL, MySQL, ODBC, BigQuery, Trino, Databricks, ADBC, Cassandra and
  NebulaGraph, live sessions (`connect`, `disconnect`), one-use transaction leases
  (`begin_transaction`, `commit_transaction`, `rollback_transaction`, reporting a
  `TransactionStatus`), statement splitting, bounded execution on the retained session
  (`execute_statements`), standalone SQLite execution (`execute_sql`), editor tabs and
  history, UTF-8 query files on local disk or S3, and the `run` composition root.
- `catalog`: standalone SQLite catalog listing and search, `refresh_catalog` through an
  independent metadata client for each adapter, completion (`complete_sql`) and snapshot
  search (`find_catalog`).
- `render`: table, vertical and width-bounded views, catalog views, bundled themes and
  keymaps, and CSV, TSV, JSON, Markdown and SQL exports that return a `SavedFile` receipt.

`run` parses the arguments, loads `.harlequin.toml` unless `--no-config` is given (a
missing file means no profiles), resolves the profile and connects. It then either executes
the `--query-file` once or runs the `sql>` loop until `.quit` or end of input, printing
tab-separated results, and it always disconnects. The exit status is 2 for argument,
configuration and profile errors, 1 for connection, batch and disconnect failures, and 0
otherwise.

Formal clauses carry the relations that the contract language can state: preserved
metadata and connections, `TransactionStatus` after begin, commit and rollback, conditional
errors decided from inputs (blank or repeated setting names, adapters without transactions,
inactive lease snapshots, non-writable destinations, zero widths, oversized search limits),
error payloads that name the caller's path, reference, limit or width, an empty endpoint in
`InvalidEndpoint`, and the timestamp shape of a catalog snapshot. The generator rules hold
only Python type-checker and SDK technique. The manifest selects no bindings.

## Evidence

`cott verify` certified the current Python snapshot with semantic coverage observed=71,
trust_declaration=46, unknown=16 and unobserved=5. Observations are bounded evidence, not
proof, and verification does not establish release readiness.

- Scenarios observe the pure and file-level behavior: the adapter table, command-line
  parsing and its first-offending-argument errors, `.harlequin.toml` loading, profile
  resolution, tab and history state, statement splitting, UTF-8 query-file round trips and
  their errors, a failed save that keeps the previous file (fixture `file.replace`
  failure), table, vertical and bounded rendering, catalog views, bundled themes and keymaps,
  completion, snapshot search and all five export formats. The file scenarios also declare
  an HTTP fixture only because the facades carry the `network` effect for S3; S3 itself is
  not exercised.
- Facades with `database.*`, `random` or `process.exit` effects cannot be called by Cott
  scenarios, and automatic candidates never execute effectful callables, so the clauses of
  `connect`, `disconnect`, the transaction calls, `execute_statements`, `execute_sql`, the
  SQLite catalog functions, `refresh_catalog` and `run` remain `trust_declaration`, `unknown`
  or `unobserved`.
- The verify run reports 20 requirements: 1 observed and 19 unverified.
  `SAVE_REPLACES_ATOMICALLY` is linked to the failed-save scenario and observed. The other
  19 are unlinked and `unverified`: live-session retention, secret-free errors (connect,
  statements, catalog), disconnect rollback, retained-driver transactions, single-use lease
  authority, rollback of leased statements, atomic `execute_sql` batches,
  complete-or-rejected statement results, the SQLite catalog listings and search, catalog
  failure mapping and owner isolation, and the three `run` composition requirements.
  `cott requirements` reports the same current statuses.
- `tests/support/harlequin_sessions.py` (the ignored
  `harlequin_live_transactions_preserve_physical_sessions` test) drives the public facades
  against real SQLite and DuckDB files, and against an ADBC SQLite driver when
  `COTT_ADBC_SQLITE_DRIVER` is set. It is external evidence, not Cott evidence, and does not
  change any requirement status.
- `tests/harlequin_program.rs` (ignored, labeled `external_program_regression`) deploys the
  verified snapshot and runs `harlequin_cli.py` in the Linux sandbox against scratch SQLite and
  DuckDB files: one-shot `--query-file` output, the interactive `sql>` loop, exit statuses, and
  rollback of an open transaction on disconnect. It passed on the verified example. Its
  companion test binds a type-valid `run` that exits without doing anything, in a throwaway
  copy only, and the regression rejects it. This is not Cott evidence, so the `run`
  requirements stay `unverified`. No regression exercises remote databases or S3.

## Run

```sh
project=examples/real/harlequin
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --no-config --adapter sqlite :memory:
```

The locked Python dependencies include PyArrow for ADBC's public metadata API. ODBC also
requires the system unixODBC runtime (`libodbc2` on Debian/Ubuntu) and a driver for the
selected data source. ADBC requires an explicitly named installed ADBC driver library or
manifest; the driver manager alone is not a database driver. Remote adapters require their
actual service endpoints and credentials.
