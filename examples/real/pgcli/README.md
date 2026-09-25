# https://github.com/dbcli/pgcli

A clean-room Cott reimplementation of a line-oriented PostgreSQL client in the spirit of pgcli, with no upstream dependency.

It does not reimplement pgcli's prompt_toolkit interface (completion and highlighting while typing, key
bindings, toolbars), its configuration file, sessions through SSH tunnels, or these meta commands, which
parse as unknown and are rejected: `\!`, `\log-file`, `\o`, `\set`, `\v`, `\password`, `\listen` and
`\watch`.

## Program

`src/real/pgcli.cott` is the whole specification.

- `run` is the CLI. It parses arguments with `parse_arguments` (`[DSN]`, `-h/--host`, `-p/--port`,
  `-U/--username`, `-d/--dbname`, `-c/--command`, `--help`; no password argument), resolves the connection
  with `resolve_connection_plan` over the `PG*` environment values, and runs `run_interactive`. The CLI
  disables history and favorites persistence.
- `run_interactive` is the session. `ExecuteOnce` (`-c`) submits one text without reading the terminal;
  `Interactive` refreshes the catalog and reads standard input line by line. Every submission goes through
  `run_meta_command`, SQL through its `ExecuteBuffer` command, which calls `plan_query`,
  `execute_planned_query` and `format_query`. Output goes through `page_output`, and SQL submissions are
  recorded with `remember_history` and `save_history` when a history policy is set. The session reports how
  many submissions ran and failed; `run` exits 0 only when none failed.
- `run_meta_command` executes one parsed backslash command and returns the updated buffer, session options
  and catalog. Its contract names the facade behind each command (`connect`, `refresh_catalog`,
  `execute_planned_query`, `import_delimited`, `export_query`, `edit_in_editor`, `load_history`,
  `load_favorites`, `save_favorites`).
- Every database operation opens its own connection, so a `Manual` transaction spans one submission, not the
  session. Only the `connect` probe reaches PostgreSQL through an SSH jump host; the other database
  operations reject SSH plans with `TunnelUnsupported`.
- The line REPL does not use these library facades: `complete_catalog_sql`, `complete_sql`, `highlight_sql`,
  `resolve_credential` (supplied, environment, keyring, then one hidden prompt that never falls back to echoed
  input), `prompt_policy`, the pure transaction-state functions, `execute_query`, `watch_query` and
  `receive_notifications`.
- History and favorites use this client's own UTF-8 JSON formats, not upstream pgcli's files.

## Run

Install the locked dependencies, generate the public facades, and verify them:

```sh
project=examples/real/pgcli
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/pgcli_cli.py" --help
```

`python/pgcli_cli.py` forwards its arguments to the generated `run` facade.

## Evidence

`cott verify` certified the current snapshot for Python. It passed the BasedPyright check, the runtime checks
and all 19 scenarios. Semantic coverage records 71 observed clauses, 49 `trust_declaration`, 31 `unknown` and
2 `unobserved`, with no clause policy-gated. That is evidence for this snapshot, not a claim that the client
is correct.

- Formally specified: result relations for the pure leaves (field precedence in `resolve_connection` and
  `resolve_connection_plan`, credential precedence, completion and truncation bounds, transaction-state
  transitions), conditional errors for failures decidable from inputs (missing database, invalid SSH hop,
  disabled prompt, blank, duplicate or excess favorites, delimiter and format checks, SSH plans on database
  operations, unknown meta commands), `errors complete` on `prompt_policy` and the transaction functions,
  and invariants on `InputBuffer`, `CompletionRequest` and `SessionReport`.
- 19 scenarios observe the pure leaves and the file leaves: connection-string parsing, profile lookup,
  connection layering, argument parsing, credential precedence without keyring or terminal access,
  completion, highlighting, statement planning, buffer editing, meta-command parsing, exact table, CSV and
  auto-expanded output, history normalization, history and favorites round trips, validation, and a failed
  replace that keeps the previous file. The file scenarios run through the compiler's fixture file adapters,
  not host file I/O.
- Four requirements are linked to those scenarios, and both `cott verify` and `cott requirements` report them
  `observed`: error messages omit connection-string secrets and argument values, and a failed history or
  favorites save keeps the previous file. The other 19 requirements are `unverified`.
- Unverified: database, terminal, editor and pager effects have no fixture backend, so their clauses stay
  `trust_declaration` or `unknown`, and these requirements stay `unverified`: `CONNECT_RELEASES_RESOURCES`,
  `CONNECT_KEEPS_PEER_CHECKS`, `CONNECT_ERRORS_OMIT_SECRETS`, `EXECUTE_QUERY_RETURNS_SERVER_ROWS`,
  `PLANNED_QUERY_HONORS_TRANSACTION_MODE`, `WATCH_REPEATS_THROUGH_EXECUTE`, `CATALOG_REFLECTS_SERVER`,
  `IMPORT_IS_ALL_OR_NOTHING`, `EXPORT_REPLACES_ATOMICALLY`, `NOTIFICATIONS_ARE_DELIVERED`,
  `EDITOR_RETURNS_EDITED_TEXT`, `PAGER_SHOWS_TEXT`, `CREDENTIAL_INPUT_STAYS_HIDDEN`,
  `META_COMMANDS_USE_FACADES`, `META_OUTPUT_OMITS_PASSWORD`, `SESSION_COMPOSES_STAGES`,
  `SESSION_EXECUTE_ONCE_SKIPS_TERMINAL`, `SESSION_REPORT_COUNTS_SUBMISSIONS` and `RUN_IS_THIN`.
- `tests/pgcli_program.rs` is a labeled `external_program_regression`, not Cott evidence, and it does not change
  any requirement status. The test is `#[ignore]`d and needs `COTT_POSTGRES_BIN` pointing at PostgreSQL
  binaries. It deploys the verified project and starts a scratch PostgreSQL server on a Unix socket inside
  the Linux sandbox. It checks, using the real generated facades:
  - the `connect` receipt (database, user, server version 16.x);
  - `Manual` commit and `ReadOnly` rollback through `execute_planned_query`;
  - a created table appearing in `refresh_catalog`;
  - `import_delimited` and `export_query` receipts, their row limits, and that a refused export leaves the
    previous file;
  - `receive_notifications` delivery;
  - the CLI exit codes for `--help`, an invalid option, a successful query and a failing query;
  - an interactive session running SQL and `\refresh`.

  A companion test binds a type-valid `run` that exits 0 without doing anything, in a throwaway copy, and the
  regression rejects it. The regression passed against PostgreSQL 16.15. It does not cover the SSH, editor,
  pager or keyring paths.
