from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong_types import LogEntry, ToolongError, ToolongError_InvalidArguments, ToolongError_ReadFailed, ViewerOptions

def parse_arguments(arguments: CottList[str]) -> Result[ViewerOptions, ToolongError]:
    """Parse the command line [--contains TEXT] PATH... . Only the first argument
can be the option: when it is exactly "--contains", the second argument is
TEXT (any string, including an empty one or one starting with "--") and
contains is Option.Some(TEXT); every later argument is a path. Otherwise
contains is Option.Nothing and every argument, including a later
"--contains", is a path. Each path argument becomes one source, in argument
order. InvalidArguments: no arguments, "--contains" without TEXT, or no path."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len(arguments) == 0)), "real.toolong.parse_arguments", "error:3:condition")):
        _expected_error = ToolongError_InvalidArguments
        _expected_error_span = {"end_byte":1165,"end_column":64,"end_line":32,"start_byte":1106,"start_column":5,"start_line":32}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/parse_arguments.py", "0c7d4e59425ec45aa9fdc116736c454ec00cfa45a6898c81c9dd9788944bc8d3", "parse_arguments", expected_project_name="toolong", expected_cott_symbol="real.toolong.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":1223,"end_column":1,"end_line":37,"start_byte":282,"start_column":1,"start_line":18}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.parse_arguments", phase="implementation-call", span={"end_byte":1223,"end_column":1,"end_line":37,"start_byte":282,"start_column":1,"start_line":18}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.parse_arguments", phase="implementation-call", span={"end_byte":1223,"end_column":1,"end_line":37,"start_byte":282,"start_column":1,"start_line":18}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ViewerOptions, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_InvalidArguments,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.parse_arguments", phase="error", span={"end_byte":1223,"end_column":1,"end_line":37,"start_byte":282,"start_column":1,"start_line":18}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.toolong.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ToolongError_InvalidArguments:
        _cott_contract_condition(True, "real.toolong.parse_arguments", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return (_cott_contract_condition(((len((options).sources) > 0)), "real.toolong.parse_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.toolong.parse_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":983,"end_column":58,"end_line":29,"start_byte":930,"start_column":5,"start_line":29}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return (_cott_contract_condition((((len((options).sources) == len(arguments)) or ((len((options).sources) + 2) == len(arguments)))), "real.toolong.parse_arguments", "ensures:2"))
        _cott_contract_condition((False), "real.toolong.parse_arguments", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.parse_arguments", clause="ensures:2", phase="ensures", span={"end_byte":1100,"end_column":117,"end_line":30,"start_byte":988,"start_column":5,"start_line":30}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ViewerOptions, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_log(source: Path, text: str) -> CottList[LogEntry]:
    """Split the text of one log file into entries. Split text at every LF; drop the
last piece when it is empty (text ending in LF, or empty text); then remove
one trailing CR from each remaining piece. Empty lines in the middle are
kept. No other character (CR alone, VT, FF, NEL, U+2028, U+2029) separates
lines. Entry i, counted from one in piece order, has this source, line i and
the piece as text."""
    source = _cott_validate_abi(source, Path, path="$.source")
    text = _cott_validate_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/parse_log.py", "fb61cd2699d23ed4964a979c1bc923b983cb5f119bfc54805b1111cc4a4f8b25", "parse_log", expected_project_name="toolong", expected_cott_symbol="real.toolong.parse_log")
        _result = _implementation(source, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.parse_log"
        if _error.span is None:
            _error.span = {"end_byte":1857,"end_column":1,"end_line":52,"start_byte":1223,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.parse_log", phase="implementation-call", span={"end_byte":1857,"end_column":1,"end_line":52,"start_byte":1223,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.parse_log", phase="implementation-call", span={"end_byte":1857,"end_column":1,"end_line":52,"start_byte":1223,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[LogEntry], path="$.return")
    if not (_cott_contract_condition((((not (text == "")) or (len(_result) == 0))), "real.toolong.parse_log", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.parse_log", clause="ensures:1", phase="ensures", span={"end_byte":1766,"end_column":44,"end_line":47,"start_byte":1727,"start_column":5,"start_line":47}, expected="true", actual="false")
    if not (_cott_contract_condition((((not ((text != "") and (not ("\n" in text)))) or (len(_result) == 1))), "real.toolong.parse_log", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.parse_log", clause="ensures:2", phase="ensures", span={"end_byte":1839,"end_column":73,"end_line":48,"start_byte":1771,"start_column":5,"start_line":48}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[LogEntry], path="$.return", validator=_cott_validate_abi)
    return _result

def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]:
    """Read each source completely, in list order, and decode its bytes as strict
