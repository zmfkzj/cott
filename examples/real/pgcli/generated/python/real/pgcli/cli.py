from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.pgcli.cli_types import CliCommand, CliCommand_Launch, CliCommand_ShowHelp, CliError, CliError_Usage, CliOptions, PGCLI_HELP, PGCLI_VERSION, SetupEnvironment
from real.pgcli.config_types import PgcliConfig
from real.pgcli.session_types import SessionSettings

def parse_pgcli_arguments(arguments: CottList[str], environment: FrozenMap[str, str], default_pgclirc: str) -> Result[CliCommand, CliError]:
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
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    environment = _cott_validate_abi(environment, FrozenMap[str, str], path="$.environment")
    default_pgclirc = _cott_validate_abi(default_pgclirc, str, path="$.default_pgclirc")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/cli/parse_pgcli_arguments.py", "585f2552ac62ef7ea3358969ed43a06f1e6ced086d541421d6783d68ce626d86", "parse_pgcli_arguments", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.cli.parse_pgcli_arguments")
        _result = _implementation(arguments, environment, default_pgclirc)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.cli.parse_pgcli_arguments"
        if _error.span is None:
            _error.span = {"end_byte":7507,"end_column":1,"end_line":120,"start_byte":5092,"start_column":1,"start_line":77}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.cli.parse_pgcli_arguments", phase="implementation-call", span={"end_byte":7507,"end_column":1,"end_line":120,"start_byte":5092,"start_column":1,"start_line":77}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.cli.parse_pgcli_arguments", phase="implementation-call", span={"end_byte":7507,"end_column":1,"end_line":120,"start_byte":5092,"start_column":1,"start_line":77}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CliCommand, CliError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.cli.parse_pgcli_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CliError_Usage,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.cli.parse_pgcli_arguments", phase="error", span={"end_byte":7507,"end_column":1,"end_line":120,"start_byte":5092,"start_column":1,"start_line":77}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.cli.parse_pgcli_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.cli.parse_pgcli_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is CliError_Usage:
        _cott_contract_condition(True, "real.pgcli.cli.parse_pgcli_arguments", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is CliCommand_ShowHelp and True:
            text = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((text == PGCLI_HELP)), "real.pgcli.cli.parse_pgcli_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.cli.parse_pgcli_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.cli.parse_pgcli_arguments", clause="ensures:1", phase="ensures", span={"end_byte":7454,"end_column":71,"end_line":114,"start_byte":7388,"start_column":5,"start_line":114}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CliCommand, CliError], path="$.return", validator=_cott_validate_abi)
    return _result

def obfuscate_process_title(title: str) -> str:
    """obfuscate_process_password on a process title: when the title contains
"://", re.sub(r":(.*):(.*)@", r":\\1:xxxx@", title); else when it contains
"=", re.sub(r"password=(.+?)((\\s[a-zA-Z]+=)|$)", r"password=xxxx\\2",
title); otherwise unchanged."""
    title = _cott_validate_abi(title, str, path="$.title")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/cli/obfuscate_process_title.py", "e88aadc9cc498228e96cfb447622cd6ceb18553ddc3b6037c1b5df3379cc5f94", "obfuscate_process_title", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.cli.obfuscate_process_title")
        _result = _implementation(title)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.cli.obfuscate_process_title"
        if _error.span is None:
            _error.span = {"end_byte":7850,"end_column":1,"end_line":130,"start_byte":7507,"start_column":1,"start_line":120}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.cli.obfuscate_process_title", phase="implementation-call", span={"end_byte":7850,"end_column":1,"end_line":130,"start_byte":7507,"start_column":1,"start_line":120}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.cli.obfuscate_process_title", phase="implementation-call", span={"end_byte":7850,"end_column":1,"end_line":130,"start_byte":7507,"start_column":1,"start_line":120}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def session_settings_from(options: CliOptions, config: PgcliConfig, environment: SetupEnvironment) -> SessionSettings:
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
    options = _cott_validate_abi(options, CliOptions, path="$.options")
    config = _cott_validate_abi(config, PgcliConfig, path="$.config")
    environment = _cott_validate_abi(environment, SetupEnvironment, path="$.environment")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/cli/session_settings_from.py", "160545126ddb84d915aba188bdb38ac8936a82ab7016879c721ba59abc1752b3", "session_settings_from", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.cli.session_settings_from")
        _result = _implementation(options, config, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.cli.session_settings_from"
        if _error.span is None:
            _error.span = {"end_byte":9887,"end_column":1,"end_line":167,"start_byte":7850,"start_column":1,"start_line":130}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.cli.session_settings_from", phase="implementation-call", span={"end_byte":9887,"end_column":1,"end_line":167,"start_byte":7850,"start_column":1,"start_line":130}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.cli.session_settings_from", phase="implementation-call", span={"end_byte":9887,"end_column":1,"end_line":167,"start_byte":7850,"start_column":1,"start_line":130}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SessionSettings, path="$.return")
    if not (_cott_contract_condition((((_result).tuples_only == (options).tuples_only)), "real.pgcli.cli.session_settings_from", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.cli.session_settings_from", clause="ensures:1", phase="ensures", span={"end_byte":9803,"end_column":54,"end_line":162,"start_byte":9754,"start_column":5,"start_line":162}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).force_destructive == (options).force_destructive)), "real.pgcli.cli.session_settings_from", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.cli.session_settings_from", clause="ensures:2", phase="ensures", span={"end_byte":9869,"end_column":66,"end_line":163,"start_byte":9808,"start_column":5,"start_line":163}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SessionSettings, path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
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
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/cli/run.py", "446f9bb9b2b7cc3f2c0f1877665828f632380c922db22797e8730bebf0338fac", "run", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.cli.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.cli.run"
        if _error.span is None:
            _error.span = {"end_byte":16304,"end_column":1,"end_line":263,"start_byte":9887,"start_column":1,"start_line":167}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.cli.run", phase="implementation-call", span={"end_byte":16304,"end_column":1,"end_line":263,"start_byte":9887,"start_column":1,"start_line":167}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.pgcli.cli.run", phase="return", span={"end_byte":16304,"end_column":1,"end_line":263,"start_byte":9887,"start_column":1,"start_line":167}, expected="Never", actual=repr(_result))

__all__ = ["CliCommand", "CliCommand_Launch", "CliCommand_ShowHelp", "CliError", "CliError_Usage", "CliOptions", "PGCLI_HELP", "PGCLI_VERSION", "SetupEnvironment", "obfuscate_process_title", "parse_pgcli_arguments", "run", "session_settings_from"]
