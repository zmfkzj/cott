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

from real.harlequin.hsql_types import CatalogPath, HSQL_PROTOCOL_VERSION, HsqlArguments, HsqlContext, HsqlError, HsqlError_Connection, HsqlError_Crash, HsqlError_Interrupted, HsqlError_Query, HsqlError_Timeout, HsqlError_Usage, HsqlMode, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_ConfigMode, HsqlMode_Execute, HsqlMode_History, HsqlMode_HistorySearch, HsqlMode_Info, HsqlMode_Serve, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlMode_Skill, HsqlMode_Spec, HsqlResponse, LayoutOptions, SqlSource, SqlSource_Command, SqlSource_SqlFile
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, Connection, ConnectionRequest
from real.harlequin.config_types import ConfigEntry
from real.harlequin.results_types import ColumnInfo, ResultSet

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def hsql_exit_status(failure: HsqlError) -> I64:
    """The exit status of failure: Usage 2, Query 1, Connection 3, Timeout 4,
Interrupted 130, Crash 70."""
    failure = _cott_normalize_f32_abi(failure, HsqlError, path="$.failure")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/hsql_exit_status.py", "c5c75e9f16d6be7c21de21fe7a99cb79555761b82c96401ff537e338f84fd30f", "hsql_exit_status", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.hsql_exit_status")
        _result = _implementation(failure)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.hsql_exit_status"
        if _error.span is None:
            _error.span = {"end_byte":4630,"end_column":1,"end_line":176,"start_byte":4414,"start_column":1,"start_line":166}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.hsql_exit_status", phase="implementation-call", span={"end_byte":4630,"end_column":1,"end_line":176,"start_byte":4414,"start_column":1,"start_line":166}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.hsql_exit_status", phase="implementation-call", span={"end_byte":4630,"end_column":1,"end_line":176,"start_byte":4414,"start_column":1,"start_line":166}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, I64, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((_result >= 1)), "real.harlequin.hsql.hsql_exit_status", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.hsql_exit_status", clause="ensures:1", phase="ensures", span={"end_byte":4612,"end_column":24,"end_line":172,"start_byte":4593,"start_column":5,"start_line":172}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, I64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def hsql_error_line(failure: HsqlError) -> str:
    """The stderr text for failure: "hsql: error: {message}\\n" (Interrupted is
"hsql: error: interrupted\\n"); Crash is "hsql: error: hsql hit a bug in
itself and could not finish the run.\\nnote: {message}\\n"."""
    failure = _cott_normalize_f32_abi(failure, HsqlError, path="$.failure")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/hsql_error_line.py", "6748f895e7569178c50e10a82112e817cf9ba99d5596542cfa9138df84e1264f", "hsql_error_line", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.hsql_error_line")
        _result = _implementation(failure)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.hsql_error_line"
        if _error.span is None:
            _error.span = {"end_byte":4980,"end_column":1,"end_line":187,"start_byte":4630,"start_column":1,"start_line":176}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.hsql_error_line", phase="implementation-call", span={"end_byte":4980,"end_column":1,"end_line":187,"start_byte":4630,"start_column":1,"start_line":176}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.hsql_error_line", phase="implementation-call", span={"end_byte":4980,"end_column":1,"end_line":187,"start_byte":4630,"start_column":1,"start_line":176}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "hsql: error: ")), "real.harlequin.hsql.hsql_error_line", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.hsql_error_line", clause="ensures:1", phase="ensures", span={"end_byte":4962,"end_column":51,"end_line":183,"start_byte":4916,"start_column":5,"start_line":183}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def parse_hsql_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[HsqlArguments, HsqlError]:
    """Parse `hsql [OPTIONS] [CONN_STR]...` (arguments without the program name)
with the click grammar of real.harlequin.cli.parse_harlequin_arguments
(interleaved positionals, "--", --name=VALUE, -xVALUE, clustered short
flags such as -tA or -tAc SQL). Options: -a/--adapter NAME (one of
adapter_names, case-insensitive; default duckdb); -c/--command TEXT and
-f/--file PATH (repeatable, kept in argv order as sources); -o/--output
PATH; --format NAME (table, markdown, md, vertical, csv, tsv, json, jsonl,
ndjson, parquet, orc, feather, arrow, none; case-insensitive); --csv,
--json, --jsonl, --markdown, -x/--vertical shorthands; -t/--tuples-only;
-A/--no-align; --no-header; --no-footer; --null-string TEXT; -P/--profile
NAME; --config-path PATH; -r/--read-only; --timeout SECONDS (> 0);
--ssh-host, --ssh-forward (repeatable), --ssh-batch-mode,
--ssh-allow-reuse, --ssh-timeout SECONDS (> 0); --catalog;
--catalog-search TERM; --path TEXT; --history; --history-search TERM;
--config MODE (show, list-profiles, validate, schema, init); --spec;
--info; --skill; --limit N (integer >= -1, default 500); --display-rows N
(>= -1); --result all|last|N; --on-error stop|continue; --no-write-history;
--stats; --color auto|always|never (default never); --serve NAME;
--session NAME; --session-reset; --session-status; --queue-timeout
SECONDS (> 0); --idle-timeout SECONDS (>= 0, default 1800);
--max-lifetime SECONDS (>= 0, default 28800); --help; --version; plus
each adapter option (spellings that collide with an hsql spelling are
withheld). Errors are Usage with click's messages ("No such option: X",
"Option 'X' requires an argument.", "Invalid value for ...") and these:
two modes: "{first} and {second} can't be used together."; a mode with
-c/-f: "{mode} doesn't run SQL, so it can't be combined with -c/--command
or -f/--file."; a format shorthand with another format selector:
"{a} and {b} both choose an output format; pass only one."; --path
without --catalog or --catalog-search: "--path only applies to --catalog
and --catalog-search."; blank --catalog-search term: "--catalog-search
needs a term to search for."; blank --history-search term:
"--history-search needs a term to search for."; a per-request option with
--serve: "{option} is a per-request option; pass it with each --session
request, not to --serve."; a server-lifetime option without --serve:
"{option} only applies to --serve."; an invalid --result: "--result must
be all, last, or a result number."."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    adapter_names = _cott_normalize_f32_abi(adapter_names, CottList[str], path="$.adapter_names")
    adapter_options = _cott_normalize_f32_abi(adapter_options, CottList[AdapterOption], path="$.adapter_options")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/parse_hsql_arguments.py", "40c8f6e02760425d19627a710dda221438f5c7180f66c3d83bcf43c83e4387c5", "parse_hsql_arguments", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.parse_hsql_arguments")
        _result = _implementation(arguments, adapter_names, adapter_options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.parse_hsql_arguments"
        if _error.span is None:
            _error.span = {"end_byte":7876,"end_column":1,"end_line":237,"start_byte":4980,"start_column":1,"start_line":187}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.parse_hsql_arguments", phase="implementation-call", span={"end_byte":7876,"end_column":1,"end_line":237,"start_byte":4980,"start_column":1,"start_line":187}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.parse_hsql_arguments", phase="implementation-call", span={"end_byte":7876,"end_column":1,"end_line":237,"start_byte":4980,"start_column":1,"start_line":187}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[HsqlArguments, HsqlError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.hsql.parse_hsql_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (HsqlError_Usage,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.hsql.parse_hsql_arguments", phase="error", span={"end_byte":7876,"end_column":1,"end_line":237,"start_byte":4980,"start_column":1,"start_line":187}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.hsql.parse_hsql_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.hsql.parse_hsql_arguments", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is HsqlError_Usage:
            _cott_contract_condition(True, "real.harlequin.hsql.parse_hsql_arguments", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                parsed = _cott_match_value.value
                return (_cott_contract_condition((((parsed).limit >= (-1))), "real.harlequin.hsql.parse_hsql_arguments", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.hsql.parse_hsql_arguments", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.parse_hsql_arguments", clause="ensures:1", phase="ensures", span={"end_byte":7831,"end_column":52,"end_line":231,"start_byte":7784,"start_column":5,"start_line":231}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HsqlArguments, HsqlError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def hsql_help(descriptors: CottList[AdapterDescriptor], selected: Option[AdapterDescriptor], options: CottList[AdapterOption]) -> str:
    """The hsql help text in click's layout: "Usage: hsql [OPTIONS] [CONN_STR]...",
