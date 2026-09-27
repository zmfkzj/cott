from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_starts_with

from real.harlequin.cli_types import CliArguments, CliError, CliError_Usage, FirstPass, HARLEQUIN_VERSION, HarlequinSettings, SshSettings
from real.harlequin.adapters_types import AdapterDescriptor, AdapterKind, AdapterOption, ConnectionRequest
from real.harlequin.config_types import ConfigEntry, ConfigError, ConfigError_Invalid, Profile

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def first_pass(arguments: CottList[str]) -> FirstPass:
    """Scan raw arguments (without the program name) up to a "--": -a NAME,
-aNAME, --adapter NAME and --adapter=NAME set adapter (last wins, lower
cased); -P NAME, -PNAME, --profile NAME and --profile=NAME set profile;
--config-path PATH and --config-path=PATH set config_path; --help,
--version, --config and --keys set the corresponding wants flags. A value
option at the very end without a value sets nothing. Nothing else is
interpreted."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/cli/first_pass.py", "113a99d7c182e74f061e81a38bbbd0118e9f335b3feda2fbe157e69e7cb2255b", "first_pass", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.cli.first_pass")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.cli.first_pass"
        if _error.span is None:
            _error.span = {"end_byte":2754,"end_column":1,"end_line":91,"start_byte":2203,"start_column":1,"start_line":78}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.cli.first_pass", phase="implementation-call", span={"end_byte":2754,"end_column":1,"end_line":91,"start_byte":2203,"start_column":1,"start_line":78}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.cli.first_pass", phase="implementation-call", span={"end_byte":2754,"end_column":1,"end_line":91,"start_byte":2203,"start_column":1,"start_line":78}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FirstPass, path="$.return")
    _result = _cott_wrap_async_protocol(_result, FirstPass, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def harlequin_option_names() -> CottList[str]:
    """The profile keys the harlequin command itself owns, in this order: adapter,
