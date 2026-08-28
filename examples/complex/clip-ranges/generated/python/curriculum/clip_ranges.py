from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.clip_ranges_types import ClipPlan, ClipRangeError, ClipRangeError_EmptyRanges, ClipRangeError_PastDuration, ClipRangeError_StartNotBeforeEnd, ClipRangeError_TotalOverflow, ClipRequest, TimeRange

def range_duration_ms(range: TimeRange) -> U64:
    """Return the duration of one validated half-open time range in milliseconds.
The caller must establish that the range starts before it ends."""
    range = _cott_validate_abi(range, TimeRange, path="$.range")
    if not (((range).start_ms < (range).end_ms)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.clip_ranges.range_duration_ms", clause="requires:1", phase="requires", span={"end_byte":570,"end_column":43,"end_line":27,"start_byte":532,"start_column":5,"start_line":27}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/clip_ranges/range_duration_ms.py", "79fa8a7f5c0a0a0275b9b274d89b1c654943aaa46e070d5a77850da37dc304f1", "range_duration_ms", expected_project_name="clip-ranges", expected_cott_symbol="curriculum.clip_ranges.range_duration_ms")
        _result = _implementation(range)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.clip_ranges.range_duration_ms"
        if _error.span is None:
            _error.span = {"end_byte":572,"end_column":1,"end_line":29,"start_byte":313,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.clip_ranges.range_duration_ms", phase="implementation-call", span={"end_byte":572,"end_column":1,"end_line":29,"start_byte":313,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.clip_ranges.range_duration_ms", phase="implementation-call", span={"end_byte":572,"end_column":1,"end_line":29,"start_byte":313,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=_cott_validate_abi)
    return _result

def plan_clip_ranges(request: ClipRequest) -> Result[ClipPlan, ClipRangeError]:
    """Validate requested intervals in input order and build a clip plan.
Empty input is rejected first. Each range must start before it ends and
must not extend past the source duration. Valid ranges remain unchanged
and their durations are accumulated with checked U64 arithmetic."""
    request = _cott_validate_abi(request, ClipRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((request).ranges) == 0)):
        _expected_error = ClipRangeError_EmptyRanges
        _expected_error_span = {"end_byte":1150,"end_column":66,"end_line":40,"start_byte":1089,"start_column":5,"start_line":40}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/clip_ranges/plan_clip_ranges.py", "39342f5ad87c9b61bc2a1aa4453dab7b19632334ef7b171fc1cc11d1b2b7c880", "plan_clip_ranges", expected_project_name="clip-ranges", expected_cott_symbol="curriculum.clip_ranges.plan_clip_ranges")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.clip_ranges.plan_clip_ranges"
        if _error.span is None:
            _error.span = {"end_byte":1271,"end_column":1,"end_line":44,"start_byte":572,"start_column":1,"start_line":29}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.clip_ranges.plan_clip_ranges", phase="implementation-call", span={"end_byte":1271,"end_column":1,"end_line":44,"start_byte":572,"start_column":1,"start_line":29}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.clip_ranges.plan_clip_ranges", phase="implementation-call", span={"end_byte":1271,"end_column":1,"end_line":44,"start_byte":572,"start_column":1,"start_line":29}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ClipPlan, ClipRangeError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.clip_ranges.plan_clip_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClipRangeError_StartNotBeforeEnd, ClipRangeError_PastDuration, ClipRangeError_TotalOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.clip_ranges.plan_clip_ranges", phase="error", span={"end_byte":1271,"end_column":1,"end_line":44,"start_byte":572,"start_column":1,"start_line":29}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.clip_ranges.plan_clip_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return ((len((plan).ranges) == len((request).ranges)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.clip_ranges.plan_clip_ranges", clause="ensures:1", phase="ensures", span={"end_byte":1032,"end_column":69,"end_line":37,"start_byte":968,"start_column":5,"start_line":37}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return ((len((plan).ranges) > 0))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.clip_ranges.plan_clip_ranges", clause="ensures:2", phase="ensures", span={"end_byte":1083,"end_column":51,"end_line":38,"start_byte":1037,"start_column":5,"start_line":38}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ClipPlan, ClipRangeError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ClipPlan", "ClipRangeError", "ClipRangeError_EmptyRanges", "ClipRangeError_PastDuration", "ClipRangeError_StartNotBeforeEnd", "ClipRangeError_TotalOverflow", "ClipRequest", "TimeRange", "plan_clip_ranges", "range_duration_ms"]