a blank line, the description "  Run SQL against a database and exit.
hsql is Harlequin's headless CLI." with a line listing the installed
adapter names ("  Installed adapters: duckdb, sqlite, ..."), then
"Options:" with every hsql option of parse_hsql_arguments (spellings,
metavar, help sentence with its default), and, when selected is Some, a
section "{display_name} Adapter Options:" with options."""
    descriptors = _cott_normalize_f32_abi(descriptors, CottList[AdapterDescriptor], path="$.descriptors")
    selected = _cott_normalize_f32_abi(selected, Option[AdapterDescriptor], path="$.selected")
    options = _cott_normalize_f32_abi(options, CottList[AdapterOption], path="$.options")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/hsql_help.py", "d75bac42eeec3271c89df790297405be8b26dbf071f4ba9a67e376d405bfe347", "hsql_help", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.hsql_help")
        _result = _implementation(descriptors, selected, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.hsql_help"
        if _error.span is None:
            _error.span = {"end_byte":8636,"end_column":1,"end_line":256,"start_byte":7876,"start_column":1,"start_line":237}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.hsql_help", phase="implementation-call", span={"end_byte":8636,"end_column":1,"end_line":256,"start_byte":7876,"start_column":1,"start_line":237}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.hsql_help", phase="implementation-call", span={"end_byte":8636,"end_column":1,"end_line":256,"start_byte":7876,"start_column":1,"start_line":237}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "Usage: hsql [OPTIONS] [CONN_STR]...")), "real.harlequin.hsql.hsql_help", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.hsql_help", clause="ensures:1", phase="ensures", span={"end_byte":8618,"end_column":73,"end_line":252,"start_byte":8550,"start_column":5,"start_line":252}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def layout_text(result_set: ResultSet, layout: str, options: LayoutOptions) -> str:
    """Render result_set in a text layout (upstream harlequin.layout): layout
