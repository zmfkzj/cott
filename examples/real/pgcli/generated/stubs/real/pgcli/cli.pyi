from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.cli_types import CliCommand as CliCommand, CliCommand_Launch as CliCommand_Launch, CliCommand_ShowHelp as CliCommand_ShowHelp, CliError as CliError, CliError_Usage as CliError_Usage, CliOptions as CliOptions, PGCLI_HELP as PGCLI_HELP, PGCLI_VERSION as PGCLI_VERSION, SetupEnvironment as SetupEnvironment
from real.pgcli.config_types import PgcliConfig
from real.pgcli.session_types import SessionSettings
"""Parse arguments (without the program name) exactly as upstream's click
command "pgcli" does, using the lock-selected click to build and parse the
command so option syntax, clustering, "--opt=value", "--", error texts and
"Did you mean" suggestions match click. Parameters in declaration order:
-h/--host TEXT (default "", env PGHOST, "Host address of the postgres
database."); -p/--port INTEGER (default 5432, env PGPORT); -U/--username
TEXT and -u/--user TEXT (both set username_option); --timeout INTEGER;
-W/--password flag; -w/--no-password flag; --single-connection flag;
-v/--version flag; -d/--dbname TEXT; --pgclirc FILE (click.Path(dir_okay=
False), default default_pgclirc, env PGCLIRC); -D/--dsn TEXT (default "",
env DSN); --list-dsn flag; --row-limit INTEGER (env PGROWLIMIT);
--application-name TEXT (default "pgcli", env PGAPPNAME); --less-chatty
flag; -t/--tuples-only flag; --prompt TEXT; --prompt-dsn TEXT; -l/--list
flag; --ping flag; --auto-vertical-output flag; --warn TEXT; --ssh-tunnel
TEXT; --log-file TEXT; --init-command TEXT; -c/--command TEXT (multiple);
-y/--yes flag; -f/--file FILE (multiple, click.Path(exists=True,
readable=True, dir_okay=False)); arguments DBNAME (env PGDATABASE) and
USERNAME (env PGUSER), each optional (nargs=1, default None). Help texts
are those of PGCLI_HELP. Environment fallbacks come only from the given
environment map (never from os.environ); a fallback value is converted and
validated like a command-line value.
--help anywhere (processed eagerly like click's help option, before other
value conversion) gives ShowHelp(PGCLI_HELP). Every click UsageError
(unknown option, missing option value, bad integer, missing -f file,
extra argument) gives Usage(text) with the exact text click's standalone
mode writes: "Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]\\nTry 'pgcli
--help' for help.\\n\\nError: " + message + "\\n" (click omits the usage
lines for some errors, e.g. "Error: Option '-p' requires an argument.\\n";
reproduce whatever click 8 prints)."""
def parse_pgcli_arguments(arguments: CottList[str], environment: FrozenMap[str, str], default_pgclirc: str) -> Result[CliCommand, CliError]: ...

"""obfuscate_process_password on a process title: when the title contains
"://", re.sub(r":(.*):(.*)@", r":\\1:xxxx@", title); else when it contains
"=", re.sub(r"password=(.+?)((\\s[a-zA-Z]+=)|$)", r"password=xxxx\\2",
title); otherwise unchanged."""
def obfuscate_process_title(title: str) -> str: ...

"""PGCli.__init__'s settings: table_format = config table_format;
expanded_output = [main] expand; auto_expand = --auto-vertical-output or
[main] auto_expand; multi_line, multiline_mode (multi_line_mode), vi_mode
(vi), smart_completion, hide_named_query_text, verbose_errors from [main];
explain_mode false; output_file Nothing; log_file = Some(--log-file) when
given else Nothing; row_limit = --row-limit when given else [main]
row_limit; max_field_width, null_string, on_error from [main];
destructive_warning = real.pgcli.parseutils.parse_destructive_warning of
--warn when given (a --warn value containing "," is split on "," and used
as is without mapping; otherwise the one-item list) else of [main]
destructive_warning; destructive_warning_restarts_connection,
destructive_statements_require_transaction, auto_retry_closed_connection
from [main]; force_destructive = -y; tuples_only = -t; less_chatty =
--less-chatty or [main] less_chatty; decimal_format and float_format from
[data_formats]; column_date_formats from [column_date_formats];
case_column_headers from [main]; output_style = Some(OutputStyle with
header/odd_row/even_row/null from the [colors] keys output.header,
output.odd-row, output.even-row, output.null ("" when absent), base = the
Token style of pygments.styles.get_style_by_name(syntax_style) ("native"
when unknown), table_separator = [colors] Token.Output.TableSeparator or
"", true_color = "truecolor" in environment.colorterm lower-cased));
prompt_format = --prompt when given else [main] prompt; prompt_dsn_format =
--prompt-dsn; dsn_alias Nothing; scripted = commands or files were given;
completion_refreshing false."""
def session_settings_from(options: CliOptions, config: PgcliConfig, environment: SetupEnvironment) -> SessionSettings: ...

