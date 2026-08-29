from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.toolong_types import EntryKind, EntryKind_Access, EntryKind_Error, EntryKind_Json, EntryKind_Plain, LogEntry, LogPage, LogSource, ToolongError, ToolongError_CompressedAppendUnsupported, ToolongError_DecodeFailed, ToolongError_InvalidIndent, ToolongError_InvalidLimit, ToolongError_InvalidOffset, ToolongError_OpenFailed

def load_log(source: LogSource, limit: U64) -> Result[LogPage, ToolongError]:
    source = _cott_validate_abi(source, LogSource, path="$.source")
    limit = _cott_validate_abi(limit, U64, path="$.limit")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((limit == 0)):
        _expected_error = ToolongError_InvalidLimit
        _expected_error_span = {"end_byte":801,"end_column":52,"end_line":38,"start_byte":754,"start_column":5,"start_line":38}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/load_log.py", "69bbf8e7580f68be98eec10eb165f8fd8dc9e04c6df5f41a7e9086ee115e161e", "load_log", expected_project_name="toolong", expected_cott_symbol="real.toolong.load_log")
        _result = _implementation(source, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.load_log"
        if _error.span is None:
            _error.span = {"end_byte":898,"end_column":1,"end_line":44,"start_byte":562,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.load_log", phase="implementation-call", span={"end_byte":898,"end_column":1,"end_line":44,"start_byte":562,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.load_log", phase="implementation-call", span={"end_byte":898,"end_column":1,"end_line":44,"start_byte":562,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LogPage, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.load_log", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_OpenFailed, ToolongError_DecodeFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.load_log", phase="error", span={"end_byte":898,"end_column":1,"end_line":44,"start_byte":562,"start_column":1,"start_line":34}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.load_log", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            page = _cott_match_value.value
            return (((page).source == source))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.load_log", clause="ensures:0", phase="ensures", span={"end_byte":691,"end_column":53,"end_line":35,"start_byte":643,"start_column":5,"start_line":35}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            page = _cott_match_value.value
            return ((len((page).entries) <= limit))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.load_log", clause="ensures:1", phase="ensures", span={"end_byte":748,"end_column":57,"end_line":36,"start_byte":696,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LogPage, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_jsonl(entries: CottList[LogEntry], indent: U8) -> Result[CottList[str], ToolongError]:
    entries = _cott_validate_abi(entries, CottList[LogEntry], path="$.entries")
    indent = _cott_validate_abi(indent, U8, path="$.indent")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((indent == 0)):
        _expected_error = ToolongError_InvalidIndent
        _expected_error_span = {"end_byte":1104,"end_column":54,"end_line":47,"start_byte":1055,"start_column":5,"start_line":47}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/render_jsonl.py", "8020c0e1fcc8f6375671a8410ae7e5e8d4b411c61c02f46b64f23427bbc085fb", "render_jsonl", expected_project_name="toolong", expected_cott_symbol="real.toolong.render_jsonl")
        _result = _implementation(entries, indent)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.render_jsonl"
        if _error.span is None:
            _error.span = {"end_byte":1122,"end_column":1,"end_line":51,"start_byte":898,"start_column":1,"start_line":44}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.render_jsonl", phase="implementation-call", span={"end_byte":1122,"end_column":1,"end_line":51,"start_byte":898,"start_column":1,"start_line":44}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.render_jsonl", phase="implementation-call", span={"end_byte":1122,"end_column":1,"end_line":51,"start_byte":898,"start_column":1,"start_line":44}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.render_jsonl", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.render_jsonl", phase="error", span={"end_byte":1122,"end_column":1,"end_line":51,"start_byte":898,"start_column":1,"start_line":44}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.render_jsonl", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return ((len(rendered) == len(entries)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.render_jsonl", clause="ensures:0", phase="ensures", span={"end_byte":1049,"end_column":63,"end_line":45,"start_byte":991,"start_column":5,"start_line":45}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def merge_pages(pages: CottList[LogPage], limit: U64) -> Result[CottList[LogEntry], ToolongError]:
    pages = _cott_validate_abi(pages, CottList[LogPage], path="$.pages")
    limit = _cott_validate_abi(limit, U64, path="$.limit")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((limit == 0)):
        _expected_error = ToolongError_InvalidLimit
        _expected_error_span = {"end_byte":1317,"end_column":52,"end_line":54,"start_byte":1270,"start_column":5,"start_line":54}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/merge_pages.py", "7bb8327e9a4e2b501a064c003ac1043e767433117b2b8ef523a115a980e5df8b", "merge_pages", expected_project_name="toolong", expected_cott_symbol="real.toolong.merge_pages")
        _result = _implementation(pages, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.merge_pages"
        if _error.span is None:
            _error.span = {"end_byte":1335,"end_column":1,"end_line":58,"start_byte":1122,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.merge_pages", phase="implementation-call", span={"end_byte":1335,"end_column":1,"end_line":58,"start_byte":1122,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.merge_pages", phase="implementation-call", span={"end_byte":1335,"end_column":1,"end_line":58,"start_byte":1122,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[LogEntry], ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.merge_pages", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.merge_pages", phase="error", span={"end_byte":1335,"end_column":1,"end_line":58,"start_byte":1122,"start_column":1,"start_line":51}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.merge_pages", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            merged = _cott_match_value.value
            return ((len(merged) <= limit))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.merge_pages", clause="ensures:0", phase="ensures", span={"end_byte":1264,"end_column":53,"end_line":52,"start_byte":1216,"start_column":5,"start_line":52}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[LogEntry], ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def search_entries(entries: CottList[LogEntry], needle: str, limit: U64) -> Result[CottList[LogEntry], ToolongError]:
    entries = _cott_validate_abi(entries, CottList[LogEntry], path="$.entries")
    needle = _cott_validate_abi(needle, str, path="$.needle")
    limit = _cott_validate_abi(limit, U64, path="$.limit")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((limit == 0)):
        _expected_error = ToolongError_InvalidLimit
        _expected_error_span = {"end_byte":1562,"end_column":52,"end_line":65,"start_byte":1515,"start_column":5,"start_line":65}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/search_entries.py", "fcad354e6e627a2a676d29b42b9ca456ea215ae6cd6b49d749cd258dcf3a2a5d", "search_entries", expected_project_name="toolong", expected_cott_symbol="real.toolong.search_entries")
        _result = _implementation(entries, needle, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.search_entries"
        if _error.span is None:
            _error.span = {"end_byte":1580,"end_column":1,"end_line":69,"start_byte":1335,"start_column":1,"start_line":58}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.search_entries", phase="implementation-call", span={"end_byte":1580,"end_column":1,"end_line":69,"start_byte":1335,"start_column":1,"start_line":58}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.search_entries", phase="implementation-call", span={"end_byte":1580,"end_column":1,"end_line":69,"start_byte":1335,"start_column":1,"start_line":58}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[LogEntry], ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.search_entries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.search_entries", phase="error", span={"end_byte":1580,"end_column":1,"end_line":69,"start_byte":1335,"start_column":1,"start_line":58}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.search_entries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            found = _cott_match_value.value
            return ((len(found) <= limit))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.search_entries", clause="ensures:0", phase="ensures", span={"end_byte":1509,"end_column":51,"end_line":63,"start_byte":1463,"start_column":5,"start_line":63}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[LogEntry], ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

def read_appended(source: LogSource, from_byte: U64, limit: U64) -> Result[LogPage, ToolongError]:
    source = _cott_validate_abi(source, LogSource, path="$.source")
    from_byte = _cott_validate_abi(from_byte, U64, path="$.from_byte")
    limit = _cott_validate_abi(limit, U64, path="$.limit")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((limit == 0)):
        _expected_error = ToolongError_InvalidLimit
        _expected_error_span = {"end_byte":1899,"end_column":52,"end_line":74,"start_byte":1852,"start_column":5,"start_line":74}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/read_appended.py", "31340b478ce726e851fc153f2a58153818cc917684ca95c70a057fa4fff40263", "read_appended", expected_project_name="toolong", expected_cott_symbol="real.toolong.read_appended")
        _result = _implementation(source, from_byte, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.read_appended"
        if _error.span is None:
            _error.span = {"end_byte":2083,"end_column":1,"end_line":81,"start_byte":1580,"start_column":1,"start_line":69}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.read_appended", phase="implementation-call", span={"end_byte":2083,"end_column":1,"end_line":81,"start_byte":1580,"start_column":1,"start_line":69}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.read_appended", phase="implementation-call", span={"end_byte":2083,"end_column":1,"end_line":81,"start_byte":1580,"start_column":1,"start_line":69}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LogPage, ToolongError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.toolong.read_appended", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ToolongError_InvalidOffset, ToolongError_OpenFailed, ToolongError_DecodeFailed, ToolongError_CompressedAppendUnsupported,):
            raise CottContractViolation("returned error is not allowed", symbol="real.toolong.read_appended", phase="error", span={"end_byte":2083,"end_column":1,"end_line":81,"start_byte":1580,"start_column":1,"start_line":69}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.read_appended", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            page = _cott_match_value.value
            return (((page).source == source))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.read_appended", clause="ensures:0", phase="ensures", span={"end_byte":1730,"end_column":53,"end_line":70,"start_byte":1682,"start_column":5,"start_line":70}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            page = _cott_match_value.value
            return ((len((page).entries) <= limit))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.read_appended", clause="ensures:1", phase="ensures", span={"end_byte":1787,"end_column":57,"end_line":71,"start_byte":1735,"start_column":5,"start_line":71}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            page = _cott_match_value.value
            return (((page).next_byte >= from_byte))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.toolong.read_appended", clause="ensures:2", phase="ensures", span={"end_byte":1846,"end_column":59,"end_line":72,"start_byte":1792,"start_column":5,"start_line":72}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LogPage, ToolongError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["EntryKind", "EntryKind_Access", "EntryKind_Error", "EntryKind_Json", "EntryKind_Plain", "LogEntry", "LogPage", "LogSource", "ToolongError", "ToolongError_CompressedAppendUnsupported", "ToolongError_DecodeFailed", "ToolongError_InvalidIndent", "ToolongError_InvalidLimit", "ToolongError_InvalidOffset", "ToolongError_OpenFailed", "load_log", "merge_pages", "read_appended", "render_jsonl", "search_entries"]