is "table", "markdown" (also "md") or "vertical". Cells are the Python
str() of each value (bytes as their Python repr; floats by repr), SQL NULL
as options.null_string or "NULL", CRLF normalized to LF. Rows are capped
at options.max_rows before widths are measured. Widths count terminal
cells (wcwidth for non-ASCII). Table aligned: header " a | b" (a leading
space, " | " separators, each cell padded), rule of "-" with "-+-" at
separators, then rows the same way; the last column is not padded;
multi-line cells continue on the next physical line with "+" at the
separator. Table unaligned: header and rows joined by "|", no rule.
Markdown: "| a | b |", "| --- | --- |" (minimum width 3), cells with "|"
escaped as "\\\\|" and newlines as "<br>", footer as "*(N rows)*" after a
blank line. Vertical aligned: each record starts "-[ RECORD N ]" followed
by dashes to the widest line, then "name | value" lines with names padded;
unaligned "name|value". Footer (when options.footer): "(1 row)" or
"(N rows)"; "(SHOWN of TOTAL rows)" when capped; "(SHOWN of >FETCHED
rows)" when result_set.truncated. header false drops the header and rule
(vertical: record rules become blank lines). With options.color the
header cells are wrapped in "\\u001b[1m...\\u001b[0m" and NULL cells in
"\\u001b[2m...\\u001b[0m". Every line ends with "\\n"."""
    result_set = _cott_normalize_f32_abi(result_set, ResultSet, path="$.result_set")
    layout = _cott_normalize_f32_abi(layout, str, path="$.layout")
    options = _cott_normalize_f32_abi(options, LayoutOptions, path="$.options")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/layout_text.py", "174a5a2a53ed17e2f225f9a1fbc7f010db3c53700fce182ad20f333aefc0e630", "layout_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.layout_text")
        _result = _implementation(result_set, layout, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.layout_text"
        if _error.span is None:
            _error.span = {"end_byte":10235,"end_column":1,"end_line":282,"start_byte":8636,"start_column":1,"start_line":256}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.layout_text", phase="implementation-call", span={"end_byte":10235,"end_column":1,"end_line":282,"start_byte":8636,"start_column":1,"start_line":256}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.layout_text", phase="implementation-call", span={"end_byte":10235,"end_column":1,"end_line":282,"start_byte":8636,"start_column":1,"start_line":256}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def format_suffix(format: str) -> str:
    """The file suffix of an output format: table and vertical ".txt", markdown
and md ".md", csv ".csv", tsv ".tsv", json ".json", jsonl ".jsonl", ndjson
".ndjson", parquet ".parquet", orc ".orc", feather ".feather", arrow
".arrow", none "" (and "" for anything else)."""
    format = _cott_normalize_f32_abi(format, str, path="$.format")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/format_suffix.py", "5b6dbaadaa1172efbd79e14d1c87df44b091475f90ef26f4e1fd47a79ff09ea3", "format_suffix", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.format_suffix")
        _result = _implementation(format)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.format_suffix"
        if _error.span is None:
            _error.span = {"end_byte":10589,"end_column":1,"end_line":292,"start_byte":10235,"start_column":1,"start_line":282}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.format_suffix", phase="implementation-call", span={"end_byte":10589,"end_column":1,"end_line":292,"start_byte":10235,"start_column":1,"start_line":282}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.format_suffix", phase="implementation-call", span={"end_byte":10589,"end_column":1,"end_line":292,"start_byte":10235,"start_column":1,"start_line":282}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def parse_catalog_path(path: str) -> Result[CatalogPath, HsqlError]:
    """Parse an hsql --path (upstream navigate.parse): a blank path is the root
