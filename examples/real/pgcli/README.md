# https://github.com/dbcli/pgcli

A clean-room Cott reimplementation of an interactive PostgreSQL client with no upstream dependency.

## Features

- DSNs, named profiles, environment values, TLS, SSH tunnelling, and keyring or prompt password policy.
- Refreshed database catalogs, context-aware completion, SQL highlighting, and multiline editing.
- Database, schema, relation, routine, role, extension, publication, and subscription meta commands.
- Query history, favorites, transaction modes, timing, watch execution, editor and pager output.
- Deterministic aligned, vertical, CSV, TSV, JSON, JSON Lines, HTML, LaTeX, and Markdown results.
- Delimited import, query export, and bounded PostgreSQL notification consumption.

## Run

Generate the public facade and lock dependencies through the Cott orchestrator, then run:

```sh
project=examples/real/pgcli
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/pgcli_cli.py" --help
```

The adapter forwards its arguments to the generated `run` facade. Connection and terminal behavior are
specified by `src/real/pgcli.cott`.
