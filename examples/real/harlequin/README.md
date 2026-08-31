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

The restored host implementations provide the deterministic SQLite statement,
execution, catalog, and table-rendering leaves. The generated facade remains
the only public import path; `harlequin_cli.py` only adapts process arguments
to `real.harlequin.core.run`.

## Run

```sh
project=examples/real/harlequin
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --adapter sqlite :memory:
```
