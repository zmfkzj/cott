from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.calculate_age_types import AgeError, AgeError_InvalidDate, AgeError_NegativeAge, AgeError_Overflow, AgeSummary

def calculate_age_days(age_years: I64, today_year: I64, today_month: I64, today_day: I64) -> Result[I64, AgeError]:
    """Calculate the elapsed Gregorian days for an age in whole years ending on the supplied date.

A February 29 anniversary falls on February 28 in a non-leap start year. Validation returns NegativeAge before InvalidDate, and InvalidDate before Overflow."""
    age_years = _cott_validate_abi(age_years, I64, path="$.age_years")
    today_year = _cott_validate_abi(today_year, I64, path="$.today_year")
    today_month = _cott_validate_abi(today_month, I64, path="$.today_month")
    today_day = _cott_validate_abi(today_day, I64, path="$.today_day")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((age_years < 0)):
        _expected_error = AgeError_NegativeAge
        _expected_error_span = {"end_byte":681,"end_column":50,"end_line":28,"start_byte":636,"start_column":5,"start_line":28}
        _expected_error_clause = "error:2"
    if _expected_error is None and ((age_years > (today_year - 1))):
        _expected_error = AgeError_Overflow
        _expected_error_span = {"end_byte":772,"end_column":60,"end_line":30,"start_byte":717,"start_column":5,"start_line":30}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/calculate_age/calculate_age_days.py", "4f84cf31f170a41e4a13ee66e5c9a17a1931b741c864aac6d39677c34a2cd9f3", "calculate_age_days", expected_project_name="calculate-age", expected_cott_symbol="curriculum.calculate_age.calculate_age_days")
        _result = _implementation(age_years, today_year, today_month, today_day)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.calculate_age.calculate_age_days"
        if _error.span is None:
            _error.span = {"end_byte":774,"end_column":1,"end_line":32,"start_byte":173,"start_column":1,"start_line":14}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.calculate_age.calculate_age_days", phase="implementation-call", span={"end_byte":774,"end_column":1,"end_line":32,"start_byte":173,"start_column":1,"start_line":14}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.calculate_age.calculate_age_days", phase="implementation-call", span={"end_byte":774,"end_column":1,"end_line":32,"start_byte":173,"start_column":1,"start_line":14}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[I64, AgeError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.calculate_age.calculate_age_days", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (AgeError_InvalidDate,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.calculate_age.calculate_age_days", phase="error", span={"end_byte":774,"end_column":1,"end_line":32,"start_byte":173,"start_column":1,"start_line":14}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.calculate_age.calculate_age_days", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        days = _result.value
        if not ((days >= 0)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.calculate_age.calculate_age_days", clause="ensures:1", phase="ensures", span={"end_byte":630,"end_column":41,"end_line":26,"start_byte":594,"start_column":5,"start_line":26}, expected="true", actual="false")
    return _result

def summarize_age(name: str, age_years: I64, today_year: I64, today_month: I64, today_day: I64) -> Result[AgeSummary, AgeError]:
    """Build an age summary from the Gregorian day count calculated by calculate_age_days.

On success, name is unchanged, years is age_years, months is age_years * 12, and days is the helper result. Helper errors are propagated unchanged."""
    name = _cott_validate_abi(name, str, path="$.name")
    age_years = _cott_validate_abi(age_years, I64, path="$.age_years")
    today_year = _cott_validate_abi(today_year, I64, path="$.today_year")
    today_month = _cott_validate_abi(today_month, I64, path="$.today_month")
    today_day = _cott_validate_abi(today_day, I64, path="$.today_day")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((age_years < 0)):
        _expected_error = AgeError_NegativeAge
        _expected_error_span = {"end_byte":1476,"end_column":50,"end_line":50,"start_byte":1431,"start_column":5,"start_line":50}
        _expected_error_clause = "error:5"
    if _expected_error is None and ((age_years > (today_year - 1))):
        _expected_error = AgeError_Overflow
        _expected_error_span = {"end_byte":1567,"end_column":60,"end_line":52,"start_byte":1512,"start_column":5,"start_line":52}
        _expected_error_clause = "error:7"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/calculate_age/summarize_age.py", "61f500e5a09960c46e9eea4694160d3e6c59780d6ffc9c0c0869fc1d52d5f3d7", "summarize_age", expected_project_name="calculate-age", expected_cott_symbol="curriculum.calculate_age.summarize_age")
        _result = _implementation(name, age_years, today_year, today_month, today_day)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.calculate_age.summarize_age"
        if _error.span is None:
            _error.span = {"end_byte":1568,"end_column":1,"end_line":53,"start_byte":774,"start_column":1,"start_line":32}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.calculate_age.summarize_age", phase="implementation-call", span={"end_byte":1568,"end_column":1,"end_line":53,"start_byte":774,"start_column":1,"start_line":32}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.calculate_age.summarize_age", phase="implementation-call", span={"end_byte":1568,"end_column":1,"end_line":53,"start_byte":774,"start_column":1,"start_line":32}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[AgeSummary, AgeError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.calculate_age.summarize_age", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (AgeError_InvalidDate,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.calculate_age.summarize_age", phase="error", span={"end_byte":1568,"end_column":1,"end_line":53,"start_byte":774,"start_column":1,"start_line":32}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.calculate_age.summarize_age", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        summary = _result.value
        if not (((summary).name == name)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.calculate_age.summarize_age", clause="ensures:1", phase="ensures", span={"end_byte":1245,"end_column":55,"end_line":45,"start_byte":1195,"start_column":5,"start_line":45}, expected="true", actual="false")
    if type(_result) is Ok and True:
        summary = _result.value
        if not (((summary).years == age_years)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.calculate_age.summarize_age", clause="ensures:2", phase="ensures", span={"end_byte":1306,"end_column":61,"end_line":46,"start_byte":1250,"start_column":5,"start_line":46}, expected="true", actual="false")
    if type(_result) is Ok and True:
        summary = _result.value
        if not (((summary).months == (age_years * 12))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.calculate_age.summarize_age", clause="ensures:3", phase="ensures", span={"end_byte":1373,"end_column":67,"end_line":47,"start_byte":1311,"start_column":5,"start_line":47}, expected="true", actual="false")
    if type(_result) is Ok and True:
        summary = _result.value
        if not (((summary).days >= 0)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.calculate_age.summarize_age", clause="ensures:4", phase="ensures", span={"end_byte":1425,"end_column":52,"end_line":48,"start_byte":1378,"start_column":5,"start_line":48}, expected="true", actual="false")
    return _result

__all__ = ["AgeError", "AgeError_InvalidDate", "AgeError_NegativeAge", "AgeError_Overflow", "AgeSummary", "calculate_age_days", "summarize_age"]