UTF-8. Each source path is read from the file system the program runs
against: the fs fixture root while a Cott scenario with an fs fixture is
active, otherwise the host file system, where a relative path is relative to
the process working directory. The result is the concatenation of
real.toolong.parse_log(source, text) for every source, so numbering restarts
at one for each source. The first source that is missing, cannot be opened
or read, or is not strict UTF-8 stops loading with ToolongError.ReadFailed
whose path is that source; no entries are returned then. While a scenario fs
fixture is active, a path the fixture does not permit (absolute, or outside
the fixture root) is a contract violation raised by the fixture, not a read
failure."""
    sources = _cott_validate_abi(sources, CottList[Path], path="$.sources")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/load_entries.py", "97814f4223ec75b71f98e9daf547114a78221f1f8f940266b426f019881941d9", "load_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.load_entries")
        _result = _implementation(sources)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.load_entries"
        if _error.span is None:
            _error.span = {"end_byte":2964,"end_column":1,"end_line":74,"start_byte":1857,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.load_entries", phase="implementation-call", span={"end_byte":2964,"end_column":1,"end_line":74,"start_byte":1857,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.load_entries", phase="implementation-call", span={"end_byte":2964,"end_column":1,"end_line":74,"start_byte":1857,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[LogEntry], ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.load_entries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.load_entries", phase="error", span={"end_byte":2964,"end_column":1,"end_line":74,"start_byte":1857,"start_column":1,"start_line":52}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.load_entries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.toolong.load_entries", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ToolongError_ReadFailed:
        _cott_contract_condition(True, "real.toolong.load_entries", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return (_cott_contract_condition((((not (len(sources) == 0)) or (len(entries) == 0))), "real.toolong.load_entries", "ensures:1"))
        _cott_contract_condition((False), "real.toolong.load_entries", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.load_entries", clause="ensures:1", phase="ensures", span={"end_byte":2902,"end_column":73,"end_line":68,"start_byte":2834,"start_column":5,"start_line":68}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[LogEntry], ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]:
    """Without a filter return entries unchanged. With a filter keep, in their
original order and multiplicity, exactly the entries whose text contains the
filter as a substring after mapping the ASCII letters A-Z to a-z in both
strings. Every other code point compares exactly: there is no Unicode case
folding or normalization. An empty filter keeps every entry."""
    entries = _cott_validate_abi(entries, CottList[LogEntry], path="$.entries")
    contains = _cott_validate_abi(contains, Option[str], path="$.contains")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/filter_entries.py", "26391901daaa3c5678ab77b44f6674b18c542684e27ba7e82cea88edacaafb5e", "filter_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.filter_entries")
        _result = _implementation(entries, contains)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.filter_entries"
        if _error.span is None:
            _error.span = {"end_byte":3656,"end_column":1,"end_line":89,"start_byte":2964,"start_column":1,"start_line":74}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.filter_entries", phase="implementation-call", span={"end_byte":3656,"end_column":1,"end_line":89,"start_byte":2964,"start_column":1,"start_line":74}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.filter_entries", phase="implementation-call", span={"end_byte":3656,"end_column":1,"end_line":89,"start_byte":2964,"start_column":1,"start_line":74}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[LogEntry], path="$.return")
    if not (_cott_contract_condition(((len(_result) <= len(entries))), "real.toolong.filter_entries", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.filter_entries", clause="ensures:1", phase="ensures", span={"end_byte":3485,"end_column":38,"end_line":83,"start_byte":3452,"start_column":5,"start_line":83}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = contains
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition(((_result == entries)), "real.toolong.filter_entries", "ensures:2"))
        _cott_contract_condition((False), "real.toolong.filter_entries", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.filter_entries", clause="ensures:2", phase="ensures", span={"end_byte":3550,"end_column":65,"end_line":84,"start_byte":3490,"start_column":5,"start_line":84}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = contains
        if type(_cott_match_value) is Some and True:
            needle = _cott_match_value.value
            return (_cott_contract_condition((((not (needle == "")) or (_result == entries))), "real.toolong.filter_entries", "ensures:3"))
        _cott_contract_condition((False), "real.toolong.filter_entries", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.filter_entries", clause="ensures:3", phase="ensures", span={"end_byte":3638,"end_column":88,"end_line":85,"start_byte":3555,"start_column":5,"start_line":85}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[LogEntry], path="$.return", validator=_cott_validate_abi)
    return _result

def render_entries(entries: CottList[LogEntry]) -> str:
    """Render one line per entry in order: the source path text, ":", the decimal
