# https://github.com/tconbeer/harlequin

This is a clean-room Cott reimplementation of a bounded SQLite terminal SQL-client core.
The upstream project is licensed under [MIT](https://github.com/tconbeer/harlequin/blob/v2.12.0/LICENSE).

## Supported behavior

This project selects either an in-memory database by default or one SQLite file path. It splits
semicolon-delimited SQL without splitting inside strings, quoted identifiers, or comments; executes
statements in order with `sqlite3`; and returns typed cells, rows, and closed typed failures. Read-only
queries permit `EXPLAIN`, `PRAGMA`, `SELECT`, `VALUES`, and read-only `WITH` statements while rejecting
all mutations, including mutations hidden inside a `WITH` statement. It inspects main-schema user tables
and views, their columns, and case-insensitive literal name matches. Query and catalog results
render as deterministic left-aligned ASCII grids. The headless CLI exposes `query`, `catalog relations`,
`catalog columns`, and `search` through generated public Cott facades.

## Run

From the repository root, create the project-local environment, generate the Cott Python facades, and run:

```sh
project=examples/real/harlequin
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
"$project/.venv/bin/python" -c 'import sqlite3; db = sqlite3.connect("examples/real/harlequin/sample.db"); db.execute("create table users (id integer primary key, name text)"); db.execute("insert into users (name) values ('\''Ada'\'')"); db.commit()'
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" query "select 1 as answer; select 'ok' as status"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --database "$project/sample.db" catalog relations
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --database "$project/sample.db" catalog columns users
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --database "$project/sample.db" search user
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/harlequin_cli.py" --read-only query "delete from users"
```
