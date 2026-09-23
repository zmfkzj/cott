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

Install the locked dependencies, generate the public facade, and explicitly verify it:

```sh
project=examples/real/pgcli
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/pgcli_cli.py" --help
```

The adapter forwards its arguments to the generated `run` facade. Connection and terminal behavior are
specified by `src/real/pgcli.cott`.

`run` is a line-oriented psycopg REPL with a positional DSN, `-h/--host`,
`-p/--port`, `-U/--username`, `-d/--dbname`, `-c/--command`, and `--help`.
The structured `connect` API additionally accepts the documented TLS and SSH plan;
an SSH hop requires an installed OpenSSH client and an existing trusted host key.
It never enables automatic host-key acceptance.

History and favorites use this client's documented UTF-8 JSON formats, not upstream
pgcli's history/configuration files. Credential resolution prefers supplied input,
then the supplied environment value, then the locked `keyring` SDK, then a hidden
terminal prompt. `no_prompt` prohibits terminal input, and lookup never writes a
credential. A system keyring backend must be available when keyring lookup is used.
