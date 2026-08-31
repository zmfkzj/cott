from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.toolong_types import LogEntry, ToolongError, ToolongError_InvalidArguments, ToolongError_ReadFailed, ViewerOptions

def parse_arguments(arguments: CottList[str]) -> Result[ViewerOptions, ToolongError]:
    """Parse [--contains TEXT] followed by one or more log paths."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/parse_arguments.py", "bd0df7e058f57cbddde47aa9e3311b3b71c5f0a87481899452c5c2ce952a32b2", "parse_arguments", expected_project_name="toolong", expected_cott_symbol="real.toolong.parse_arguments")
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
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return ((len((options).sources) > 0))
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
        _implementation = _cott_load("_cott_impl/real/toolong/load_entries.py", "c7b9d559d4a88bebffda092dd9dfb887b6ce39cb414bf80b07a6869f5a8aa5e7", "load_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.load_entries")
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
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return ((len(sources) > 0))
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
        _implementation = _cott_load("_cott_impl/real/toolong/filter_entries.py", "f12bb90139231155d801ec61e130fa01c8c0668f052abdb35136c4ad16a53571", "filter_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.filter_entries")
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
        _implementation = _cott_load("_cott_impl/real/toolong/render_entries.py", "6c8020ec71d266ea6fc539f6133b3b239f24657f6d1cf1ce834a57d479e86ae8", "render_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.render_entries")
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
    """Parse arguments, load logs, apply the optional filter, and render matching entries."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/execute.py", "92cec9de3dd5238cd5ebec7dcbe7ca205da8ca2272ca6337479a0e42a7633e94", "execute", expected_project_name="toolong", expected_cott_symbol="real.toolong.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.execute"
        if _error.span is None:
            _error.span = {"end_byte":1512,"end_column":1,"end_line":63,"start_byte":1187,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.execute", phase="implementation-call", span={"end_byte":1512,"end_column":1,"end_line":63,"start_byte":1187,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.execute", phase="implementation-call", span={"end_byte":1512,"end_column":1,"end_line":63,"start_byte":1187,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_InvalidArguments, ToolongError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.execute", phase="error", span={"end_byte":1512,"end_column":1,"end_line":63,"start_byte":1187,"start_column":1,"start_line":52}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return ((len(arguments) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.execute", clause="ensures:1", phase="ensures", span={"end_byte":1411,"end_column":53,"end_line":57,"start_byte":1363,"start_column":5,"start_line":57}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LogEntry", "ToolongError", "ToolongError_InvalidArguments", "ToolongError_ReadFailed", "ViewerOptions", "execute", "filter_entries", "load_entries", "parse_arguments", "render_entries"]
