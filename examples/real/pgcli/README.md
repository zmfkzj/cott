# https://github.com/dbcli/pgcli

This is a clean-room Cott reimplementation; it does not reuse upstream source, tests, or prose.

Upstream license: [BSD-3-Clause](https://github.com/dbcli/pgcli/blob/main/LICENSE.txt).

## Bounded behavior

This project supports only:

- explicit `host`, `port`, `user`, `password`, and `database` values overriding `PGHOST`,
  `PGPORT`, `PGUSER`, `PGPASSWORD`, and `PGDATABASE` respectively;
- an explicit no-password policy that rejects an absent password instead of prompting;
- deterministic SQL-name completion from `--table [schema.]table:column,...` catalog entries;
- deterministic horizontal or vertical text rendering from supplied column names, text cells, and width;
- recognition of `\\q`, `\\?`, `\\dt`, and `\\d`; and
- synchronous Psycopg query execution, including result rows or an affected-row status.

It does not provide an interactive terminal UI, SQL parsing beyond the declared completion context,
connection profiles, query history, configuration files, or upstream compatibility behavior.

## Run

Generate the public facade and lock dependencies through the Cott orchestrator, then run:

```sh
project=examples/real/pgcli
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/pgcli_cli.py" complete 'select * from us' --table public.users:id,name
PGDATABASE=postgres PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/pgcli_cli.py" query --sql 'select 1'
```

Use `--host`, `--port`, `--user`, `--password`, or `--database` to override the corresponding
PostgreSQL environment value. Add `--no-password` to refuse a prompt, and `--vertical` or `--width`
to select rendering.