(no segments). Segments are separated by "."; a segment wholly in double
quotes is literal (a doubled "" is one quote, dots and wildcards are
literal); a bare final segment containing * or ? is the pattern. Errors are
Usage: an empty segment "'{path}' has an empty segment. Separate labels
with one dot, and quote a label that contains a dot, like \\"my.table\\".";
an unquoted wildcard before the last segment "'{segment}' contains a
wildcard in the middle of a path, which is not supported. A wildcard is
only allowed in the last path segment."; an unterminated quote "The quoted
segment starting at {rest} never closes. Write a literal quote as \\"\\".";
a partially quoted segment "'{segment}' mixes quoted and bare text. Quote
the whole segment or none of it."."""
    path = _cott_normalize_f32_abi(path, str, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/parse_catalog_path.py", "fab2a1c4e1e5bea8467f5f152a04d0eda9db88340468dae59e94a362682abd8e", "parse_catalog_path", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.parse_catalog_path")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.parse_catalog_path"
        if _error.span is None:
            _error.span = {"end_byte":11680,"end_column":1,"end_line":314,"start_byte":10589,"start_column":1,"start_line":292}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.parse_catalog_path", phase="implementation-call", span={"end_byte":11680,"end_column":1,"end_line":314,"start_byte":10589,"start_column":1,"start_line":292}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.parse_catalog_path", phase="implementation-call", span={"end_byte":11680,"end_column":1,"end_line":314,"start_byte":10589,"start_column":1,"start_line":292}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CatalogPath, HsqlError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.hsql.parse_catalog_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (HsqlError_Usage,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.hsql.parse_catalog_path", phase="error", span={"end_byte":11680,"end_column":1,"end_line":314,"start_byte":10589,"start_column":1,"start_line":292}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.hsql.parse_catalog_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.hsql.parse_catalog_path", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is HsqlError_Usage:
            _cott_contract_condition(True, "real.harlequin.hsql.parse_catalog_path", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                parsed = _cott_match_value.value
                return (_cott_contract_condition((((not (path == "")) or (len((parsed).segments) == 0))), "real.harlequin.hsql.parse_catalog_path", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.hsql.parse_catalog_path", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.parse_catalog_path", clause="ensures:1", phase="ensures", span={"end_byte":11635,"end_column":74,"end_line":308,"start_byte":11566,"start_column":5,"start_line":308}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CatalogPath, HsqlError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def spell_catalog_label(label: str) -> str:
    """A label as a --path segment: wrapped in double quotes (inner quotes
doubled) when it is empty, has leading or trailing whitespace, or contains
".", "*", "?" or a double quote; otherwise unchanged."""
    label = _cott_normalize_f32_abi(label, str, path="$.label")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/spell_catalog_label.py", "378be17404bfa5aaf9195754c9602ec3a1bf64496f1076aabf5fc27dd6b646b4", "spell_catalog_label", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.spell_catalog_label")
        _result = _implementation(label)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.spell_catalog_label"
        if _error.span is None:
            _error.span = {"end_byte":11969,"end_column":1,"end_line":323,"start_byte":11680,"start_column":1,"start_line":314}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.spell_catalog_label", phase="implementation-call", span={"end_byte":11969,"end_column":1,"end_line":323,"start_byte":11680,"start_column":1,"start_line":314}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.spell_catalog_label", phase="implementation-call", span={"end_byte":11969,"end_column":1,"end_line":323,"start_byte":11680,"start_column":1,"start_line":314}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def missing_label_message(segment: str, parent: Option[str], siblings: CottList[str]) -> str:
    """The error for a --path segment that names nothing: "There is no '{segment}'
under {parent}." (parent spelled "'{parent}'", or "the top level of the
catalog" when Nothing), then " Did you mean: {a}, {b}?" with up to three
real.harlequin.sqltext.close_matches(segment, siblings, 3) (each spelled with
spell_catalog_label) when any; else " It contains: {first five}" plus
", and N more" when there are more; else " That level is empty."."""
    segment = _cott_normalize_f32_abi(segment, str, path="$.segment")
    parent = _cott_normalize_f32_abi(parent, Option[str], path="$.parent")
    siblings = _cott_normalize_f32_abi(siblings, CottList[str], path="$.siblings")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/missing_label_message.py", "b4e84f3e691749f87c5e7cb4477064bdd759c7ea71beb7d7d9d2c528bbcae1dd", "missing_label_message", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.missing_label_message")
        _result = _implementation(segment, parent, siblings)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.missing_label_message"
        if _error.span is None:
            _error.span = {"end_byte":12605,"end_column":1,"end_line":337,"start_byte":11969,"start_column":1,"start_line":323}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.missing_label_message", phase="implementation-call", span={"end_byte":12605,"end_column":1,"end_line":337,"start_byte":11969,"start_column":1,"start_line":323}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.missing_label_message", phase="implementation-call", span={"end_byte":12605,"end_column":1,"end_line":337,"start_byte":11969,"start_column":1,"start_line":323}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "There is no ")), "real.harlequin.hsql.missing_label_message", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.missing_label_message", clause="ensures:1", phase="ensures", span={"end_byte":12587,"end_column":50,"end_line":333,"start_byte":12542,"start_column":5,"start_line":333}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def stats_json(status: str, statements: U64, rows: U64, truncated: bool, limit: Option[U64], elapsed_ms: U64, columns: CottList[ColumnInfo], failure_text: Option[str]) -> str:
    """The --stats line: compact JSON (separators "," and ":") with keys in this
order: "status", "statements", "rows", "truncated", "limit" (null when
Nothing), "elapsed_ms", "columns" (a list of {"name":...,"type":...} with
type the column's type_label), and "error" only when failure_text is Some;
followed by "\\n"."""
    status = _cott_normalize_f32_abi(status, str, path="$.status")
    statements = _cott_normalize_f32_abi(statements, U64, path="$.statements")
    rows = _cott_normalize_f32_abi(rows, U64, path="$.rows")
    truncated = _cott_normalize_f32_abi(truncated, bool, path="$.truncated")
    limit = _cott_normalize_f32_abi(limit, Option[U64], path="$.limit")
    elapsed_ms = _cott_normalize_f32_abi(elapsed_ms, U64, path="$.elapsed_ms")
    columns = _cott_normalize_f32_abi(columns, CottList[ColumnInfo], path="$.columns")
    failure_text = _cott_normalize_f32_abi(failure_text, Option[str], path="$.failure_text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/stats_json.py", "b193d7a160491f9c9cc5d19fbcfdd00e1a8b0e1442d195d85de714e97a9c1559", "stats_json", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.stats_json")
        _result = _implementation(status, statements, rows, truncated, limit, elapsed_ms, columns, failure_text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.stats_json"
        if _error.span is None:
            _error.span = {"end_byte":13231,"end_column":1,"end_line":359,"start_byte":12605,"start_column":1,"start_line":337}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.stats_json", phase="implementation-call", span={"end_byte":13231,"end_column":1,"end_line":359,"start_byte":12605,"start_column":1,"start_line":337}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.stats_json", phase="implementation-call", span={"end_byte":13231,"end_column":1,"end_line":359,"start_byte":12605,"start_column":1,"start_line":337}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "{\"status\":")), "real.harlequin.hsql.stats_json", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.stats_json", clause="ensures:1", phase="ensures", span={"end_byte":13213,"end_column":50,"end_line":355,"start_byte":13168,"start_column":5,"start_line":355}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def valid_session_name(name: str) -> bool:
    """Whether name is a session name: 1 to 64 characters, each an ASCII letter,
digit, "_" or "-"."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/valid_session_name.py", "0f5009631be0c9dab2eb6c75abe0b87d5aa68830346c8696bf0cb5d7505a75eb", "valid_session_name", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.valid_session_name")
        _result = _implementation(name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.valid_session_name"
        if _error.span is None:
            _error.span = {"end_byte":13473,"end_column":1,"end_line":369,"start_byte":13231,"start_column":1,"start_line":359}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.valid_session_name", phase="implementation-call", span={"end_byte":13473,"end_column":1,"end_line":369,"start_byte":13231,"start_column":1,"start_line":359}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.valid_session_name", phase="implementation-call", span={"end_byte":13473,"end_column":1,"end_line":369,"start_byte":13231,"start_column":1,"start_line":359}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, bool, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not _result) or ((len(name) >= 1) and (len(name) <= 64)))), "real.harlequin.hsql.valid_session_name", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.valid_session_name", clause="ensures:1", phase="ensures", span={"end_byte":13455,"end_column":61,"end_line":365,"start_byte":13399,"start_column":5,"start_line":365}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def session_socket_path(name: str, environment: FrozenMap[str, str], uid: I64) -> Path:
    """The socket of session name: "{XDG_RUNTIME_DIR}/hsql/{name}.sock" when
