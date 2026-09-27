from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.history_types import HarlequinPaths, HistoryError, HistoryError_Unavailable, HistoryFilter, HistoryFocus, HistoryFocus_List, HistoryFocus_Outcome, HistoryFocus_Program, HistoryFocus_Search, HistoryOutcome, HistoryOutcome_Close, HistoryOutcome_Reload, HistoryOutcome_Select, HistoryOutcome_Stay, HistoryScreen, HistoryStep, QueryRecord, QueryStatus, QueryStatus_Canceled, QueryStatus_Error, QueryStatus_Ok
from real.harlequin.style_types import StyledLine

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def harlequin_paths(platform: str, home: Path, environment: FrozenMap[str, str]) -> HarlequinPaths:
    """Compute Harlequin's per-user directories exactly as platformdirs does for
appname "harlequin" with appauthor False.
platform "darwin": config_dir home/Library/Application Support/harlequin,
cache_dir home/Library/Caches/harlequin, state_dir and data_dir
home/Library/Application Support/harlequin, log_dir home/Library/Logs/harlequin.
Any other platform (Linux and other Unix): config_dir $XDG_CONFIG_HOME/harlequin
(default home/.config/harlequin), cache_dir $XDG_CACHE_HOME/harlequin (default
home/.cache/harlequin), state_dir $XDG_STATE_HOME/harlequin (default
home/.local/state/harlequin), data_dir $XDG_DATA_HOME/harlequin (default
home/.local/share/harlequin), log_dir state_dir/log. An XDG variable that is
unset or blank uses the default; values are used verbatim otherwise.
query_log is state_dir/history.db, buffer_cache is cache_dir/buffers-1.json and
crash_dir is log_dir."""
    platform = _cott_normalize_f32_abi(platform, str, path="$.platform")
    home = _cott_normalize_f32_abi(home, Path, path="$.home")
    environment = _cott_normalize_f32_abi(environment, FrozenMap[str, str], path="$.environment")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/harlequin_paths.py", "75cd691ca3e719efc09ede115dcaf639d785021adec0093ec75ab637770950d1", "harlequin_paths", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.harlequin_paths")
        _result = _implementation(platform, home, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.harlequin_paths"
        if _error.span is None:
            _error.span = {"end_byte":3464,"end_column":1,"end_line":110,"start_byte":2397,"start_column":1,"start_line":91}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.harlequin_paths", phase="implementation-call", span={"end_byte":3464,"end_column":1,"end_line":110,"start_byte":2397,"start_column":1,"start_line":91}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.harlequin_paths", phase="implementation-call", span={"end_byte":3464,"end_column":1,"end_line":110,"start_byte":2397,"start_column":1,"start_line":91}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, HarlequinPaths, path="$.return")
    _result = _cott_wrap_async_protocol(_result, HarlequinPaths, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def record_query(log_path: Path, record: QueryRecord) -> Result[I64, HistoryError]:
    """Append record to the SQLite query log at log_path and return its row id.
The store is created on first use: create missing parent directories with
mode 0700, open with sqlite3 (busy timeout 5000 ms, journal_mode WAL when the
file system allows it, synchronous NORMAL), set file mode 0600 on a new file,
and create the table when absent:
queries(id INTEGER PRIMARY KEY, run_at TEXT NOT NULL, program TEXT NOT NULL,
connection TEXT, profile TEXT, adapter TEXT, sql TEXT NOT NULL, status TEXT
NOT NULL, rows INTEGER, truncated INTEGER, elapsed_ms REAL, error_text TEXT) with
index queries_by_connection on (connection, id DESC), and PRAGMA user_version
1. status is stored as "ok", "error" or "canceled"; truncated as 0/1 or NULL.
The first write in a process also trims the table to its newest 100000 rows.
Any failure to open, create or write is Unavailable(log_path, message) with
the error text; logging never raises."""
    log_path = _cott_normalize_f32_abi(log_path, Path, path="$.log_path")
    record = _cott_normalize_f32_abi(record, QueryRecord, path="$.record")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/record_query.py", "9badcab25b53a1d0275e45f02d58acd497bd56ab5aec10100f73fd918bd376cc", "record_query", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.record_query")
        _result = _implementation(log_path, record)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.record_query"
        if _error.span is None:
            _error.span = {"end_byte":4729,"end_column":1,"end_line":134,"start_byte":3464,"start_column":1,"start_line":110}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.record_query", phase="implementation-call", span={"end_byte":4729,"end_column":1,"end_line":134,"start_byte":3464,"start_column":1,"start_line":110}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.record_query", phase="implementation-call", span={"end_byte":4729,"end_column":1,"end_line":134,"start_byte":3464,"start_column":1,"start_line":110}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[I64, HistoryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.history.record_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (HistoryError_Unavailable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.history.record_query", phase="error", span={"end_byte":4729,"end_column":1,"end_line":134,"start_byte":3464,"start_column":1,"start_line":110}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.history.record_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.history.record_query", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is HistoryError_Unavailable:
            _cott_contract_condition(True, "real.harlequin.history.record_query", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                row = _cott_match_value.value
                return (_cott_contract_condition(((row > 0)), "real.harlequin.history.record_query", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.history.record_query", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.record_query", clause="ensures:1", phase="ensures", span={"end_byte":4576,"end_column":38,"end_line":127,"start_byte":4543,"start_column":5,"start_line":127}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is HistoryError_Unavailable and True and True:
                path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((path == log_path)), "real.harlequin.history.record_query", "ensures:2"))
            _cott_contract_condition((False), "real.harlequin.history.record_query", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.record_query", clause="ensures:2", phase="ensures", span={"end_byte":4654,"end_column":78,"end_line":128,"start_byte":4581,"start_column":5,"start_line":128}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[I64, HistoryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def update_query(log_path: Path, row: I64, status: QueryStatus, rows: Option[I64], truncated: Option[bool], elapsed_ms: Option[F64], failure: Option[str]) -> Result[Unit, HistoryError]:
    """Fill in the outcome of a logged statement once it is known: set status,
rows, truncated, elapsed_ms (rounded to 3 decimals) and error_text (from failure) of the row
with this id in the log at log_path. A missing row is not an error. Any
failure is Unavailable(log_path, message)."""
    log_path = _cott_normalize_f32_abi(log_path, Path, path="$.log_path")
    row = _cott_normalize_f32_abi(row, I64, path="$.row")
    status = _cott_normalize_f32_abi(status, QueryStatus, path="$.status")
    rows = _cott_normalize_f32_abi(rows, Option[I64], path="$.rows")
    truncated = _cott_normalize_f32_abi(truncated, Option[bool], path="$.truncated")
    elapsed_ms = _cott_normalize_f32_abi(elapsed_ms, Option[F64], path="$.elapsed_ms")
    failure = _cott_normalize_f32_abi(failure, Option[str], path="$.failure")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/update_query.py", "e48ec2a7c972aea05914e7e8f7e1c378c6065201b79d8f6727e7eb68a8065be6", "update_query", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.update_query")
        _result = _implementation(log_path, row, status, rows, truncated, elapsed_ms, failure)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.update_query"
        if _error.span is None:
            _error.span = {"end_byte":5456,"end_column":1,"end_line":157,"start_byte":4729,"start_column":1,"start_line":134}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.update_query", phase="implementation-call", span={"end_byte":5456,"end_column":1,"end_line":157,"start_byte":4729,"start_column":1,"start_line":134}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.update_query", phase="implementation-call", span={"end_byte":5456,"end_column":1,"end_line":157,"start_byte":4729,"start_column":1,"start_line":134}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, HistoryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.history.update_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (HistoryError_Unavailable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.history.update_query", phase="error", span={"end_byte":5456,"end_column":1,"end_line":157,"start_byte":4729,"start_column":1,"start_line":134}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.history.update_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.history.update_query", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is HistoryError_Unavailable:
            _cott_contract_condition(True, "real.harlequin.history.update_query", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.history.update_query", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.history.update_query", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.update_query", clause="ensures:1", phase="ensures", span={"end_byte":5303,"end_column":42,"end_line":150,"start_byte":5266,"start_column":5,"start_line":150}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is HistoryError_Unavailable and True and True:
                path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((path == log_path)), "real.harlequin.history.update_query", "ensures:2"))
            _cott_contract_condition((False), "real.harlequin.history.update_query", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.update_query", clause="ensures:2", phase="ensures", span={"end_byte":5381,"end_column":78,"end_line":151,"start_byte":5308,"start_column":5,"start_line":151}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, HistoryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def recent_queries(log_path: Path, filter: HistoryFilter, limit: Option[U64]) -> Result[CottList[QueryRecord], HistoryError]:
    """Read the log at log_path newest first (descending id), keeping rows that
match filter, at most limit rows (all rows for Nothing). The search is a
SQL LIKE '%term%' with "\\\\", "%" and "_" escaped by a backslash (ESCAPE
'\\\\'). A log file that does not exist, or has no queries table, yields an
empty list; reading never creates or migrates the store (open it read-only
with a 250 ms busy timeout). Other failures are Unavailable(log_path,
message). Rows with a status other than ok/error/canceled are skipped."""
    log_path = _cott_normalize_f32_abi(log_path, Path, path="$.log_path")
    filter = _cott_normalize_f32_abi(filter, HistoryFilter, path="$.filter")
    limit = _cott_normalize_f32_abi(limit, Option[U64], path="$.limit")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/recent_queries.py", "79d40ed51f63c2289bc64c408631c86ba704eb62fec40806753a9e6691f0308d", "recent_queries", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.recent_queries")
        _result = _implementation(log_path, filter, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.recent_queries"
        if _error.span is None:
            _error.span = {"end_byte":6328,"end_column":1,"end_line":179,"start_byte":5456,"start_column":1,"start_line":157}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.recent_queries", phase="implementation-call", span={"end_byte":6328,"end_column":1,"end_line":179,"start_byte":5456,"start_column":1,"start_line":157}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.recent_queries", phase="implementation-call", span={"end_byte":6328,"end_column":1,"end_line":179,"start_byte":5456,"start_column":1,"start_line":157}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[QueryRecord], HistoryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.history.recent_queries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (HistoryError_Unavailable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.history.recent_queries", phase="error", span={"end_byte":6328,"end_column":1,"end_line":179,"start_byte":5456,"start_column":1,"start_line":157}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.history.recent_queries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.history.recent_queries", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is HistoryError_Unavailable:
            _cott_contract_condition(True, "real.harlequin.history.recent_queries", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                records = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.history.recent_queries", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.history.recent_queries", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.recent_queries", clause="ensures:1", phase="ensures", span={"end_byte":6187,"end_column":39,"end_line":172,"start_byte":6153,"start_column":5,"start_line":172}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is HistoryError_Unavailable and True and True:
                path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((path == log_path)), "real.harlequin.history.recent_queries", "ensures:2"))
            _cott_contract_condition((False), "real.harlequin.history.recent_queries", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.recent_queries", clause="ensures:2", phase="ensures", span={"end_byte":6265,"end_column":78,"end_line":173,"start_byte":6192,"start_column":5,"start_line":173}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[QueryRecord], HistoryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def history_label(record: QueryRecord, timezone_offset_minutes: I64) -> str:
    """The status line Harlequin's history list shows for one record:
the run_at time shifted by timezone_offset_minutes and formatted
"%a, %b %d %H:%M:%S", two spaces, then the outcome. For status other than
Ok the outcome is the upper-case status ("ERROR", "CANCELED"). For Ok it is
"{n} record" / "{n} records" (n formatted with plain decimal digits) when
rows is Some and nonzero, otherwise "SUCCESS", followed by
" in {seconds:.2f}s" when elapsed_ms is Some (seconds = elapsed_ms / 1000).
A run_at that does not parse as ISO-8601 is shown verbatim."""
    record = _cott_normalize_f32_abi(record, QueryRecord, path="$.record")
    timezone_offset_minutes = _cott_normalize_f32_abi(timezone_offset_minutes, I64, path="$.timezone_offset_minutes")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/history_label.py", "2efe5d1bb37fd4f2d3ab397b91ea462113c7c96ac63fc4edab9de425e9051d5b", "history_label", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.history_label")
        _result = _implementation(record, timezone_offset_minutes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.history_label"
        if _error.span is None:
            _error.span = {"end_byte":7020,"end_column":1,"end_line":193,"start_byte":6328,"start_column":1,"start_line":179}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.history_label", phase="implementation-call", span={"end_byte":7020,"end_column":1,"end_line":193,"start_byte":6328,"start_column":1,"start_line":179}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.history_label", phase="implementation-call", span={"end_byte":7020,"end_column":1,"end_line":193,"start_byte":6328,"start_column":1,"start_line":179}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def history_preview(sql: str) -> CottList[str]:
    """The query lines a history row shows: sql stripped and split into lines;
with more than 8 lines, the first 7 followed by "… (N more lines)" where N
is the number of lines not shown."""
    sql = _cott_normalize_f32_abi(sql, str, path="$.sql")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/history_preview.py", "1f802f706d96e9f507fd6d5154a513f6c8fcf7acc1f934bb6abcb3d2ff1c3004", "history_preview", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.history_preview")
        _result = _implementation(sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.history_preview"
        if _error.span is None:
            _error.span = {"end_byte":7324,"end_column":1,"end_line":204,"start_byte":7020,"start_column":1,"start_line":193}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.history_preview", phase="implementation-call", span={"end_byte":7324,"end_column":1,"end_line":204,"start_byte":7020,"start_column":1,"start_line":193}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.history_preview", phase="implementation-call", span={"end_byte":7324,"end_column":1,"end_line":204,"start_byte":7020,"start_column":1,"start_line":193}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= 8)), "real.harlequin.history.history_preview", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.history_preview", clause="ensures:1", phase="ensures", span={"end_byte":7306,"end_column":28,"end_line":200,"start_byte":7283,"start_column":5,"start_line":200}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def open_history_screen(connection: str) -> HistoryScreen:
    """The initial History screen for the active connection: filter with
connection Some(connection), empty search, no program or status; filters
hidden; focus List; everything else 0."""
    connection = _cott_normalize_f32_abi(connection, str, path="$.connection")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/open_history_screen.py", "1ce2fce6351543e8384e8ddb8e5e9bfd48f949ebd55e04e5861af73b55e88292", "open_history_screen", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.open_history_screen")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.open_history_screen"
        if _error.span is None:
            _error.span = {"end_byte":7771,"end_column":1,"end_line":217,"start_byte":7324,"start_column":1,"start_line":204}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.open_history_screen", phase="implementation-call", span={"end_byte":7771,"end_column":1,"end_line":217,"start_byte":7324,"start_column":1,"start_line":204}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.open_history_screen", phase="implementation-call", span={"end_byte":7771,"end_column":1,"end_line":217,"start_byte":7324,"start_column":1,"start_line":204}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, HistoryScreen, path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = ((_result).filter).connection
            if type(_cott_match_value) is Some and True:
                active = _cott_match_value.value
                return (_cott_contract_condition(((active == connection)), "real.harlequin.history.open_history_screen", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.history.open_history_screen", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.open_history_screen", clause="ensures:1", phase="ensures", span={"end_byte":7681,"end_column":89,"end_line":211,"start_byte":7597,"start_column":5,"start_line":211}, expected="true", actual="false")
        if not (_cott_contract_condition(((not (_result).filters_visible)), "real.harlequin.history.open_history_screen", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.open_history_screen", clause="ensures:2", phase="ensures", span={"end_byte":7720,"end_column":39,"end_line":212,"start_byte":7686,"start_column":5,"start_line":212}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).selected == 0)), "real.harlequin.history.open_history_screen", "ensures:3")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.open_history_screen", clause="ensures:3", phase="ensures", span={"end_byte":7753,"end_column":33,"end_line":213,"start_byte":7725,"start_column":5,"start_line":213}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, HistoryScreen, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def history_key(screen: HistoryScreen, records: CottList[QueryRecord], key: str, text: str) -> HistoryStep:
    """Apply one key to the History screen, as Harlequin's history screen reacts.
key is a normalized Textual key name; text is the printable character the key
produced ("" when none). records are the records currently shown.
- "escape": when filters are visible and focus is Search with a nonempty
  search, clear the search (Reload); when filters are visible otherwise,
  hide them and clear search, program and status (Reload); when filters are
  hidden, Close.
- "ctrl+f": toggle filters_visible; showing focuses Search, hiding clears
  search, program and status and focuses List (Reload when anything was
  cleared, else Stay).
- "enter": on List with records, Select(records[selected].sql); on Search,
  focus List; on Program or Outcome, cycle that choice (Program: Nothing ->
  "harlequin" -> "hsql" -> Nothing; Outcome: Nothing -> Ok -> Error ->
  Canceled -> Nothing) and Reload.
- "tab"/"shift+tab" while filters are visible: move focus forward/backward
  through Search, Program, Outcome, List (wrapping).
- On List: "up"/"down" move selected by one, "pageup"/"pagedown" by 10,
  "home"/"end" to the first/last record, clamped; any printable text
  (single character, not a space-only key name) shows filters, focuses
  Search, appends text to the search and Reloads.
- On Search: printable text inserts at search_cursor; "backspace" deletes
  before it, "delete" after it; "left"/"right"/"home"/"end" move the caret;
  every change of the search Reloads.
- Every other key: Stay.
A Reload resets selected and first_row to 0. selected is always clamped to
the records."""
    screen = _cott_normalize_f32_abi(screen, HistoryScreen, path="$.screen")
    records = _cott_normalize_f32_abi(records, CottList[QueryRecord], path="$.records")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/history_key.py", "e519027e6c7a3c2a59725436e513b7291d13db54e7ec0abad56bc0fb54d6713d", "history_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.history_key")
        _result = _implementation(screen, records, key, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.history_key"
        if _error.span is None:
            _error.span = {"end_byte":9609,"end_column":1,"end_line":254,"start_byte":7771,"start_column":1,"start_line":217}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.history_key", phase="implementation-call", span={"end_byte":9609,"end_column":1,"end_line":254,"start_byte":7771,"start_column":1,"start_line":217}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.history_key", phase="implementation-call", span={"end_byte":9609,"end_column":1,"end_line":254,"start_byte":7771,"start_column":1,"start_line":217}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, HistoryStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, HistoryStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_history(screen: HistoryScreen, records: CottList[QueryRecord], width: U64, height: U64, timezone_offset_minutes: I64) -> CottList[StyledLine]:
    """Draw the History screen body into width x height cells.
Line 1: the title "Query History" styled "class:hq.dialog.title" followed by
" — " and the list subtitle "No matching queries", "1 query" or
"{n} queries" styled "class:hq.muted".
When filters are visible, line 2 is: "Search: " then the search text or the
placeholder "Filter by query text" (styled "class:hq.muted" when the search
is empty), then "  Program: " and the program or "Any program", then
"  Outcome: " and the status ("ok", "error", "canceled") or "Any outcome";
the focused filter's value span carries " class:hq.cursor".
Then a list area and a preview area: the list takes the upper part and shows,
for each record from first_row (moved minimally so selected is visible), its
history_label line (styled "class:hq.error" when status is not Ok, else
"class:hq.text") followed by its history_preview lines indented two spaces
(styled "class:hq.muted"), with " class:hq.selection" added to every line of
the selected record; the preview shows up to 8 lines starting with
"Highlighted Query Preview" (styled "class:hq.title") and the selected
record's sql lines. The footer line is "Enter: Select  Ctrl+F: Filter
Esc: Cancel" styled "class:hq.footer". Lines are cut at width cells and at
most height lines are returned. Render only lines of actual content:
do not pad either the record list or the preview with blank rows to fill
height. The terminal widget paints unused space. In particular, an empty
history returns at most title, optional filters, preview heading and footer
regardless of how large height is; computation and allocation must not be
proportional to empty terminal space."""
    screen = _cott_normalize_f32_abi(screen, HistoryScreen, path="$.screen")
    records = _cott_normalize_f32_abi(records, CottList[QueryRecord], path="$.records")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    height = _cott_normalize_f32_abi(height, U64, path="$.height")
    timezone_offset_minutes = _cott_normalize_f32_abi(timezone_offset_minutes, I64, path="$.timezone_offset_minutes")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/history/render_history.py", "cb1b7ac02021df9389f38e8bce9e7802761414f2077cd9e7e6cb4457c385fd3b", "render_history", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.history.render_history")
        _result = _implementation(screen, records, width, height, timezone_offset_minutes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.history.render_history"
        if _error.span is None:
            _error.span = {"end_byte":11651,"end_column":1,"end_line":293,"start_byte":9609,"start_column":1,"start_line":254}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.history.render_history", phase="implementation-call", span={"end_byte":11651,"end_column":1,"end_line":293,"start_byte":9609,"start_column":1,"start_line":254}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.history.render_history", phase="implementation-call", span={"end_byte":11651,"end_column":1,"end_line":293,"start_byte":9609,"start_column":1,"start_line":254}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= height)), "real.harlequin.history.render_history", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.render_history", clause="ensures:1", phase="ensures", span={"end_byte":11585,"end_column":33,"end_line":288,"start_byte":11557,"start_column":5,"start_line":288}, expected="true", actual="false")
        if not (_cott_contract_condition((((not (len(records) == 0)) or (len(_result) <= 4))), "real.harlequin.history.render_history", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.history.render_history", clause="ensures:2", phase="ensures", span={"end_byte":11633,"end_column":48,"end_line":289,"start_byte":11590,"start_column":5,"start_line":289}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["HarlequinPaths", "HistoryError", "HistoryError_Unavailable", "HistoryFilter", "HistoryFocus", "HistoryFocus_List", "HistoryFocus_Outcome", "HistoryFocus_Program", "HistoryFocus_Search", "HistoryOutcome", "HistoryOutcome_Close", "HistoryOutcome_Reload", "HistoryOutcome_Select", "HistoryOutcome_Stay", "HistoryScreen", "HistoryStep", "QueryRecord", "QueryStatus", "QueryStatus_Canceled", "QueryStatus_Error", "QueryStatus_Ok", "harlequin_paths", "history_key", "history_label", "history_preview", "open_history_screen", "recent_queries", "record_query", "render_history", "update_query"]
