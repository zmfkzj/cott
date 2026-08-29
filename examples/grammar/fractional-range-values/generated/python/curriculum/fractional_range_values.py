from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.fractional_range_values_types import FractionalRangeError, FractionalRangeError_NonFiniteInput, FractionalRangeError_OutputLimitExceeded, FractionalRangeError_StepDoesNotAdvance, OutputLimit, PositiveStep

def build_bounded_range(start: F64, stop: F64, step: PositiveStep, limit: OutputLimit) -> Result[CottList[F64], FractionalRangeError]:
    """Constructs an ascending finite sequence of binary64 values. The start is
included when start is less than stop; stop is always excluded. If start is
greater than or equal to stop, the result is an empty list.

The function first rejects a non-finite start, stop, or step with
NonFiniteInput. Each candidate is computed directly as start plus index
times step, with binary64 round-to-nearest, ties-to-even after the
multiplication and addition. A candidate equal to or above stop ends the
sequence. A candidate that does not exceed the preceding rounded value
produces StepDoesNotAdvance. After limit values, the next candidate is
checked only for termination; if it is still below stop,
OutputLimitExceeded takes precedence."""
    start = _cott_validate_abi(start, F64, path="$.start")
    stop = _cott_validate_abi(stop, F64, path="$.stop")
    step = _cott_validate_abi(step, PositiveStep, path="$.step")
    limit = _cott_validate_abi(limit, OutputLimit, path="$.limit")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/fractional_range_values/build_bounded_range.py", "ea06e3bc1ed7abf7c04fff66e55b60af95dc256258b7927e3b296df07f634662", "build_bounded_range", expected_project_name="fractional-range-values", expected_cott_symbol="curriculum.fractional_range_values.build_bounded_range")
        _result = _implementation(start, stop, step, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.fractional_range_values.build_bounded_range"
        if _error.span is None:
            _error.span = {"end_byte":1384,"end_column":1,"end_line":40,"start_byte":240,"start_column":1,"start_line":14}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.fractional_range_values.build_bounded_range", phase="implementation-call", span={"end_byte":1384,"end_column":1,"end_line":40,"start_byte":240,"start_column":1,"start_line":14}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.fractional_range_values.build_bounded_range", phase="implementation-call", span={"end_byte":1384,"end_column":1,"end_line":40,"start_byte":240,"start_column":1,"start_line":14}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[F64], FractionalRangeError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.fractional_range_values.build_bounded_range", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FractionalRangeError_NonFiniteInput, FractionalRangeError_StepDoesNotAdvance, FractionalRangeError_OutputLimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.fractional_range_values.build_bounded_range", phase="error", span={"end_byte":1384,"end_column":1,"end_line":40,"start_byte":240,"start_column":1,"start_line":14}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.fractional_range_values.build_bounded_range", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            values = _cott_match_value.value
            return ((len(values) <= 10000))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.fractional_range_values.build_bounded_range", clause="ensures:1", phase="ensures", span={"end_byte":1235,"end_column":53,"end_line":35,"start_byte":1187,"start_column":5,"start_line":35}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[F64], FractionalRangeError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["FractionalRangeError", "FractionalRangeError_NonFiniteInput", "FractionalRangeError_OutputLimitExceeded", "FractionalRangeError_StepDoesNotAdvance", "OutputLimit", "PositiveStep", "build_bounded_range"]
