# https://github.com/tconbeer/harlequin

A clean-room Cott reimplementation of a terminal SQL IDE. Its public boundary is generated from
`core`, `catalog`, and `render`; it does not depend on the upstream application
distribution.

The contracts model CLI configuration and profiles; descriptors for DuckDB,
SQLite, PostgreSQL, MySQL, ODBC, BigQuery, Trino, Databricks, ADBC, Cassandra,
and NebulaGraph; connections, transactions, editor tabs, history, SQL files,
and S3 references. They also cover bounded SQL execution, catalog refresh,
autocomplete and search, themes, keymaps, table and vertical views, and CSV,
TSV, JSON, Markdown, and SQL exports.

Implementations are generated from the contracts; the sole manifest-owned binding
is the interactive host boundary. The generated facade remains the only public
import path; `harlequin_cli.py` adapts process arguments to `real.harlequin.core.run`.

`core.connect` returns a live `Connection.session` handle, not a connection-id
registry entry. `execute_statements` borrows that retained SDK session.
`begin_transaction` returns its owning connection and a one-use opaque lease;
commit/rollback reject stale or wrong-owner leases. `disconnect` rolls back an
active transaction, closes owned resources, and is idempotent. The REPL keeps the
same connection across statements, including for `:memory:` databases.

`catalog.refresh_catalog` uses real temporary SDK connections and preserves the
requested scope. `src/real/harlequin/core.cott` documents each adapter's endpoint
format; `catalog.cott` defines namespace selection, table/view projection, overflow,
cleanup, and error behavior. It never substitutes an empty catalog for driver failure.
`catalog.find_catalog` searches the snapshot's relation names with case-folded
substring matching, stable order, and an explicit 1000-match request limit.
Catalog refresh remains an independent committed snapshot, not a view of the
owner's uncommitted transaction. Its fresh `:memory:` metadata connection therefore
does not share the retained session's tables.

The locked Python dependencies include PyArrow for ADBC's public metadata API.
ODBC also requires the system unixODBC runtime (`libodbc2` on Debian/Ubuntu) and
a driver for the selected data source. ADBC requires an explicitly named installed
ADBC driver library or manifest; the driver manager alone is not a database driver.
Remote adapters require their actual service endpoints and credentials.

## Run

```sh
project=examples/real/harlequin
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --adapter sqlite :memory:
```

The native regression exercises actual SQLite and DuckDB commit/rollback,
in-memory persistence, lease rejection and disconnect cleanup through public facades:

```sh
cargo test --test examples harlequin_live_transactions_preserve_physical_sessions -- --ignored
```

Set `COTT_ADBC_SQLITE_DRIVER` to an installed SQLite ADBC shared library to exercise
that driver in the same regression. No remote database or cloud service is implied
by these local smoke checks.