conn_str, keymap_name, limit, locale, no_download_tzdata, no_write_history,
output, read_only, show_files, show_s3, ssh_allow_reuse, ssh_batch_mode,
ssh_forward, ssh_host, ssh_timeout, theme, viewer_max_rows."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/cli/harlequin_option_names.py", "eb9119f946e4ad42f40ac0bb2310077e8043234725b6b301fe96aa7d2d1320e4", "harlequin_option_names", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.cli.harlequin_option_names")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.cli.harlequin_option_names"
        if _error.span is None:
            _error.span = {"end_byte":3164,"end_column":1,"end_line":103,"start_byte":2754,"start_column":1,"start_line":91}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.cli.harlequin_option_names", phase="implementation-call", span={"end_byte":3164,"end_column":1,"end_line":103,"start_byte":2754,"start_column":1,"start_line":91}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.cli.harlequin_option_names", phase="implementation-call", span={"end_byte":3164,"end_column":1,"end_line":103,"start_byte":2754,"start_column":1,"start_line":91}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 18)), "real.harlequin.cli.harlequin_option_names", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.cli.harlequin_option_names", clause="ensures:1", phase="ensures", span={"end_byte":3146,"end_column":29,"end_line":99,"start_byte":3122,"start_column":5,"start_line":99}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def parse_harlequin_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[CliArguments, CliError]:
    """Parse the harlequin command line like Harlequin's click command.
Core options (spellings | profile key | kind):
-P/--profile TEXT (not a profile key: sets profile) ;
--config-path PATH (sets config_path) ; -t/--theme TEXT | theme | Text ;
--viewer-max-rows INTEGER | viewer_max_rows | Integer, must be >= -1 ;
--limit INTEGER | limit | Integer, >= -1 ; -o/--output PATH | output | Text ;
-a/--adapter NAME | adapter | Text, must be one of adapter_names ignoring case
(stored lower case) ; --no-write-history | no_write_history | flag ;
-r/--read-only | read_only | flag ; -f/--show-files DIRECTORY | show_files |
Text ; --show-s3/--s3 TEXT | show_s3 | Text ; --keymap-name TEXT (repeatable)
| keymap_name | Array ; --ssh-host TEXT | ssh_host | Text ; --ssh-forward TEXT
(repeatable) | ssh_forward | Array ; --ssh-batch-mode | ssh_batch_mode | flag ;
--ssh-allow-reuse | ssh_allow_reuse | flag ; --ssh-timeout FLOAT |
ssh_timeout | Real, must be > 0 ; --locale TEXT | locale | Text ;
--no-download-tzdata | no_download_tzdata | flag ; --config (run the config
wizard) ; --keys (run the keymap editor) ; --version ; --help.
Flags are stored as Boolean true. adapter_options adds each option of the
selected adapter as --{name} plus its short_decls, stored under the name with
"-" replaced by "_": Flag as Boolean true, Repeated as an Array of Text,
Choice as the matching choice's declared spelling (case-insensitive match),
Text and FilePath as Text.
Grammar: options and positional arguments may interleave; "--" ends options
and every later argument is positional; a lone "-" is positional. A long
option takes its value from "--name=VALUE" or the next argument (taken
verbatim even when it starts with "-"); a flag written "--flag=VALUE" is an
error. A short option taking a value accepts "-xVALUE" or the next argument;
short flags may be clustered ("-r"). Positional arguments collect into
conn_str.
Errors are Usage(message) for the first offending argument, with click's
wording: "No such option: {arg}" (for spellings that belong only to hsql:
-c, --command, --file, --format, --csv, --json, --jsonl, --markdown, -x,
--vertical, --tuples-only, -A, --no-align, --no-header, --no-footer,
--null-string, --timeout, --catalog, --catalog-search, --path, --history,
--history-search, --spec, --info, --skill, --display-rows, --result,
--on-error, --stats, --color, --serve, --session, --session-reset,
--session-status, --queue-timeout, --idle-timeout and --max-lifetime, instead "{arg} is not a
harlequin option. Did you mean 'hsql {arg}'? hsql is Harlequin's headless
CLI: it runs SQL and exits. See https://harlequin.sh/docs/headless");
"Option '{name}' requires an argument."; "Option '{name}' does not take a
value."; "Invalid value for '{names}': '{value}' is not one of {choices}."
(choices quoted with ' and joined by ", "); "Invalid value for '{names}':
'{value}' is not a valid integer." / "is not a valid float."; "Invalid value
for '{names}': {value} is not in the range x>=-1." (x>0 for --ssh-timeout);
where names is the option's spellings joined by " / " as click lists them
(for example "'-a' / '--adapter'" written as '--adapter' / '-a')."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    adapter_names = _cott_normalize_f32_abi(adapter_names, CottList[str], path="$.adapter_names")
    adapter_options = _cott_normalize_f32_abi(adapter_options, CottList[AdapterOption], path="$.adapter_options")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/cli/parse_harlequin_arguments.py", "5ffad19c8b80d468fc22ce464158d22bcd26f5bbf918e826b7031685db17f581", "parse_harlequin_arguments", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.cli.parse_harlequin_arguments")
        _result = _implementation(arguments, adapter_names, adapter_options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.cli.parse_harlequin_arguments"
        if _error.span is None:
            _error.span = {"end_byte":6841,"end_column":1,"end_line":162,"start_byte":3164,"start_column":1,"start_line":103}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.cli.parse_harlequin_arguments", phase="implementation-call", span={"end_byte":6841,"end_column":1,"end_line":162,"start_byte":3164,"start_column":1,"start_line":103}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.cli.parse_harlequin_arguments", phase="implementation-call", span={"end_byte":6841,"end_column":1,"end_line":162,"start_byte":3164,"start_column":1,"start_line":103}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CliArguments, CliError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.cli.parse_harlequin_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (CliError_Usage,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.cli.parse_harlequin_arguments", phase="error", span={"end_byte":6841,"end_column":1,"end_line":162,"start_byte":3164,"start_column":1,"start_line":103}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.cli.parse_harlequin_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.cli.parse_harlequin_arguments", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is CliError_Usage:
            _cott_contract_condition(True, "real.harlequin.cli.parse_harlequin_arguments", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                parsed = _cott_match_value.value
                return (_cott_contract_condition((((not (len(arguments) == 0)) or ((len((parsed).conn_str) == 0) and (len((parsed).explicit) == 0)))), "real.harlequin.cli.parse_harlequin_arguments", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.cli.parse_harlequin_arguments", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.cli.parse_harlequin_arguments", clause="ensures:1", phase="ensures", span={"end_byte":6797,"end_column":111,"end_line":156,"start_byte":6691,"start_column":5,"start_line":156}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CliArguments, CliError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def harlequin_version_text(adapter_names: CottList[str]) -> str:
    """The --version output: "harlequin, version {HARLEQUIN_VERSION}\\n\\nInstalled
