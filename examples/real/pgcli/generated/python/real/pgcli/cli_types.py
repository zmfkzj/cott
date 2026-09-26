from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.pgcli.config_types import PgcliConfig
from real.pgcli.session_types import SessionSettings

PGCLI_VERSION: Final[str] = "4.7.1"

"""Exactly what upstream pgcli 4.7.1 prints for --help on an 80-column terminal
(click 8 help formatting), including the final line feed."""
PGCLI_HELP: Final[str] = "Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]\n\nOptions:\n  -h, --host TEXT          Host address of the postgres database.\n  -p, --port INTEGER       Port number at which the postgres instance is\n                           listening.\n  -U, --username TEXT      Username to connect to the postgres database.\n  -u, --user TEXT          Username to connect to the postgres database.\n  --timeout INTEGER        Seconds to wait for a connection before giving up\n                           (0 waits forever). Overrides the connection string\n                           and $PGCONNECT_TIMEOUT.\n  -W, --password           Force password prompt.\n  -w, --no-password        Never prompt for password.\n  --single-connection      Do not use a separate connection for completions.\n  -v, --version            Version of pgcli.\n  -d, --dbname TEXT        database name to connect to.\n  --pgclirc FILE           Location of pgclirc file.\n  -D, --dsn TEXT           Use DSN configured into the [alias_dsn] section of\n                           pgclirc file.\n  --list-dsn               list of DSN configured into the [alias_dsn] section\n                           of pgclirc file.\n  --row-limit INTEGER      Set threshold for row limit prompt. Use 0 to\n                           disable prompt.\n  --application-name TEXT  Application name for the connection.\n  --less-chatty            Skip intro on startup and goodbye on exit.\n  -t, --tuples-only        Print rows only: no column headers, no status\n                           footer and no timing, like psql.\n  --prompt TEXT            Prompt format (Default: \"\\u@\\h:\\d> \").\n  --prompt-dsn TEXT        Prompt format for connections using DSN aliases\n                           (Default: \"\\u@\\h:\\d> \").\n  -l, --list               list available databases, then exit.\n  --ping                   Check database connectivity, then exit.\n  --auto-vertical-output   Automatically switch to vertical output mode if the\n                           result is wider than the terminal width.\n  --warn TEXT              Warn before running a destructive query.\n  --ssh-tunnel TEXT        Open an SSH tunnel to the given address and connect\n                           to the database from it.\n  --log-file TEXT          Write all queries & output into a file, in addition\n                           to the normal output destination.\n  --init-command TEXT      SQL statement to execute after connecting.\n  -c, --command TEXT       run command (SQL or internal) and exit. Multiple -c\n                           options are allowed.\n  -y, --yes                Force destructive commands without confirmation\n                           prompt.\n  -f, --file FILE          execute commands from file, then exit. Multiple -f\n                           options are allowed.\n  --help                   Show this message and exit.\n"

