from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.cta_row_types import DayType, DayType_Saturday, DayType_SundayHoliday, DayType_Weekday, RideCount, RideRow, RideRowError, RideRowError_InvalidDate, RideRowError_InvalidDayType, RideRowError_InvalidRidership, RideRowError_InvalidRoute, RouteCode, ServiceDate

def decode_row(route: str, date: str, day_type: str, rides: I64) -> Result[RideRow, RideRowError]:
    """Purely decode and validate one transit ridership row. Validation is performed in day_type, rides, route, date order and returns the corresponding first error. day_type maps U to SundayHoliday, A to Saturday, and W to Weekday. A valid route contains one to four ASCII uppercase letters or digits and at least one digit. A valid date is a Gregorian date in canonical MM/DD/YYYY form with a year from 0001 through 9999. rides must be from 0 through 9223372036854775807.

Success returns a RideRow containing nominal RouteCode, ServiceDate, and RideCount values and the mapped DayType variant. The function has no external effects."""
    route = _cott_validate_abi(route, str, path="$.route")
    date = _cott_validate_abi(date, str, path="$.date")
    day_type = _cott_validate_abi(day_type, str, path="$.day_type")
    rides = _cott_validate_abi(rides, I64, path="$.rides")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((not (((day_type == "U") or (day_type == "A")) or (day_type == "W")))), "curriculum.cta_row.decode_row", "error:5:condition")):
        _expected_error = RideRowError_InvalidDayType
        _expected_error_span = {"end_byte":1557,"end_column":103,"end_line":38,"start_byte":1459,"start_column":5,"start_line":38}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition(((rides < 0)), "curriculum.cta_row.decode_row", "error:6:condition")):
        _expected_error = RideRowError_InvalidRidership
        _expected_error_span = {"end_byte":1612,"end_column":55,"end_line":39,"start_byte":1562,"start_column":5,"start_line":39}
        _expected_error_clause = "error:6"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/cta_row/decode_row.py", "a2711bfc647a4bb769822e7b65c9de364db7e13bda12f167a6b9c9daa4a7483d", "decode_row", expected_project_name="cta-row", expected_cott_symbol="curriculum.cta_row.decode_row")
        _result = _implementation(route, date, day_type, rides)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.cta_row.decode_row"
        if _error.span is None:
            _error.span = {"end_byte":1685,"end_column":1,"end_line":43,"start_byte":355,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.cta_row.decode_row", phase="implementation-call", span={"end_byte":1685,"end_column":1,"end_line":43,"start_byte":355,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.cta_row.decode_row", phase="implementation-call", span={"end_byte":1685,"end_column":1,"end_line":43,"start_byte":355,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RideRow, RideRowError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.cta_row.decode_row", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RideRowError_InvalidRoute, RideRowError_InvalidDate,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.cta_row.decode_row", phase="error", span={"end_byte":1685,"end_column":1,"end_line":43,"start_byte":355,"start_column":1,"start_line":26}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.cta_row.decode_row", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.cta_row.decode_row", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is RideRowError_InvalidRoute:
        _cott_contract_condition(True, "curriculum.cta_row.decode_row", "error:7")
    if type(_result) is Err and type(_result.error) is RideRowError_InvalidDate:
        _cott_contract_condition(True, "curriculum.cta_row.decode_row", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            row = _cott_match_value.value
            return (_cott_contract_condition((((((row).route).value == route) and (((row).date).value == date))), "curriculum.cta_row.decode_row", "ensures:1"))
        _cott_contract_condition((False), "curriculum.cta_row.decode_row", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.cta_row.decode_row", clause="ensures:1", phase="ensures", span={"end_byte":1197,"end_column":84,"end_line":33,"start_byte":1118,"start_column":5,"start_line":33}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            row = _cott_match_value.value
            return (_cott_contract_condition((((not (day_type == "U")) or ((row).day_type == DayType_SundayHoliday()))), "curriculum.cta_row.decode_row", "ensures:2"))
        _cott_contract_condition((False), "curriculum.cta_row.decode_row", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.cta_row.decode_row", clause="ensures:2", phase="ensures", span={"end_byte":1286,"end_column":89,"end_line":34,"start_byte":1202,"start_column":5,"start_line":34}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            row = _cott_match_value.value
            return (_cott_contract_condition((((not (day_type == "A")) or ((row).day_type == DayType_Saturday()))), "curriculum.cta_row.decode_row", "ensures:3"))
        _cott_contract_condition((False), "curriculum.cta_row.decode_row", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.cta_row.decode_row", clause="ensures:3", phase="ensures", span={"end_byte":1370,"end_column":84,"end_line":35,"start_byte":1291,"start_column":5,"start_line":35}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            row = _cott_match_value.value
            return (_cott_contract_condition((((not (day_type == "W")) or ((row).day_type == DayType_Weekday()))), "curriculum.cta_row.decode_row", "ensures:4"))
        _cott_contract_condition((False), "curriculum.cta_row.decode_row", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.cta_row.decode_row", clause="ensures:4", phase="ensures", span={"end_byte":1453,"end_column":83,"end_line":36,"start_byte":1375,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[RideRow, RideRowError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["DayType", "DayType_Saturday", "DayType_SundayHoliday", "DayType_Weekday", "RideCount", "RideRow", "RideRowError", "RideRowError_InvalidDate", "RideRowError_InvalidDayType", "RideRowError_InvalidRidership", "RideRowError_InvalidRoute", "RouteCode", "ServiceDate", "decode_row"]