line number, one space and the text. Lines are joined with LF and there is no
trailing LF, so no entries render as the empty string."""
    entries = _cott_validate_abi(entries, CottList[LogEntry], path="$.entries")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/render_entries.py", "b9fe8031ead22b13e137ad1cc95fd7182c62c20cf96da12c2fbb13db10197e16", "render_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.render_entries")
        _result = _implementation(entries)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.render_entries"
        if _error.span is None:
            _error.span = {"end_byte":4067,"end_column":1,"end_line":101,"start_byte":3656,"start_column":1,"start_line":89}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.render_entries", phase="implementation-call", span={"end_byte":4067,"end_column":1,"end_line":101,"start_byte":3656,"start_column":1,"start_line":89}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.render_entries", phase="implementation-call", span={"end_byte":4067,"end_column":1,"end_line":101,"start_byte":3656,"start_column":1,"start_line":89}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition((((not (len(entries) == 0)) or (_result == ""))), "real.toolong.render_entries", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.render_entries", clause="ensures:1", phase="ensures", span={"end_byte":3994,"end_column":47,"end_line":96,"start_byte":3952,"start_column":5,"start_line":96}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len(entries) > 0)) or (":" in _result))), "real.toolong.render_entries", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.render_entries", clause="ensures:2", phase="ensures", span={"end_byte":4049,"end_column":55,"end_line":97,"start_byte":3999,"start_column":5,"start_line":97}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def execute(arguments: CottList[str]) -> Result[str, ToolongError]:
    """The toolong composition root. Call real.toolong.parse_arguments with
arguments, then real.toolong.load_entries with its sources, then
real.toolong.filter_entries with the loaded entries and its contains value,
and return real.toolong.render_entries of the kept entries. An error from
parse_arguments is returned unchanged before any file is read; an error from
load_entries is returned unchanged and nothing is filtered or rendered."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len(arguments) == 0)), "real.toolong.execute", "error:2:condition")):
        _expected_error = ToolongError_InvalidArguments
        _expected_error_span = {"end_byte":4891,"end_column":64,"end_line":115,"start_byte":4832,"start_column":5,"start_line":115}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/execute.py", "18be04bc330476c84ec450e4a40a0bf526641ddbdd0edfb70d518ba66122b9b3", "execute", expected_project_name="toolong", expected_cott_symbol="real.toolong.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.execute"
        if _error.span is None:
            _error.span = {"end_byte":4992,"end_column":1,"end_line":121,"start_byte":4067,"start_column":1,"start_line":101}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.execute", phase="implementation-call", span={"end_byte":4992,"end_column":1,"end_line":121,"start_byte":4067,"start_column":1,"start_line":101}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.execute", phase="implementation-call", span={"end_byte":4992,"end_column":1,"end_line":121,"start_byte":4067,"start_column":1,"start_line":101}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_InvalidArguments, ToolongError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.execute", phase="error", span={"end_byte":4992,"end_column":1,"end_line":121,"start_byte":4067,"start_column":1,"start_line":101}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.toolong.execute", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ToolongError_InvalidArguments:
        _cott_contract_condition(True, "real.toolong.execute", "error:3")
    if type(_result) is Err and type(_result.error) is ToolongError_ReadFailed:
        _cott_contract_condition(True, "real.toolong.execute", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return (_cott_contract_condition((((rendered == "") or (":" in rendered))), "real.toolong.execute", "ensures:1"))
        _cott_contract_condition((False), "real.toolong.execute", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.execute", clause="ensures:1", phase="ensures", span={"end_byte":4826,"end_column":79,"end_line":113,"start_byte":4752,"start_column":5,"start_line":113}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LogEntry", "ToolongError", "ToolongError_InvalidArguments", "ToolongError_ReadFailed", "ViewerOptions", "execute", "filter_entries", "load_entries", "parse_arguments", "parse_log", "render_entries"]