Adapters:\\n" followed by one line "  - {name}, version {HARLEQUIN_VERSION}\\n"
per adapter name in sorted order (every adapter ships in this build)."""
    adapter_names = _cott_normalize_f32_abi(adapter_names, CottList[str], path="$.adapter_names")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/cli/harlequin_version_text.py", "2d5eb12f41a21a431269601367ec5989aedc7496a8705e40a78655ef0c905c88", "harlequin_version_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.cli.harlequin_version_text")
        _result = _implementation(adapter_names)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.cli.harlequin_version_text"
        if _error.span is None:
            _error.span = {"end_byte":7231,"end_column":1,"end_line":173,"start_byte":6841,"start_column":1,"start_line":162}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.cli.harlequin_version_text", phase="implementation-call", span={"end_byte":7231,"end_column":1,"end_line":173,"start_byte":6841,"start_column":1,"start_line":162}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.cli.harlequin_version_text", phase="implementation-call", span={"end_byte":7231,"end_column":1,"end_line":173,"start_byte":6841,"start_column":1,"start_line":162}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "harlequin, version ")), "real.harlequin.cli.harlequin_version_text", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.cli.harlequin_version_text", clause="ensures:1", phase="ensures", span={"end_byte":7213,"end_column":57,"end_line":169,"start_byte":7161,"start_column":5,"start_line":169}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def harlequin_help(descriptors: CottList[AdapterDescriptor]) -> str:
    """The --help text, in click's layout: "Usage: harlequin [OPTIONS] [CONN_STR]...",
a blank line, the indented description "  The Harlequin IDE: a SQL IDE for
your terminal. CONN_STR is zero or more connection strings or database file
paths for the selected adapter.", then an "Options:" section with one entry
per core option of parse_harlequin_arguments (spellings, metavar, and a help
sentence naming its default), then for each descriptor in order a section
"{display_name} Adapter Options:" listing each option of
real.harlequin.adapters.adapter_options(kind) as its spellings, metavar
(TEXT, PATH or [choice|...] ; flags have none) and description, with secret
options noted "(secret)". Entries are two-space indented with help text
aligned in a column and wrapped at 79 characters."""
    descriptors = _cott_normalize_f32_abi(descriptors, CottList[AdapterDescriptor], path="$.descriptors")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/cli/harlequin_help.py", "075c7b11540639bd100348b0c2ddaea7eecc452a20e0aed4d6b35c6cdadf5d0f", "harlequin_help", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.cli.harlequin_help")
        _result = _implementation(descriptors)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.cli.harlequin_help"
        if _error.span is None:
            _error.span = {"end_byte":8240,"end_column":1,"end_line":192,"start_byte":7231,"start_column":1,"start_line":173}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.cli.harlequin_help", phase="implementation-call", span={"end_byte":8240,"end_column":1,"end_line":192,"start_byte":7231,"start_column":1,"start_line":173}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.cli.harlequin_help", phase="implementation-call", span={"end_byte":8240,"end_column":1,"end_line":192,"start_byte":7231,"start_column":1,"start_line":173}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "Usage: harlequin [OPTIONS] [CONN_STR]...")), "real.harlequin.cli.harlequin_help", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.cli.harlequin_help", clause="ensures:1", phase="ensures", span={"end_byte":8222,"end_column":78,"end_line":188,"start_byte":8149,"start_column":5,"start_line":188}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def resolve_harlequin_settings(profile: Option[Profile], arguments: CliArguments, descriptor: AdapterDescriptor, options: CottList[AdapterOption]) -> Result[HarlequinSettings, ConfigError]:
    """Combine the selected (already interpolated) profile with the command line
