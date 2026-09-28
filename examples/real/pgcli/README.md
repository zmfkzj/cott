# https://github.com/dbcli/pgcli

Cott reimplementation of upstream pgcli **v4.7.1**, pinned to [`101e523eb2987ada87231c4533f0ab701c4c3124`](https://github.com/dbcli/pgcli/tree/101e523eb2987ada87231c4533f0ab701c4c3124). The contracts cover pgcli's CLI, PostgreSQL session, interactive prompt, configuration, completion, and output. The only authored Python adapter, `python/pgcli_cli.py`, passes `sys.argv` to the generated `real.pgcli.cli.run` facade. `pgcli` itself is **not** a dependency; the locked distributions include psycopg, pgspecial, prompt_toolkit, cli_helpers, tabulate, pygments, click, configobj, keyring, sshtunnel, sqlparse, tzlocal, and setproctitle.

## Modules

| Contract | Upstream counterpart |
| --- | --- |
| `real.pgcli.cli` | `main.cli`, `PGCli.__init__`, option parsing and launch |
| `real.pgcli.config` | `config.py`, pgclirc defaults/merge, logging |
| `real.pgcli.connection` | `PGExecute.connect/copy`, URI/service resolution, SSH tunnel, keyring, timezone |
| `real.pgcli.parseutils` | SQL tables, CTEs, keywords, quotes, destructive-command parsing |
| `real.pgcli.completion` | `pgcompleter`, `sqlcompletion`, prioritization and catalog refresh |
| `real.pgcli.output` | table/vertical/CSV/SQL/explain renderers, colours and timing |
| `real.pgcli.session` | SQL and pgspecial execution, named queries, special commands, routing, reconnect, watch |
| `real.pgcli.repl` | prompt_toolkit history, toolbar, key bindings, highlighting, vi and multiline modes |

`source_files`: `src/real/pgcli/cli.cott`, `completion.cott`, `config.cott`, `connection.cott`, `output.cott`, `parseutils.cott`, `repl.cott`, `session.cott` (each in `src/real/pgcli/`). `adapter_files`: `python/pgcli_cli.py`. All 85 callable implementations under `python/_cott_impl` and the facades under `generated/` were produced by `cott generate`, not hand-edited. Opaque connection/catalog/row handles keep large PostgreSQL results out of the facade's bounded ABI traversal.

## Parity evidence

| Feature family | Implemented / observation |
| --- | --- |
| CLI options, help, version, config and DSN | `--help`, `--version`, invalid options, `--list-dsn`, missing aliases, ping and `-l` matched upstream in 35-case side-by-side comparison; configuration and option scenarios passed `cott verify`. |
| Connection, transactions, metadata | External regression against scratch PostgreSQL 16.15 passed independent connection, reconnection, transaction, catalog and completion refresh checks. URI/service/local-timezone paths have contracts. |
| SSH tunnel | `database.ssh_tunnel` starts the host's own OpenSSH `sshd` (unprivileged, freshly generated host and user keys) on the sandbox's private loopback and runs `pgcli --ssh-tunnel user@127.0.0.1:22022 -h 127.0.0.1 …`: the query succeeds, sshd logs the accepted public key and the `direct-tcpip` channel to the database port, and an unreachable gateway exits 1 with `Could not establish session to SSH gateway`. Password-authenticated gateways, `~/.ssh/config`, `[ssh tunnels]`/`[dsn ssh tunnels]` matching and remote gateways are contract-only. |
| Keyring | `cli.keyring_without_backend` observes the no-backend path (keyring enabled, no Secret Service or KWallet inside the sandbox): upstream's exact red "Load your password from keyring returned: …" text on stderr, the query still runs, and `keyring = False` silences it. Loading and storing a password through a genuine keyring backend was **not** exercised (no backend or credentials exist for the test) and remains unobserved. |
| SQL and special commands | `-c`/`-f`, row limits, query errors, `\dt`, `\d`, `\h`, `\?`, `\copy`, `\T`, `\conninfo`, `\echo`, `\qecho`, `\v`, `\x`, `\timing`, named-query save/run/delete, `\o`, `\log-file`, includes, LISTEN/NOTIFY and quit were exercised by regression and/or comparison. |
| Watch, external editor, pager | Real PTY sessions: `cli.watch` repeats `SELECT 42 AS w \watch 1` until Ctrl-C, and a bare `\watch 1` repeats the last query; `cli.external_editor` runs `$EDITOR` for `\e` (last query) and `\ev view` and executes the edited text, the editor's input files being byte-identical to upstream's; `cli.pager` sends a 60-row result through `$PAGER` with `LESS=-SRXF` (byte-identical to upstream) while a short result stays on screen. |
| Output and completion | ASCII/grid/CSV/SQL-insert, vertical records, colours, explain formatting, completion and prioritization are generated from contracts and covered by representative Cott scenarios. Comparison matched upstream for output formats, NULL/numeric data, errors and row limits; the database regression checked actual metadata. |
| Interactive UI | Regression passed both piped interactive SQL/history and a real PTY completion/multiline session. A wide pyte-rendered PTY smoke additionally observed F2/F3/F4/F5 toolbar toggles, SQL result `SELECT 1`, and `Goodbye!`. |

The side-by-side comparison was **34/35 byte-identical cases** after normalizing elapsed times and notification PIDs. The sole deliberate difference: upstream pgcli crashes with `'NoneType' object has no attribute 'output'` for `-c '\\x on' -c 'select …'` because no prompt application exists in script mode. This implementation uses the real terminal width and displays the expanded result instead. Upstream does **not** register `\set`, `\password` or `\listen` as special commands: they are passed to PostgreSQL and yield its syntax errors, as observed in the comparison. Upstream packaging files are not reimplemented.

The IPython extension (`%load_ext pgcli.magic`, upstream `magic.py`) is part of upstream's user-visible surface but is **not implemented in this verified snapshot**: generating its line magic with the default OMP agent failed twice with the provider's `usage_limit_reached`, so neither its contracts nor its extension shell were published here. Upstream's extension was exercised for reference in a PTY against scratch PostgreSQL with IPython 9.17.1, ipython-sql 0.5.0, SQLAlchemy 2.1.1 and prettytable 3.11.0: it needs a `postgresql+psycopg://` URL (SQLAlchemy 2 rejects the documented `postgres://`) and prettytable below 3.12 (ipython-sql 0.5.0 reads `prettytable.__dict__["DEFAULT"]`, which 3.12+ removed).

## Build and verification

```sh
project=examples/real/pgcli
# Set this to your native PostgreSQL 16 bin directory when it is not on PATH.
export COTT_POSTGRES_BIN=/tmp/cott-pg/root/usr/lib/postgresql/16/bin
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott generate --agent omp --model openai-codex/gpt-6-sol --target python -j 4 --project "$project"
cott verify --project "$project"
cott requirements --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/pgcli_cli.py" --help
```

The current `generated/generation.json` snapshot is verified with `current == last_verified`, 85 bound implementations and zero unresolved symbols. `cott verify` reports **68 observed, 8 trust_declaration, 0 unknown and 0 unobserved** semantic clauses after legitimate `openai-codex/gpt-6-sol` generation. The three requirements remain `unverified` because they have no `checked_by` links; the external regression is separate evidence, not Cott scenario evidence. The external program regression in `tests/pgcli_program.rs` and `tests/support/pgcli_program.py` previously passed **13/13** checks against a scratch PostgreSQL 16 server using a verified deployment. Prerequisites of that ignored external regression test: `COTT_POSTGRES_BIN`, OpenSSH's `/usr/sbin/sshd` and `/usr/bin/ssh-keygen`, the locked `.venv`, and the compiler's Linux sandbox. A missing sshd fails `database.ssh_tunnel` (`openssh_missing`) instead of skipping it. The upstream comparison and pyte PTY drivers used for that historical verification remain in `/home/arthur/.cache/cott-real-drafts/pgcli/scripts/`.

The strict coverage policy selects 53 clauses across 27 callables, including
connection/reconnection, SQL execution and destructive-query confirmation,
configuration, completion, URI/service resolution and CLI/output boundaries.
No `unobserved`, `trust_declaration` or `unknown` is allowed. Real `verify` now
passes all 53 selected clauses (exit 0), resolving all 32 original violations.
The database scenarios use fresh compiler-owned PostgreSQL 16.15 clusters over
private Unix sockets, real facade-created connections, SQL/catalog operations,
injected database failures and actual SIGINT. They do not use ambient servers,
fake driver objects or external regression results as clause evidence.
The `VirtualDatabase` rejection scenario retains a live facade-created connection
and sets the public executor's caller-supplied flag. It tests that flag's guard,
not a PgBouncer server; the original connection is then pinged and closed.
`tools.postgresql_fixture` records the native version and frozen content hashes;
shutdown and scratch cleanup must succeed before any scenario is certified.
The PostgreSQL regression result above is historical and is not Cott scenario
evidence. Static proofs remain separate from execution coverage; selected
observations establish only the exercised invocation scope, not every path.