"""The pgcli command (upstream cli() and PGCli), arguments without the program
name. Everything printed in red/green/yellow uses click.secho with that fg
colour; "stderr" means err=True.
1. environment = os.environ. config directory =
real.pgcli.config.pgcli_config_directory(XDG_CONFIG_HOME when set, the
home directory). Parse with real.pgcli.cli.parse_pgcli_arguments(arguments,
environment, directory + "config"). Usage(text): write text to stderr, exit
2. ShowHelp(text): write text to stdout, exit 0.
2. -v: print "Version: 4.7.1", exit 0.
3. Create the config directory (without its trailing "/") when missing.
When ~/.pgclirc exists: move it to directory + "config" and print "Config
file (~/.pgclirc) moved to new location <path>" when that file does not
exist, else print "Config file is now located at <path>" and "Please move
the existing config file ~/.pgclirc to <path>".
4. --list-dsn: when the --pgclirc file does not exist exit 0 without
output; otherwise read it with configobj (interpolation=False, UTF-8) and
print "<alias> : <dsn>" for each [alias_dsn] entry, exit 0. A valid
config without an [alias_dsn] section has zero entries and exits 0
without output, not an error. A malformed [alias_dsn] section or any
read/parse failure prints in red on stderr 'Invalid DSNs found in the
config file. Please check the "[alias_dsn]" section in pgclirc.' and exits 1.
5. config = real.pgcli.config.load_pgcli_config(--pgclirc path); an error
prints its message in red on stderr and exits 1.
real.pgcli.config.configure_pgcli_logging([main] log_file, log_level,
directory). Pager: when [main] pager is nonempty set os.environ PAGER to it
(log 'Default pager found in config file: "<pager>"'), else keep PAGER
(log 'Default pager found in PAGER environment variable: "<pager>"' when
set, else log "No default pager found in environment. Using os default
pager"); set LESS to "-SRXF" when LESS is unset or empty. When
--log-file is given open it in "a+" mode once (an OSError prints in red on
stderr and exits 1). settings =
real.pgcli.cli.session_settings_from(options, config, SetupEnvironment(
home, COLORTERM or "")). special =
real.pgcli.session.create_special_handle(SpecialSetup(timing = [main]
timing and not -t, enable_pager, the --pgclirc path)).
6. Target: real.pgcli.connection.select_connect_target(TargetRequest(
-d, DBNAME, -U/-u, USERNAME, host, str(port), PGSERVICE when set, -l or
--ping, -D, [alias_dsn])); AliasMissing prints in red on stderr 'Could not
find a DSN with alias <name>. Please check the "[alias_dsn]" section in
pgclirc.' and exits 1. Alias(name, uri): dsn_alias = name and the spec is
real.pgcli.connection.connection_spec_from_uri(uri); Uri(uri): the same
without alias; Conninfo(dsn, user): spec(dsn, user); Service(service,
user): real.pgcli.connection.lookup_pg_service(service, PGSERVICEFILE,
PGSYSCONFDIR, home) gives dbname, host, user (the given user wins), port and
password; ServiceMissing prints in red on stderr "service '<service>' was
not found in <file>" and exits 1; Params(database, host, user, port): that
spec. Then real.pgcli.connection.open_executor(OpenRequest(spec,
application_name, -W, -w, [main] keyring, --timeout, [main]
connect_timeout, PGPASSWORD or "", PGCONNECT_TIMEOUT or "", dsn_alias,
--ssh-tunnel, [dsn ssh tunnels], [ssh tunnels])); a failure prints the
message in red on stderr and exits 1.
7. When [main] use_local_timezone: real.pgcli.connection.apply_local_timezone.
8. Init commands: every [init-commands] entry's commands in order, then
with a DSN alias the [alias_dsn.init-commands] entry named like the alias,
then --init-command. When there are any, print "Running init commands: " +
"; ".join(commands) and run them with
real.pgcli.session.run_init_commands; a failure prints in red on stderr and
exits 1.
9. -l: print the text of real.pgcli.session.database_listing and exit 0
(errors print in red on stderr, exit 1). --ping: print
"PONG" and exit 0 when real.pgcli.session.ping_database, else print in red
on stderr "Could not connect to the database. Please check that the
database is running." and exit 1.
10. Replace the process title (setproctitle) by
real.pgcli.cli.obfuscate_process_title of the current title.
11. -c commands, in order, each through real.pgcli.session.run_script_text
with TerminalSize from shutil.get_terminal_size() (upstream has no prompt
application in this mode and fails with "'NoneType' object has no
attribute 'output'" whenever auto-expand is on; this client uses the real
terminal size instead)
(stop at the first command whose run is not ok); a quit exits 0; any other
exception prints in red on stderr and exits 1. Without -f files exit 0.
Then each -f file in order: read it as UTF-8; when its content is not blank
run it through run_script_text, stopping at the first not-ok run; a quit
exits 0; exceptions print in red on stderr and exit 1; then exit 0.
12. Otherwise run real.pgcli.repl.run_pgcli_repl(Session(settings with
dsn_alias, executor, special,
real.pgcli.completion.empty_completion_catalog(), ""), ReplSettings(syntax_style, colors,
show_bottom_toolbar, wider_completion_menu, min_num_menu_lines,
multiline_continuation_char, auto_suggest, the history path (directory +
"history" when [main] history_file is "default", else the value with "~"
expanded), --single-connection or always_use_single_connection, completer
settings from [main] (keyword_casing, qualify_columns,
asterisk_column_order, search_path_filter, generate_aliases and the alias
map loaded with real.pgcli.completion.load_alias_map from alias_map_file
when nonempty, whose error prints in red on stderr and exits 1), refresh
settings (casing file = directory + "casing" when [main] casing_file is
"default", generate_casing_file))) and exit 0 when it returns.
Ctrl-C outside the prompt loop exits 1 after Python's usual
KeyboardInterrupt message is suppressed; a password is never printed."""
def run(arguments: CottList[str]) -> Never: ...

__all__ = ["CliCommand", "CliCommand_Launch", "CliCommand_ShowHelp", "CliError", "CliError_Usage", "CliOptions", "PGCLI_HELP", "PGCLI_VERSION", "SetupEnvironment", "obfuscate_process_title", "parse_pgcli_arguments", "run", "session_settings_from"]