"""The parsed command line of upstream cli(). Option-valued fields are Nothing
when neither the option nor its environment fallback was given.
port is -p/--port ($PGPORT), default 5432. pgclirc is --pgclirc ($PGCLIRC),
default config directory + "config". dsn is -D/--dsn ($DSN), default "".
row_limit is --row-limit ($PGROWLIMIT). application_name is
--application-name ($PGAPPNAME), default "pgcli". dbname and username are the
two optional positional arguments with $PGDATABASE and $PGUSER fallbacks.
commands (-c, repeatable) and files (-f, repeatable) keep command-line order."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliOptions:
    __hash__ = None
    host: str
    port: I64
    username_option: Option[str]
    timeout: Option[I64]
    force_password_prompt: bool
    never_password_prompt: bool
    single_connection: bool
    version: bool
    dbname_option: Option[str]
    pgclirc: str
    dsn: str
    list_dsn: bool
    row_limit: Option[I64]
    application_name: str
    less_chatty: bool
    tuples_only: bool
    prompt: Option[str]
    prompt_dsn: Option[str]
    list_databases: bool
    ping: bool
    auto_vertical_output: bool
    warn: Option[str]
    ssh_tunnel: Option[str]
    log_file: Option[str]
    init_command: Option[str]
    commands: CottList[str]
    force_destructive: bool
    files: CottList[str]
    dbname: Option[str]
    username: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, I64, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "username_option", _cott_validate_abi(self.username_option, Option[str], path="$.username_option"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timeout", _cott_validate_abi(self.timeout, Option[I64], path="$.timeout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_password_prompt", _cott_validate_abi(self.force_password_prompt, bool, path="$.force_password_prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "never_password_prompt", _cott_validate_abi(self.never_password_prompt, bool, path="$.never_password_prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "single_connection", _cott_validate_abi(self.single_connection, bool, path="$.single_connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "version", _cott_validate_abi(self.version, bool, path="$.version"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dbname_option", _cott_validate_abi(self.dbname_option, Option[str], path="$.dbname_option"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pgclirc", _cott_validate_abi(self.pgclirc, str, path="$.pgclirc"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn", _cott_validate_abi(self.dsn, str, path="$.dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "list_dsn", _cott_validate_abi(self.list_dsn, bool, path="$.list_dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "row_limit", _cott_validate_abi(self.row_limit, Option[I64], path="$.row_limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "application_name", _cott_validate_abi(self.application_name, str, path="$.application_name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "less_chatty", _cott_validate_abi(self.less_chatty, bool, path="$.less_chatty"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tuples_only", _cott_validate_abi(self.tuples_only, bool, path="$.tuples_only"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt", _cott_validate_abi(self.prompt, Option[str], path="$.prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt_dsn", _cott_validate_abi(self.prompt_dsn, Option[str], path="$.prompt_dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "list_databases", _cott_validate_abi(self.list_databases, bool, path="$.list_databases"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ping", _cott_validate_abi(self.ping, bool, path="$.ping"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_vertical_output", _cott_validate_abi(self.auto_vertical_output, bool, path="$.auto_vertical_output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "warn", _cott_validate_abi(self.warn, Option[str], path="$.warn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh_tunnel", _cott_validate_abi(self.ssh_tunnel, Option[str], path="$.ssh_tunnel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "log_file", _cott_validate_abi(self.log_file, Option[str], path="$.log_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "init_command", _cott_validate_abi(self.init_command, Option[str], path="$.init_command"))
        if not _cott_validated_construction():
            object.__setattr__(self, "commands", _cott_validate_abi(self.commands, CottList[str], path="$.commands"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_destructive", _cott_validate_abi(self.force_destructive, bool, path="$.force_destructive"))
        if not _cott_validated_construction():
            object.__setattr__(self, "files", _cott_validate_abi(self.files, CottList[str], path="$.files"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dbname", _cott_validate_abi(self.dbname, Option[str], path="$.dbname"))
        if not _cott_validated_construction():
            object.__setattr__(self, "username", _cott_validate_abi(self.username, Option[str], path="$.username"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliCommand_ShowHelp:
    __hash__ = None
    text: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliCommand_Launch:
    __hash__ = None
    options: CliOptions

CliCommand: TypeAlias = Union[CliCommand_ShowHelp, CliCommand_Launch]

"""A click usage error: text is everything click prints on standard error for
it, for example "Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]\\nTry 'pgcli
--help' for help.\\n\\nError: No such option '--bogus'. (Did you mean one of:
'--host', '--user'?)\\n". The process exits 2."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliError_Usage:
    __hash__ = None
    text: str

CliError: TypeAlias = Union[CliError_Usage]

"""Process environment values read by session setup."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SetupEnvironment:
    __hash__ = None
    home: str
    colorterm: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "home", _cott_validate_abi(self.home, str, path="$.home"))
        if not _cott_validated_construction():
            object.__setattr__(self, "colorterm", _cott_validate_abi(self.colorterm, str, path="$.colorterm"))

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
"""obfuscate_process_password on a process title: when the title contains
"://", re.sub(r":(.*):(.*)@", r":\\1:xxxx@", title); else when it contains
"=", re.sub(r"password=(.+?)((\\s[a-zA-Z]+=)|$)", r"password=xxxx\\2",
title); otherwise unchanged."""
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
__all__ = ["CliCommand", "CliCommand_Launch", "CliCommand_ShowHelp", "CliError", "CliError_Usage", "CliOptions", "PGCLI_HELP", "PGCLI_VERSION", "SetupEnvironment"]
