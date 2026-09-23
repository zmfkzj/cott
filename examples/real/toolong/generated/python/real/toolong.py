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
    """Parse [--contains TEXT] followed by one or more log paths."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/parse_arguments.py", "0c7d4e59425ec45aa9fdc116736c454ec00cfa45a6898c81c9dd9788944bc8d3", "parse_arguments", expected_project_name="toolong", expected_cott_symbol="real.toolong.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":534,"end_column":1,"end_line":27,"start_byte":253,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.parse_arguments", phase="implementation-call", span={"end_byte":534,"end_column":1,"end_line":27,"start_byte":253,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.parse_arguments", phase="implementation-call", span={"end_byte":534,"end_column":1,"end_line":27,"start_byte":253,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ViewerOptions, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_InvalidArguments,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.parse_arguments", phase="error", span={"end_byte":534,"end_column":1,"end_line":27,"start_byte":253,"start_column":1,"start_line":16}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.toolong.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ToolongError_InvalidArguments:
        _cott_contract_condition(True, "real.toolong.parse_arguments", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return (_cott_contract_condition(((len((options).sources) > 0)), "real.toolong.parse_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.toolong.parse_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":475,"end_column":58,"end_line":21,"start_byte":422,"start_column":5,"start_line":21}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ViewerOptions, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]:
    """Read UTF-8 log lines in source order and number each source from one."""
    sources = _cott_validate_abi(sources, CottList[Path], path="$.sources")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/load_entries.py", "ad1e0c808742a5f6d7927bb3c456f58ae590acfede1c6ee5eee6f6bf793258b7", "load_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.load_entries")
        _result = _implementation(sources)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.load_entries"
        if _error.span is None:
            _error.span = {"end_byte":818,"end_column":1,"end_line":38,"start_byte":534,"start_column":1,"start_line":27}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.load_entries", phase="implementation-call", span={"end_byte":818,"end_column":1,"end_line":38,"start_byte":534,"start_column":1,"start_line":27}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.load_entries", phase="implementation-call", span={"end_byte":818,"end_column":1,"end_line":38,"start_byte":534,"start_column":1,"start_line":27}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[LogEntry], ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.load_entries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.load_entries", phase="error", span={"end_byte":818,"end_column":1,"end_line":38,"start_byte":534,"start_column":1,"start_line":27}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
            return (_cott_contract_condition(((len(sources) > 0)), "real.toolong.load_entries", "ensures:1"))
        _cott_contract_condition((False), "real.toolong.load_entries", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.load_entries", clause="ensures:1", phase="ensures", span={"end_byte":756,"end_column":50,"end_line":32,"start_byte":711,"start_column":5,"start_line":32}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[LogEntry], ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]:
    """Keep all entries without a filter; otherwise keep case-insensitive substring matches."""
    entries = _cott_validate_abi(entries, CottList[LogEntry], path="$.entries")
    contains = _cott_validate_abi(contains, Option[str], path="$.contains")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/filter_entries.py", "df319414f87f74c504c062e5446d0c2221f580bee0b213affbc47b9c39e26d3e", "filter_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.filter_entries")
        _result = _implementation(entries, contains)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.filter_entries"
        if _error.span is None:
            _error.span = {"end_byte":1030,"end_column":1,"end_line":45,"start_byte":818,"start_column":1,"start_line":38}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.filter_entries", phase="implementation-call", span={"end_byte":1030,"end_column":1,"end_line":45,"start_byte":818,"start_column":1,"start_line":38}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.filter_entries", phase="implementation-call", span={"end_byte":1030,"end_column":1,"end_line":45,"start_byte":818,"start_column":1,"start_line":38}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[LogEntry], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[LogEntry], path="$.return", validator=_cott_validate_abi)
    return _result

def render_entries(entries: CottList[LogEntry]) -> str:
    """Render path:line and text for each entry, separated by newlines."""
    entries = _cott_validate_abi(entries, CottList[LogEntry], path="$.entries")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/render_entries.py", "b9fe8031ead22b13e137ad1cc95fd7182c62c20cf96da12c2fbb13db10197e16", "render_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.render_entries")
        _result = _implementation(entries)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.render_entries"
        if _error.span is None:
            _error.span = {"end_byte":1187,"end_column":1,"end_line":52,"start_byte":1030,"start_column":1,"start_line":45}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.render_entries", phase="implementation-call", span={"end_byte":1187,"end_column":1,"end_line":52,"start_byte":1030,"start_column":1,"start_line":45}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.render_entries", phase="implementation-call", span={"end_byte":1187,"end_column":1,"end_line":52,"start_byte":1030,"start_column":1,"start_line":45}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def execute(arguments: CottList[str]) -> Result[str, ToolongError]:
    """Call real.toolong.parse_arguments, then real.toolong.load_entries on its
sources. Pass the entries and parsed contains option to real.toolong.filter_entries
and return real.toolong.render_entries of those matches.
Return an error from parsing or loading unchanged; do not load files after
argument parsing fails."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/execute.py", "068be9df5ba7ae5601310d68746f937121e58601807ef49ec78a3c0f20e3439d", "execute", expected_project_name="toolong", expected_cott_symbol="real.toolong.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.execute"
        if _error.span is None:
            _error.span = {"end_byte":1757,"end_column":1,"end_line":67,"start_byte":1187,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.execute", phase="implementation-call", span={"end_byte":1757,"end_column":1,"end_line":67,"start_byte":1187,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.execute", phase="implementation-call", span={"end_byte":1757,"end_column":1,"end_line":67,"start_byte":1187,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_InvalidArguments, ToolongError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.execute", phase="error", span={"end_byte":1757,"end_column":1,"end_line":67,"start_byte":1187,"start_column":1,"start_line":52}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.toolong.execute", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ToolongError_InvalidArguments:
        _cott_contract_condition(True, "real.toolong.execute", "error:2")
    if type(_result) is Err and type(_result.error) is ToolongError_ReadFailed:
        _cott_contract_condition(True, "real.toolong.execute", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return (_cott_contract_condition(((len(arguments) > 0)), "real.toolong.execute", "ensures:1"))
        _cott_contract_condition((False), "real.toolong.execute", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.execute", clause="ensures:1", phase="ensures", span={"end_byte":1656,"end_column":53,"end_line":61,"start_byte":1608,"start_column":5,"start_line":61}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LogEntry", "ToolongError", "ToolongError_InvalidArguments", "ToolongError_ReadFailed", "ViewerOptions", "execute", "filter_entries", "load_entries", "parse_arguments", "render_entries"]
