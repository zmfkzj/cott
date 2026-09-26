from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from real.toolong.model_types import LogTimestamp, TimeUnit, TimestampScan

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def default_timestamp_order() -> CottList[U8]:
    """The timestamp scanner's initial format order: List(0, 1, 2, ..., 16), the
indexes of the format table documented on
real.toolong.timestamps.scan_timestamp in table order."""
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/timestamps/default_timestamp_order.py", "4cb1500d20c57f0a1ad1a14c2d95317a9c8482e91a8d189a0a88669ed670e3dd", "default_timestamp_order", expected_project_name="toolong", expected_cott_symbol="real.toolong.timestamps.default_timestamp_order")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.timestamps.default_timestamp_order"
        if _error.span is None:
            _error.span = {"end_byte":388,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":5}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.timestamps.default_timestamp_order", phase="implementation-call", span={"end_byte":388,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":5}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.timestamps.default_timestamp_order", phase="implementation-call", span={"end_byte":388,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":5}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[U8], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 17)), "real.toolong.timestamps.default_timestamp_order", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.timestamps.default_timestamp_order", clause="ensures:1", phase="ensures", span={"end_byte":370,"end_column":29,"end_line":12,"start_byte":346,"start_column":5,"start_line":12}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[U8], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def scan_timestamp(line: str, order: CottList[U8]) -> TimestampScan:
    """Toolong's TimestampScanner.scan for one line. When line is longer than
10000 code points only its first 10000 code points are scanned. The format
table (index: Python regular expression -> parser) is:

0: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2},\\d{3}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
1: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2},\\d{3} -> datetime.fromisoformat
2: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
3: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3} -> datetime.fromisoformat
4: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
5: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2} -> datetime.fromisoformat
6: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2},\\d{3}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
7: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2},\\d{3} -> datetime.fromisoformat
8: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\s?(?:Z|[+-]\\d{4}Z?) -> datetime.fromisoformat
9: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3} -> datetime.fromisoformat
10: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
11: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2} -> datetime.fromisoformat
12: [JFMASOND][a-z]{2}\\s(\\s|\\d)\\d \\d{2}:\\d{2}:\\d{2} -> datetime.strptime(text, "%b %d %H:%M:%S")
13: \\d{2}\\/\\w+\\/\\d{4} \\d{2}:\\d{2}:\\d{2} -> datetime.strptime(text, "%d/%b/%Y %H:%M:%S")
14: \\d{2}\\/\\w+\\/\\d{4}:\\d{2}:\\d{2}:\\d{2} [+-]\\d{4} -> datetime.strptime(text, "%d/%b/%Y:%H:%M:%S %z")
15: \\d{10}\\.\\d+ -> datetime.fromtimestamp(float(text))
16: \\d{13} -> datetime.fromtimestamp(int(text))

Visit the formats in the given order (each element is a table index; an
element that is not a table index is skipped). For a format, find the
first match of its regular expression anywhere in the line (re.search) and
give the whole matched text to its parser, as CPython 3.14 does (the
fromtimestamp parsers use the host local time zone; strptime month names
follow the current LC_TIME locale and never emit a warning to the user). A
format with no match, or whose parser raises or returns nothing, is
skipped. For the first format that yields a datetime, return it as a
LogTimestamp (utc_offset_seconds is the whole seconds of its utcoffset()
when it is aware) together with the order changed so that this format's
element moves to the front (the order is unchanged when it is already
first). When no format yields a datetime, timestamp is Nothing and the
order is returned unchanged."""
    line = _cott_normalize_f32_abi(line, str, path="$.line")
    order = _cott_normalize_f32_abi(order, CottList[U8], path="$.order")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/timestamps/scan_timestamp.py", "c88e1f62badbcf815b5d3ed4d5ae27b27bc64b2badcad99922731c79c2469446", "scan_timestamp", expected_project_name="toolong", expected_cott_symbol="real.toolong.timestamps.scan_timestamp")
        _result = _implementation(line, order)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.timestamps.scan_timestamp"
        if _error.span is None:
            _error.span = {"end_byte":3171,"end_column":1,"end_line":60,"start_byte":388,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.timestamps.scan_timestamp", phase="implementation-call", span={"end_byte":3171,"end_column":1,"end_line":60,"start_byte":388,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.timestamps.scan_timestamp", phase="implementation-call", span={"end_byte":3171,"end_column":1,"end_line":60,"start_byte":388,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TimestampScan, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).order) == len(order))), "real.toolong.timestamps.scan_timestamp", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.timestamps.scan_timestamp", clause="ensures:1", phase="ensures", span={"end_byte":3076,"end_column":42,"end_line":55,"start_byte":3039,"start_column":5,"start_line":55}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = (_result).timestamp
            if type(_cott_match_value) is Nothing:
                return (_cott_contract_condition((((_result).order == order)), "real.toolong.timestamps.scan_timestamp", "ensures:2"))
            _cott_contract_condition((False), "real.toolong.timestamps.scan_timestamp", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.timestamps.scan_timestamp", clause="ensures:2", phase="ensures", span={"end_byte":3153,"end_column":77,"end_line":56,"start_byte":3081,"start_column":5,"start_line":56}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TimestampScan, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def shift_timestamp(timestamp: LogTimestamp, amount: I32, unit: TimeUnit) -> Option[LogTimestamp]:
    """Add amount minutes, hours or days (a day is 24 hours) to the timestamp as
CPython datetime + timedelta does, keeping utc_offset_seconds. amount may be
negative. Nothing when the result falls outside years 1-9999."""
    timestamp = _cott_normalize_f32_abi(timestamp, LogTimestamp, path="$.timestamp")
    amount = _cott_normalize_f32_abi(amount, I32, path="$.amount")
    unit = _cott_normalize_f32_abi(unit, TimeUnit, path="$.unit")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/timestamps/shift_timestamp.py", "da4ceb5cbe31a673ff128ff2f73ad5c44cd3615e1c2ac182dca95c61324de064", "shift_timestamp", expected_project_name="toolong", expected_cott_symbol="real.toolong.timestamps.shift_timestamp")
        _result = _implementation(timestamp, amount, unit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.timestamps.shift_timestamp"
        if _error.span is None:
            _error.span = {"end_byte":3606,"end_column":1,"end_line":71,"start_byte":3171,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.timestamps.shift_timestamp", phase="implementation-call", span={"end_byte":3606,"end_column":1,"end_line":71,"start_byte":3171,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.timestamps.shift_timestamp", phase="implementation-call", span={"end_byte":3606,"end_column":1,"end_line":71,"start_byte":3171,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[LogTimestamp], path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Some and True:
                shifted = _cott_match_value.value
                return (_cott_contract_condition((((not (amount == 0)) or (shifted == timestamp))), "real.toolong.timestamps.shift_timestamp", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.timestamps.shift_timestamp", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.timestamps.shift_timestamp", clause="ensures:1", phase="ensures", span={"end_byte":3588,"end_column":74,"end_line":67,"start_byte":3519,"start_column":5,"start_line":67}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[LogTimestamp], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def compare_timestamps(left: LogTimestamp, right: LogTimestamp) -> Option[I8]:
    """Compare two timestamps like CPython datetimes. When both are naive, compare
their fields (year, month, day, hour, minute, second, microsecond)
lexicographically. When both are aware, compare the UTC instants they
denote. Return Some(-1), Some(0) or Some(1) when left is earlier than,
equal to or later than right. Mixing a naive and an aware timestamp is not
comparable and returns Nothing."""
    left = _cott_normalize_f32_abi(left, LogTimestamp, path="$.left")
    right = _cott_normalize_f32_abi(right, LogTimestamp, path="$.right")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/timestamps/compare_timestamps.py", "38ddfa4caa7ad669cada2b651cb45856424e01884b29c03bc6334b629d8946f9", "compare_timestamps", expected_project_name="toolong", expected_cott_symbol="real.toolong.timestamps.compare_timestamps")
        _result = _implementation(left, right)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.timestamps.compare_timestamps"
        if _error.span is None:
            _error.span = {"end_byte":4207,"end_column":1,"end_line":85,"start_byte":3606,"start_column":1,"start_line":71}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.timestamps.compare_timestamps", phase="implementation-call", span={"end_byte":4207,"end_column":1,"end_line":85,"start_byte":3606,"start_column":1,"start_line":71}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.timestamps.compare_timestamps", phase="implementation-call", span={"end_byte":4207,"end_column":1,"end_line":85,"start_byte":3606,"start_column":1,"start_line":71}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[I8], path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Some and True:
                ordering = _cott_match_value.value
                return (_cott_contract_condition((((not (left == right)) or (ordering == 0))), "real.toolong.timestamps.compare_timestamps", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.timestamps.compare_timestamps", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.timestamps.compare_timestamps", clause="ensures:1", phase="ensures", span={"end_byte":4189,"end_column":70,"end_line":81,"start_byte":4124,"start_column":5,"start_line":81}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[I8], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def timestamp_seconds(timestamp: LogTimestamp) -> F64:
    """POSIX seconds of the timestamp, as CPython datetime.timestamp() returns
them: an aware timestamp denotes an exact instant; a naive timestamp is
interpreted in the host local time zone."""
    timestamp = _cott_normalize_f32_abi(timestamp, LogTimestamp, path="$.timestamp")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/timestamps/timestamp_seconds.py", "187590143a562b37c856f4fea9f886cff4b67ec42911a43c16af57a71acafdff", "timestamp_seconds", expected_project_name="toolong", expected_cott_symbol="real.toolong.timestamps.timestamp_seconds")
        _result = _implementation(timestamp)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.timestamps.timestamp_seconds"
        if _error.span is None:
            _error.span = {"end_byte":4495,"end_column":1,"end_line":94,"start_byte":4207,"start_column":1,"start_line":85}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.timestamps.timestamp_seconds", phase="implementation-call", span={"end_byte":4495,"end_column":1,"end_line":94,"start_byte":4207,"start_column":1,"start_line":85}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.timestamps.timestamp_seconds", phase="implementation-call", span={"end_byte":4495,"end_column":1,"end_line":94,"start_byte":4207,"start_column":1,"start_line":85}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, F64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, F64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def format_local_timestamp(timestamp: LogTimestamp) -> str:
    """The footer rendering of a timestamp: CPython strftime("%x %X") of the
datetime (with its UTC offset when aware), using the process's current
LC_TIME locale. In the C/POSIX locale this is "MM/DD/YY HH:MM:SS"."""
    timestamp = _cott_normalize_f32_abi(timestamp, LogTimestamp, path="$.timestamp")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/timestamps/format_local_timestamp.py", "8da4235fdd29d66147fe7af52b6a964b7c674ae1cb5d0f0ac9b700ac1ae72eee", "format_local_timestamp", expected_project_name="toolong", expected_cott_symbol="real.toolong.timestamps.format_local_timestamp")
        _result = _implementation(timestamp)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.timestamps.format_local_timestamp"
        if _error.span is None:
            _error.span = {"end_byte":4839,"end_column":1,"end_line":105,"start_byte":4495,"start_column":1,"start_line":94}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.timestamps.format_local_timestamp", phase="implementation-call", span={"end_byte":4839,"end_column":1,"end_line":105,"start_byte":4495,"start_column":1,"start_line":94}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.timestamps.format_local_timestamp", phase="implementation-call", span={"end_byte":4839,"end_column":1,"end_line":105,"start_byte":4495,"start_column":1,"start_line":94}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) > 0)), "real.toolong.timestamps.format_local_timestamp", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.timestamps.format_local_timestamp", clause="ensures:1", phase="ensures", span={"end_byte":4821,"end_column":27,"end_line":101,"start_byte":4799,"start_column":5,"start_line":101}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["compare_timestamps", "default_timestamp_order", "format_local_timestamp", "scan_timestamp", "shift_timestamp", "timestamp_seconds"]