the way Harlequin does, for the adapter descriptor (the adapter typed with
-a, else the profile's adapter, else duckdb) whose options are options.
Start from the profile's entries; every explicit command-line entry
replaces the profile entry of the same key (explicit false and 0 included);
a nonempty positional conn_str replaces the profile's conn_str (a profile
conn_str may be one Text or an Array of Text). Then read the keys:
adapter (must name descriptor), conn_str, read_only (Boolean, or the Text
"true"/"false"), theme (Text, default "harlequin"), keymap_name (Text or
Array of Text, default ["vscode"]), limit (whole number >= -1; -1 means
Nothing; 0 is zero rows; default Nothing), viewer_max_rows (whole number >= -1;
0 and -1 mean Nothing; default 100000), output, show_files, show_s3, locale
(Text), no_write_history and no_download_tzdata (Boolean only),
ssh_host, ssh_forward (Array of Text or one Text), ssh_batch_mode (Boolean),
ssh_allow_reuse (Boolean; true is refused when it came from the profile),
ssh_timeout (number > 0; default 60.0). Every other key must be an option of
options (by profile spelling) and becomes an AdapterSetting: Flag options take
Boolean or "true"/"false" Text; Repeated options take an Array of Text (a
single Text becomes a one-element list); Choice options take one of choices
ignoring case, normalized; Text and FilePath options take Text, numbers
becoming their text.
Errors are Invalid(title, message) with title "Harlequin couldn't load your
config file." and messages: "Profile defines an option '{key}', which is not
an option of the {adapter} adapter." (plus " Did you mean '{match}'?" when
real.harlequin.sqltext.close_matches(key, command and adapter keys, 1)
finds one);
"Profile sets {key} to a value the {adapter} adapter cannot take: {reason}.";
"{key}={value!r} is not a whole number of rows."; "{key}={value!r} is not a
number of rows. Pass -1 for no limit."; "{key}={value!r} is not a positive
number of seconds. Leave it out for a run that takes as long as it takes.";
"no_write_history must be true or false."; "ssh_allow_reuse can only be set
on the command line. Pass --ssh-allow-reuse."; "SSH options are set but
ssh_host is not."; and, when read_only is true for an adapter that does not
implement read-only, title "Harlequin could not start." and message
"{adapter} does not declare read-only support, so --read-only cannot be
honored. See `hsql --info`."."""
    profile = _cott_normalize_f32_abi(profile, Option[Profile], path="$.profile")
    arguments = _cott_normalize_f32_abi(arguments, CliArguments, path="$.arguments")
    descriptor = _cott_normalize_f32_abi(descriptor, AdapterDescriptor, path="$.descriptor")
    options = _cott_normalize_f32_abi(options, CottList[AdapterOption], path="$.options")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/cli/resolve_harlequin_settings.py", "1134a82e567c7f1e5a7f56970d3b8b79341ad39ede48747a0e40c9f56f553bf1", "resolve_harlequin_settings", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.cli.resolve_harlequin_settings")
        _result = _implementation(profile, arguments, descriptor, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.cli.resolve_harlequin_settings"
        if _error.span is None:
            _error.span = {"end_byte":11241,"end_column":1,"end_line":243,"start_byte":8240,"start_column":1,"start_line":192}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.cli.resolve_harlequin_settings", phase="implementation-call", span={"end_byte":11241,"end_column":1,"end_line":243,"start_byte":8240,"start_column":1,"start_line":192}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.cli.resolve_harlequin_settings", phase="implementation-call", span={"end_byte":11241,"end_column":1,"end_line":243,"start_byte":8240,"start_column":1,"start_line":192}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[HarlequinSettings, ConfigError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.cli.resolve_harlequin_settings", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConfigError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.cli.resolve_harlequin_settings", phase="error", span={"end_byte":11241,"end_column":1,"end_line":243,"start_byte":8240,"start_column":1,"start_line":192}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.cli.resolve_harlequin_settings", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.cli.resolve_harlequin_settings", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
            _cott_contract_condition(True, "real.harlequin.cli.resolve_harlequin_settings", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                settings = _cott_match_value.value
                return (_cott_contract_condition(((((settings).request).adapter == (descriptor).kind)), "real.harlequin.cli.resolve_harlequin_settings", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.cli.resolve_harlequin_settings", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.cli.resolve_harlequin_settings", clause="ensures:1", phase="ensures", span={"end_byte":11192,"end_column":79,"end_line":237,"start_byte":11118,"start_column":5,"start_line":237}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HarlequinSettings, ConfigError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["CliArguments", "CliError", "CliError_Usage", "FirstPass", "HARLEQUIN_VERSION", "HarlequinSettings", "SshSettings", "first_pass", "harlequin_help", "harlequin_option_names", "harlequin_version_text", "parse_harlequin_arguments", "resolve_harlequin_settings"]
