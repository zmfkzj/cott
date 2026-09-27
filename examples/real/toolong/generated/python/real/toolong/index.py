from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from real.toolong.model_types import FileIndex, FileTimestamps, LineLocation, MergedIndex, TabIndex

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def start_file_index(size: U64) -> FileIndex:
    """The index of a single file before its line breaks are scanned. Toolong's
backwards scan always records the content size itself as a break before
any LF offset, so for a non-empty file breaks is an opaque tuple containing
size; an empty file has no breaks. scan_start is size and scanned_size is 0."""
    size = _cott_normalize_f32_abi(size, U64, path="$.size")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/start_file_index.py", "7796a61b7def81d6a53a0f9abba1e4261a0a8b46bd73484d37dab585b739b156", "start_file_index", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.start_file_index")
        _result = _implementation(size)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.start_file_index"
        if _error.span is None:
            _error.span = {"end_byte":661,"end_column":1,"end_line":27,"start_byte":189,"start_column":1,"start_line":14}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.start_file_index", phase="implementation-call", span={"end_byte":661,"end_column":1,"end_line":27,"start_byte":189,"start_column":1,"start_line":14}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.start_file_index", phase="implementation-call", span={"end_byte":661,"end_column":1,"end_line":27,"start_byte":189,"start_column":1,"start_line":14}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FileIndex, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).scan_start == size)), "real.toolong.index.start_file_index", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.start_file_index", clause="ensures:1", phase="ensures", span={"end_byte":606,"end_column":38,"end_line":22,"start_byte":573,"start_column":5,"start_line":22}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).scanned_size == 0)), "real.toolong.index.start_file_index", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.start_file_index", clause="ensures:2", phase="ensures", span={"end_byte":643,"end_column":37,"end_line":23,"start_byte":611,"start_column":5,"start_line":23}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FileIndex, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def add_scanned_breaks(index: FileIndex, breaks: Opaque[Literal["file_breaks"]], position: U64) -> FileIndex:
    """Record one batch of a backwards scan: scan_start becomes position (the
offset the scan has reached) and breaks becomes the ascending sort of the
existing breaks followed by the new ones (duplicates kept).
scanned_size is unchanged."""
    index = _cott_normalize_f32_abi(index, FileIndex, path="$.index")
    breaks = _cott_normalize_f32_abi(breaks, Opaque[Literal["file_breaks"]], path="$.breaks")
    position = _cott_normalize_f32_abi(position, U64, path="$.position")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/add_scanned_breaks.py", "d621d3b82d5836a9e3cf371b7169bb43a50c6c51e2c3adf8a305d3feb674c52c", "add_scanned_breaks", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.add_scanned_breaks")
        _result = _implementation(index, breaks, position)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.add_scanned_breaks"
        if _error.span is None:
            _error.span = {"end_byte":1143,"end_column":1,"end_line":40,"start_byte":661,"start_column":1,"start_line":27}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.add_scanned_breaks", phase="implementation-call", span={"end_byte":1143,"end_column":1,"end_line":40,"start_byte":661,"start_column":1,"start_line":27}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.add_scanned_breaks", phase="implementation-call", span={"end_byte":1143,"end_column":1,"end_line":40,"start_byte":661,"start_column":1,"start_line":27}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FileIndex, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).scan_start == position)), "real.toolong.index.add_scanned_breaks", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.add_scanned_breaks", clause="ensures:1", phase="ensures", span={"end_byte":1071,"end_column":42,"end_line":35,"start_byte":1034,"start_column":5,"start_line":35}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).scanned_size == (index).scanned_size)), "real.toolong.index.add_scanned_breaks", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.add_scanned_breaks", clause="ensures:2", phase="ensures", span={"end_byte":1125,"end_column":54,"end_line":36,"start_byte":1076,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FileIndex, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def complete_file_scan(index: FileIndex, size: U64, position: U64) -> FileIndex:
    """Finish (or stop) the backwards scan: scanned_size becomes the larger of
its current value and size, scan_start becomes position (0 when the whole
file was scanned, the last reached offset when the scan was cancelled).
breaks are unchanged."""
    index = _cott_normalize_f32_abi(index, FileIndex, path="$.index")
    size = _cott_normalize_f32_abi(size, U64, path="$.size")
    position = _cott_normalize_f32_abi(position, U64, path="$.position")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/complete_file_scan.py", "81ed172cabfd11057d4bad048f1ec38c149bdfa50b7f6ed124949e3c6502c040", "complete_file_scan", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.complete_file_scan")
        _result = _implementation(index, size, position)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.complete_file_scan"
        if _error.span is None:
            _error.span = {"end_byte":1599,"end_column":1,"end_line":53,"start_byte":1143,"start_column":1,"start_line":40}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.complete_file_scan", phase="implementation-call", span={"end_byte":1599,"end_column":1,"end_line":53,"start_byte":1143,"start_column":1,"start_line":40}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.complete_file_scan", phase="implementation-call", span={"end_byte":1599,"end_column":1,"end_line":53,"start_byte":1143,"start_column":1,"start_line":40}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FileIndex, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).scan_start == position)), "real.toolong.index.complete_file_scan", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.complete_file_scan", clause="ensures:1", phase="ensures", span={"end_byte":1541,"end_column":42,"end_line":48,"start_byte":1504,"start_column":5,"start_line":48}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).scanned_size >= size)), "real.toolong.index.complete_file_scan", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.complete_file_scan", clause="ensures:2", phase="ensures", span={"end_byte":1581,"end_column":40,"end_line":49,"start_byte":1546,"start_column":5,"start_line":49}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FileIndex, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def add_tail_breaks(index: FileIndex, breaks: Opaque[Literal["file_breaks"]], size: U64) -> FileIndex:
    """Record LF offsets read while tailing: they are appended in the given order
without sorting, and scanned_size becomes the larger of its current value
and size. scan_start is unchanged."""
    index = _cott_normalize_f32_abi(index, FileIndex, path="$.index")
    breaks = _cott_normalize_f32_abi(breaks, Opaque[Literal["file_breaks"]], path="$.breaks")
    size = _cott_normalize_f32_abi(size, U64, path="$.size")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/add_tail_breaks.py", "6e6b58874b8d4ed27d73bcfbcef96fc62a7ec0d1135dec1754b68a8b77fcd37a", "add_tail_breaks", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.add_tail_breaks")
        _result = _implementation(index, breaks, size)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.add_tail_breaks"
        if _error.span is None:
            _error.span = {"end_byte":2016,"end_column":1,"end_line":65,"start_byte":1599,"start_column":1,"start_line":53}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.add_tail_breaks", phase="implementation-call", span={"end_byte":2016,"end_column":1,"end_line":65,"start_byte":1599,"start_column":1,"start_line":53}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.add_tail_breaks", phase="implementation-call", span={"end_byte":2016,"end_column":1,"end_line":65,"start_byte":1599,"start_column":1,"start_line":53}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FileIndex, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).scan_start == (index).scan_start)), "real.toolong.index.add_tail_breaks", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.add_tail_breaks", clause="ensures:1", phase="ensures", span={"end_byte":1958,"end_column":50,"end_line":60,"start_byte":1913,"start_column":5,"start_line":60}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).scanned_size >= size)), "real.toolong.index.add_tail_breaks", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.add_tail_breaks", clause="ensures:2", phase="ensures", span={"end_byte":1998,"end_column":40,"end_line":61,"start_byte":1963,"start_column":5,"start_line":61}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FileIndex, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def file_line_count(index: FileIndex) -> U64:
    """Toolong's displayed line count of a single file: the number of breaks, but
at least 1."""
    index = _cott_normalize_f32_abi(index, FileIndex, path="$.index")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/file_line_count.py", "4d6c209e6fd32fe678f1a8382be14d33f7e064b90914ede65da5971ec02df5fe", "file_line_count", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.file_line_count")
        _result = _implementation(index)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.file_line_count"
        if _error.span is None:
            _error.span = {"end_byte":2218,"end_column":1,"end_line":75,"start_byte":2016,"start_column":1,"start_line":65}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.file_line_count", phase="implementation-call", span={"end_byte":2218,"end_column":1,"end_line":75,"start_byte":2016,"start_column":1,"start_line":65}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.file_line_count", phase="implementation-call", span={"end_byte":2218,"end_column":1,"end_line":75,"start_byte":2016,"start_column":1,"start_line":65}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, U64, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((_result >= 1)), "real.toolong.index.file_line_count", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.index.file_line_count", clause="ensures:1", phase="ensures", span={"end_byte":2200,"end_column":24,"end_line":71,"start_byte":2181,"start_column":5,"start_line":71}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def merge_timestamps(files: CottList[FileTimestamps], complete: bool) -> MergedIndex:
    """Toolong's merge of several files by timestamp. File i of files is file
index i of the merged view.

breaks: for an opened file with at least one entry, the end offsets of its
entries in order followed by its size; otherwise an empty list. breaks has
one element per file.

lines: for each opened file in order, one MergedLine(seconds, line, file)
per entry in entry order, after back-filling a missing header timestamp:
scanning the file's entries from the first, the first entry with non-zero
seconds among the first twelve entries (positions 0 to 11) gives its
seconds to every earlier entry of that file; when none of them has
non-zero seconds nothing is back-filled. Entries that still have 0.0
seconds keep it (they sort before every timestamped line). When complete
is true, the concatenated lines are stably sorted by (seconds, line), so
equal keys keep file order; when complete is false (a cancelled merge) they
stay in file order.

scanned_size is the sum of the sizes of all files.
Each file's timestamp entries and the completed merged indexes use
opaque tuples: inspect them inside this implementation, not via a
recursively traversed facade value."""
    files = _cott_normalize_f32_abi(files, CottList[FileTimestamps], path="$.files")
    complete = _cott_normalize_f32_abi(complete, bool, path="$.complete")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/merge_timestamps.py", "46789e25638306caa5a4f51c738d050c4bf05887e96d589a8177bb30ee3f4aef", "merge_timestamps", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.merge_timestamps")
        _result = _implementation(files, complete)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.merge_timestamps"
        if _error.span is None:
            _error.span = {"end_byte":3586,"end_column":1,"end_line":103,"start_byte":2218,"start_column":1,"start_line":75}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.merge_timestamps", phase="implementation-call", span={"end_byte":3586,"end_column":1,"end_line":103,"start_byte":2218,"start_column":1,"start_line":75}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.merge_timestamps", phase="implementation-call", span={"end_byte":3586,"end_column":1,"end_line":103,"start_byte":2218,"start_column":1,"start_line":75}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, MergedIndex, path="$.return")
    _result = _cott_wrap_async_protocol(_result, MergedIndex, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def line_location(index: TabIndex, line: U64) -> LineLocation:
    """Toolong's index_to_span: where displayed line number line (zero-based)
lives.

Single(file_index): the file is 0; with breaks b (length n), scan_start s
and scanned_size z: when n is 0 the span is (s, s); otherwise let i be
line clamped to at most n; i == 0 gives (s, b[0]); otherwise the span
starts at b[i - 1] and ends at b[i] when i < n, else at z - 1 (0 when z is
0). Spans of lines after the first therefore start at the preceding LF.

Merged(merged_index): when line < lines.len the file and the file's own
line number come from lines[line]; otherwise the file is 0 and the file's
own line number is line. The span is then computed exactly like Single
using that file's breaks (an empty list when the file has none), scan
start 0 and the merged scanned_size.
The index payloads are immutable tuples; unwrap and index them directly.
Do not allocate copies of all breaks or merged lines per lookup: this
callable runs once for each visible row and each search candidate."""
    index = _cott_normalize_f32_abi(index, TabIndex, path="$.index")
    line = _cott_normalize_f32_abi(line, U64, path="$.line")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/index/line_location.py", "f28f8d77efd88c12fc3e918ea2c65ae53fa67eb4a9a529f21064e2e12eefbec8", "line_location", expected_project_name="toolong", expected_cott_symbol="real.toolong.index.line_location")
        _result = _implementation(index, line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.index.line_location"
        if _error.span is None:
            _error.span = {"end_byte":4729,"end_column":1,"end_line":126,"start_byte":3586,"start_column":1,"start_line":103}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.index.line_location", phase="implementation-call", span={"end_byte":4729,"end_column":1,"end_line":126,"start_byte":3586,"start_column":1,"start_line":103}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.index.line_location", phase="implementation-call", span={"end_byte":4729,"end_column":1,"end_line":126,"start_byte":3586,"start_column":1,"start_line":103}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, LineLocation, path="$.return")
    _result = _cott_wrap_async_protocol(_result, LineLocation, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["add_scanned_breaks", "add_tail_breaks", "complete_file_scan", "file_line_count", "line_location", "merge_timestamps", "start_file_index"]