XDG_RUNTIME_DIR is set and nonempty in environment, else
"{TMPDIR or /tmp}/hsql-{uid}/{name}.sock"."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    environment = _cott_normalize_f32_abi(environment, FrozenMap[str, str], path="$.environment")
    uid = _cott_normalize_f32_abi(uid, I64, path="$.uid")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/session_socket_path.py", "cc9fddbeb1dcfe4cb47011dfc1e14ca5a8665f56126bb4b0be678553cfabf910", "session_socket_path", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.session_socket_path")
        _result = _implementation(name, environment, uid)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.session_socket_path"
        if _error.span is None:
            _error.span = {"end_byte":13773,"end_column":1,"end_line":378,"start_byte":13473,"start_column":1,"start_line":369}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.session_socket_path", phase="implementation-call", span={"end_byte":13773,"end_column":1,"end_line":378,"start_byte":13473,"start_column":1,"start_line":369}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.session_socket_path", phase="implementation-call", span={"end_byte":13773,"end_column":1,"end_line":378,"start_byte":13473,"start_column":1,"start_line":369}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Path, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Path, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def execute_hsql_request(connection: Connection, arguments: HsqlArguments, cwd: Path, stdin_text: Option[str], context: HsqlContext) -> HsqlResponse:
    """Serve one connected hsql request (the Execute, Catalog and CatalogSearch
modes) on connection, as a cold run and a warm session both do.
Execute: read the sources in order (files relative to cwd; "-" is
stdin_text; an OSError is Usage "could not read {path}: {reason}"), split
each with real.harlequin.sqltext.split_statements, run them with
real.harlequin.adapters.execute_statements(connection, statements, limit
(Nothing for -1), continue_on_error), then fetch every cursor with
real.harlequin.adapters.fetch_result((connection, executed, limit, Nothing). When
arguments.write_history each statement is logged with
real.harlequin.history.record_query/real.harlequin.history.update_query  (program "hsql", the
redacted sql). Select results per arguments.result; more than one result
for a single-result format (csv, tsv, json, parquet, orc, feather, arrow)
to a file or stdout is Usage "{n} result sets, but {format} holds one;
use --result last, --result N, or -o DIR for one file each". Write each
selected result: layouts with layout_text (LayoutOptions from -t, -A,
--no-header, --no-footer, --null-string, color decided by --color and
context tty/NO_COLOR, max_rows from --display-rows or 40 for table and
markdown, 10 for vertical, -1 for all) joined into stdout, separated by a
blank line; file formats with real.harlequin.export.write_result into a
temporary file whose bytes become stdout (csv null defaults to ""); -o
FILE writes stdout there instead; -o DIR writes "result-{n}{suffix}" files
and names each on stderr as "note: wrote {path}"; format none writes
nothing. Warnings on stderr: "note: results truncated at --limit {n};
pass --limit -1 for all rows" when a result was truncated; "note: printed
{shown} of {total} rows; pass --display-rows -1 for all of them" when the
footer is hidden and rows were capped; "note: --display-rows only applies
to text layouts; use --limit to fetch fewer rows." for a non-layout
format. A statement failure writes hsql_error_line(Query("{title}\\n
{message}")) and status 1 (after the earlier results). --timeout starts a
timer that calls real.harlequin.adapters.cancel_queries  (Timeout "timed out after {n}s", status
4). --stats appends stats_json to stderr.
Catalog: parse_catalog_path(arguments.catalog_path or ""), walk labels
from real.harlequin.adapters.load_catalog  with real.harlequin.adapters.load_catalog_children  (a missing label is Usage
missing_label_message), and list the level's children (filtered by the
pattern with fnmatch.fnmatchcase) as a result set with columns path, name,
query_name, type, type_label (path spelled with spell_catalog_label and
joined by "."). CatalogSearch: real.harlequin.adapters.search_catalog  under that scope.
Every stderr text is passed through real.harlequin.sqltext.redact_text
with context.secrets."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    arguments = _cott_normalize_f32_abi(arguments, HsqlArguments, path="$.arguments")
    cwd = _cott_normalize_f32_abi(cwd, Path, path="$.cwd")
    stdin_text = _cott_normalize_f32_abi(stdin_text, Option[str], path="$.stdin_text")
    context = _cott_normalize_f32_abi(context, HsqlContext, path="$.context")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/execute_hsql_request.py", "49e9d2c4ace2fc95cb81ef65a4a28590b03cca42e0c772a8b3b7799e0c8df723", "execute_hsql_request", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.execute_hsql_request")
        _result = _implementation(connection, arguments, cwd, stdin_text, context)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.execute_hsql_request"
        if _error.span is None:
            _error.span = {"end_byte":17045,"end_column":1,"end_line":431,"start_byte":13773,"start_column":1,"start_line":378}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.execute_hsql_request", phase="implementation-call", span={"end_byte":17045,"end_column":1,"end_line":431,"start_byte":13773,"start_column":1,"start_line":378}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.execute_hsql_request", phase="implementation-call", span={"end_byte":17045,"end_column":1,"end_line":431,"start_byte":13773,"start_column":1,"start_line":378}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, HsqlResponse, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).status >= 0)), "real.harlequin.hsql.execute_hsql_request", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.execute_hsql_request", clause="ensures:1", phase="ensures", span={"end_byte":16959,"end_column":31,"end_line":427,"start_byte":16933,"start_column":5,"start_line":427}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, HsqlResponse, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def serve_hsql_session(name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, environment: FrozenMap[str, str]) -> I64:
    """`hsql --serve NAME`: validate name with valid_session_name (Usage
"invalid session name '{name}': use 1 to 64 letters, digits, _ or -"),
create the runtime directory of session_socket_path (mode 0700; it must be
a real directory owned by this uid with no group/other bits, else Usage),
take an exclusive filelock.FileLock(timeout=0) on "{name}.lock" beside the
socket, released when the session ends (filelock.Timeout: Usage
"session '{name}' is already running"), remove a stale socket, connect
with real.harlequin.adapters.connect(request) (failure: "hsql: error:
{title}\\n{message}" and return 3), bind an AF_UNIX stream socket, and print
"note: session '{name}' is ready ({adapter}). Send it queries with `hsql
--session {name} -c ...`, or set HSQL_SESSION={name}. Ctrl-C stops it."
to stderr. Frames are "!BI" (kind byte, payload length) with payload at
most 64 MiB; kinds HELLO=1 REQUEST=2 STDOUT=3 STDERR=4 EXIT=5 STATUS=6
CANCEL=7. Each accepted peer (SO_PEERCRED uid must equal ours, else
"note: refused a connection from uid {uid}, which is not yours.") first
receives HELLO with HSQL_PROTOCOL_VERSION; a REQUEST payload is a JSON
object {"argv": [...], "cwd": str, "env": {"NO_COLOR"?,
"HARLEQUIN_CONFIG_PATH"?}, "stdin": str|null, "stdout_tty": bool,
"stderr_tty": bool, "id": hex}; requests run one at a time in arrival
order (arguments.queue_timeout_seconds bounds the wait: Timeout "waited
{n}s for the session's previous request and never reached the database
(--queue-timeout).") through parse_hsql_arguments and
execute_hsql_request, replying STDOUT chunks of at most 64 KiB, STDERR,
then EXIT with the 4-byte status; --session-reset closes and reconnects;
STATUS replies a JSON object with keys session, pid, version, adapter,
connection, connection_options, uptime_s, requests, state (idle, busy or
unavailable), queued, transaction_mode, ssh, idle_timeout_s,
expires_in_s without waiting behind a running query; CANCEL with a
request id cancels it with real.harlequin.adapters.cancel_queries.. Each request logs "note:
request {n}: exit {code} in {ms}ms". The server stops after
idle_timeout_seconds without requests or max_lifetime_seconds of age (0
disables either), or on Ctrl-C, printing "note: session '{name}' stopped
after {n} request(s).", closing the connection, removing the socket and
returning 0."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    request = _cott_normalize_f32_abi(request, ConnectionRequest, path="$.request")
    context = _cott_normalize_f32_abi(context, HsqlContext, path="$.context")
    arguments = _cott_normalize_f32_abi(arguments, HsqlArguments, path="$.arguments")
    environment = _cott_normalize_f32_abi(environment, FrozenMap[str, str], path="$.environment")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/serve_hsql_session.py", "b76374735a7b3c25501ec9eb7627acd7ab9c13e8acce48974dfd96bff78810f7", "serve_hsql_session", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.serve_hsql_session")
        _result = _implementation(name, request, context, arguments, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.serve_hsql_session"
        if _error.span is None:
            _error.span = {"end_byte":19784,"end_column":1,"end_line":477,"start_byte":17045,"start_column":1,"start_line":431}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.serve_hsql_session", phase="implementation-call", span={"end_byte":19784,"end_column":1,"end_line":477,"start_byte":17045,"start_column":1,"start_line":431}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.serve_hsql_session", phase="implementation-call", span={"end_byte":19784,"end_column":1,"end_line":477,"start_byte":17045,"start_column":1,"start_line":431}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, I64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, I64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def send_session_request(name: str, arguments: CottList[str], cwd: Path, stdin_text: Option[str], environment: FrozenMap[str, str], stdout_tty: bool, stderr_tty: bool) -> Result[HsqlResponse, HsqlError]:
    """The warm-session client of the serve_hsql_session wire protocol: connect an
AF_UNIX stream socket to session_socket_path(name, environment,
os.getuid()). Every frame is struct.pack("!BI", kind, len(payload)) followed
by payload; kinds are HELLO=1 REQUEST=2 STDOUT=3 STDERR=4 EXIT=5 STATUS=6
CANCEL=7. The server first sends HELLO whose payload is its version as
UTF-8; one that differs from HSQL_PROTOCOL_VERSION is
Err(Connection("session '{name}' runs hsql {v}; restart it with this
version")). When arguments contain --session-status, send one STATUS frame
with an empty payload and return Ok(HsqlResponse(stdout = the STATUS reply
payload + b"\\n", stderr "", status 0)). Otherwise send one REQUEST whose
payload is the UTF-8 JSON object {"argv": arguments, "cwd": str(cwd),
"env": {only NO_COLOR and HARLEQUIN_CONFIG_PATH when present in
environment}, "stdin": stdin_text or null, "stdout_tty": stdout_tty,
"stderr_tty": stderr_tty, "id": secrets.token_hex(8)}, then read frames,
concatenating STDOUT payloads as stdout bytes and STDERR payloads decoded
as UTF-8 text, until EXIT, whose payload is struct.pack("!i", status);
return Ok(HsqlResponse(stdout, stderr, status)). On KeyboardInterrupt while
waiting, open a second connection, read its HELLO, send CANCEL whose
payload is the request id as UTF-8, close it and return
Err(Interrupted). A socket that cannot be connected
(OSError) is Err(Connection("no session named '{name}' is running. Start
one with `hsql --serve {name} ...`.")); a connection closed before EXIT is
Err(Connection("session '{name}' closed the connection"))."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    cwd = _cott_normalize_f32_abi(cwd, Path, path="$.cwd")
    stdin_text = _cott_normalize_f32_abi(stdin_text, Option[str], path="$.stdin_text")
    environment = _cott_normalize_f32_abi(environment, FrozenMap[str, str], path="$.environment")
    stdout_tty = _cott_normalize_f32_abi(stdout_tty, bool, path="$.stdout_tty")
    stderr_tty = _cott_normalize_f32_abi(stderr_tty, bool, path="$.stderr_tty")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/send_session_request.py", "9277c54bd78879f32599a5779305e8ab428c191c29a55cd96bb0797b4d35e41d", "send_session_request", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.send_session_request")
        _result = _implementation(name, arguments, cwd, stdin_text, environment, stdout_tty, stderr_tty)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.send_session_request"
        if _error.span is None:
            _error.span = {"end_byte":21865,"end_column":1,"end_line":519,"start_byte":19784,"start_column":1,"start_line":477}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.hsql.send_session_request", phase="implementation-call", span={"end_byte":21865,"end_column":1,"end_line":519,"start_byte":19784,"start_column":1,"start_line":477}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.send_session_request", phase="implementation-call", span={"end_byte":21865,"end_column":1,"end_line":519,"start_byte":19784,"start_column":1,"start_line":477}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[HsqlResponse, HsqlError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.hsql.send_session_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (HsqlError_Connection, HsqlError_Interrupted,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.hsql.send_session_request", phase="error", span={"end_byte":21865,"end_column":1,"end_line":519,"start_byte":19784,"start_column":1,"start_line":477}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.hsql.send_session_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.hsql.send_session_request", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is HsqlError_Connection:
            _cott_contract_condition(True, "real.harlequin.hsql.send_session_request", "error:2")
        if type(_result) is Err and type(_result.error) is HsqlError_Interrupted:
            _cott_contract_condition(True, "real.harlequin.hsql.send_session_request", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                response = _cott_match_value.value
                return (_cott_contract_condition((((response).status >= 0)), "real.harlequin.hsql.send_session_request", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.hsql.send_session_request", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.hsql.send_session_request", clause="ensures:1", phase="ensures", span={"end_byte":21765,"end_column":56,"end_line":512,"start_byte":21714,"start_column":5,"start_line":512}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HsqlResponse, HsqlError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_hsql(arguments: CottList[str]) -> Never:
    """The hsql command (arguments without the program name); writes result
bytes to stdout and diagnostics to stderr (stdout flushed first) and exits
with the status. No arguments: print hsql_help to stderr and exit 2.
Session routing first: the last --session NAME (or --session=NAME, up to
"--"), else HSQL_SESSION unless an argument is --serve; a routed request
(reading stdin when an argument is "-f -" / "--file -") goes through
send_session_request; for HSQL_SESSION an unreachable session prints
"note: HSQL_SESSION={name} is not running; running cold." and continues
cold, for --session it exits 3.
Cold: real.harlequin.cli.first_pass finds -a/-P/--config-path; config
files come from real.harlequin.config.config_search_paths (explicit path,
else HARLEQUIN_CONFIG_PATH) read with real.harlequin.config.read_config_file  and merged with
real.harlequin.config.merge_config_files;; the profile is real.harlequin.config.select_profile  + real.harlequin.config.interpolate_profile

(-P None means no profile); the adapter is -a, else the profile's
adapter, else duckdb; parse_hsql_arguments with that adapter's options;
--help prints hsql_help to stdout (exit 0); --version prints "hsql,
version {HARLEQUIN_VERSION}" (exit 0). Profile entries are merged under
the explicit options (TUI-only keys theme, keymap_name, show_files,
show_s3, locale, viewer_max_rows, no_download_tzdata ignored). Modes that
do not connect: --history/--history-search read
real.harlequin.history.recent_queries (paths from real.harlequin.history.harlequin_paths;;
connection narrowing only when -P, -a or CONN_STR was typed; --limit rows,
one more read to detect truncation) and print them with layout_text as a
result set with columns run_at, program, profile, adapter, status, rows,
elapsed_ms, sql; --config show (merged config as TOML with secrets
replaced by "********", or JSON with --format json), list-profiles (one
name per line), validate (real.harlequin.config.validate_config_file  problems as
"{path}: {key}: {message}" lines, exit 2 when any, else "config is
valid"), schema (a JSON Schema object of the profile keys and adapter
options), init (real.harlequin.config.write_profile  of the typed options to the chosen profile;
-P required, "None" refused); --spec prints JSON {"hsql": {options...},
"adapters": {name: [option objects]}} (narrowed by an explicit -a);
--info prints JSON with "version", "python", "config_files",
"profile", and "adapters" capability objects; --skill prints the
packaged Markdown skill describing hsql usage (to -o DIR as
"SKILL.md"). --serve NAME runs serve_hsql_session. Otherwise connect with
real.harlequin.adapters.connect (the SSH tunnel through
real.harlequin.support.open_ssh_tunnel when --ssh-host; connection
failures exit 3 with "hsql: error: {title}\\n{message}"), no SQL source is
Usage "no SQL to run. Pass -c/--command or -f/--file, or see 'hsql
--help'.", then execute_hsql_request, write its stdout bytes and stderr
text, close the connection and exit with its status. Errors print
hsql_error_line and exit hsql_exit_status; Ctrl-C exits 130; an
unexpected exception exits 70."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/hsql/run_hsql.py", "00dfb19088836d2af88f8f15a0ecd1b9233b648f87fd1bbb57640fc691f77433", "run_hsql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.hsql.run_hsql")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.hsql.run_hsql"
        if _error.span is None:
            _error.span = {"end_byte":25403,"end_column":1,"end_line":579,"start_byte":21865,"start_column":1,"start_line":519}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.hsql.run_hsql", phase="implementation-call", span={"end_byte":25403,"end_column":1,"end_line":579,"start_byte":21865,"start_column":1,"start_line":519}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.harlequin.hsql.run_hsql", phase="return", span={"end_byte":25403,"end_column":1,"end_line":579,"start_byte":21865,"start_column":1,"start_line":519}, expected="Never", actual=repr(_result))

__all__ = ["CatalogPath", "HSQL_PROTOCOL_VERSION", "HsqlArguments", "HsqlContext", "HsqlError", "HsqlError_Connection", "HsqlError_Crash", "HsqlError_Interrupted", "HsqlError_Query", "HsqlError_Timeout", "HsqlError_Usage", "HsqlMode", "HsqlMode_Catalog", "HsqlMode_CatalogSearch", "HsqlMode_ConfigMode", "HsqlMode_Execute", "HsqlMode_History", "HsqlMode_HistorySearch", "HsqlMode_Info", "HsqlMode_Serve", "HsqlMode_SessionReset", "HsqlMode_SessionStatus", "HsqlMode_Skill", "HsqlMode_Spec", "HsqlResponse", "LayoutOptions", "SqlSource", "SqlSource_Command", "SqlSource_SqlFile", "execute_hsql_request", "format_suffix", "hsql_error_line", "hsql_exit_status", "hsql_help", "layout_text", "missing_label_message", "parse_catalog_path", "parse_hsql_arguments", "run_hsql", "send_session_request", "serve_hsql_session", "session_socket_path", "spell_catalog_label", "stats_json", "valid_session_name"]
