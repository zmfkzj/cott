from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

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
    if _expected_error is None and ((not (((day_type == "U") or (day_type == "A")) or (day_type == "W")))):
        _expected_error = RideRowError_InvalidDayType
        _expected_error_span = {"end_byte":1216,"end_column":103,"end_line":33,"start_byte":1118,"start_column":5,"start_line":33}
        _expected_error_clause = "error:1"
    if _expected_error is None and ((rides < 0)):
        _expected_error = RideRowError_InvalidRidership
        _expected_error_span = {"end_byte":1271,"end_column":55,"end_line":34,"start_byte":1221,"start_column":5,"start_line":34}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/cta_row/decode_row.py", "9119c4df86ae9805ce5fbecff043c594ebb803ac0da7b472d5549e9b8ce7d002", "decode_row", expected_project_name="cta-row", expected_cott_symbol="curriculum.cta_row.decode_row")
        _result = _implementation(route, date, day_type, rides)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.cta_row.decode_row"
        if _error.span is None:
            _error.span = {"end_byte":1343,"end_column":1,"end_line":37,"start_byte":355,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.cta_row.decode_row", phase="implementation-call", span={"end_byte":1343,"end_column":1,"end_line":37,"start_byte":355,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.cta_row.decode_row", phase="implementation-call", span={"end_byte":1343,"end_column":1,"end_line":37,"start_byte":355,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RideRow, RideRowError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.cta_row.decode_row", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RideRowError_InvalidRoute, RideRowError_InvalidDate,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.cta_row.decode_row", phase="error", span={"end_byte":1343,"end_column":1,"end_line":37,"start_byte":355,"start_column":1,"start_line":26}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.cta_row.decode_row", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

__all__ = ["DayType", "DayType_Saturday", "DayType_SundayHoliday", "DayType_Weekday", "RideCount", "RideRow", "RideRowError", "RideRowError_InvalidDate", "RideRowError_InvalidDayType", "RideRowError_InvalidRidership", "RideRowError_InvalidRoute", "RouteCode", "ServiceDate", "decode_row"]
