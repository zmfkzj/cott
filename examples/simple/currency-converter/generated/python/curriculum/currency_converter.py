from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.currency_converter_types import ConversionRequest, CurrencyError, CurrencyError_DuplicateRate, CurrencyError_InvalidCurrencyCode, CurrencyError_MissingRate, CurrencyError_NegativeQuantity, CurrencyError_NonFiniteQuantity, CurrencyError_NonFiniteRate, CurrencyError_NonFiniteResult, CurrencyError_NonPositiveRate, Rate

def validate_conversion_request(request: ConversionRequest) -> Result[Unit, CurrencyError]:
    """Validates a currency conversion request and its complete EUR rate list,
returning Ok(Unit) when every rule is satisfied.

The source code, destination code, and every rate code must contain exactly
three ASCII uppercase letters A through Z. Codes are case-sensitive and
are not trimmed. The quantity must be finite and non-negative; negative
zero is accepted. Every per-EUR rate must be finite and strictly positive.

A non-finite quantity is reported before a negative quantity. The source
code is checked before the destination code. Rates are then checked in list
order; within each rate, its code is checked before a non-finite value, a
non-positive value, and a duplicate code, in that order. The entire list is
checked before missing rates, so DuplicateRate takes priority over
MissingRate. A missing source rate is checked before a missing destination
rate. Empty, singleton, and longer lists follow these same rules."""
    request = _cott_validate_abi(request, ConversionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/currency_converter/validate_conversion_request.py", "5622ab6f350238d42bc0860c9dd032b8f58e0ae9ad3001c80b03e53e57c524e9", "validate_conversion_request", expected_project_name="currency-converter", expected_cott_symbol="curriculum.currency_converter.validate_conversion_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.currency_converter.validate_conversion_request"
        if _error.span is None:
            _error.span = {"end_byte":1771,"end_column":1,"end_line":52,"start_byte":378,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.currency_converter.validate_conversion_request", phase="implementation-call", span={"end_byte":1771,"end_column":1,"end_line":52,"start_byte":378,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.currency_converter.validate_conversion_request", phase="implementation-call", span={"end_byte":1771,"end_column":1,"end_line":52,"start_byte":378,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, CurrencyError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.currency_converter.validate_conversion_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CurrencyError_NonFiniteQuantity, CurrencyError_NegativeQuantity, CurrencyError_InvalidCurrencyCode, CurrencyError_NonFiniteRate, CurrencyError_NonPositiveRate, CurrencyError_DuplicateRate, CurrencyError_MissingRate,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.currency_converter.validate_conversion_request", phase="error", span={"end_byte":1771,"end_column":1,"end_line":52,"start_byte":378,"start_column":1,"start_line":23}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.currency_converter.validate_conversion_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    _result = _cott_wrap_async_protocol(_result, Result[Unit, CurrencyError], path="$.return", validator=_cott_validate_abi)
    return _result

def convert_currency(request: ConversionRequest) -> Result[F64, CurrencyError]:
    """Validates the request, propagating its validation error unchanged, then
converts the quantity using rates expressed as units of currency per EUR.

When the source and destination codes differ, the quantity is divided by
the source rate and that result is multiplied by the destination rate,
using F64 arithmetic in that order. A non-finite intermediate or product
returns NonFiniteResult. When the codes are equal, the fully validated list
must still contain that code exactly once, but rate arithmetic is skipped
and the quantity is used unchanged.

The successful quantity is rounded to the nearest multiple of 0.01. An
exact halfway case is rounded to the multiple whose hundredths integer is
even. Ok contains the resulting finite, non-negative F64 value."""
    request = _cott_validate_abi(request, ConversionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/currency_converter/convert_currency.py", "ef54bab5f20f17ffbe4a7473eb4e360f0704d96aad366752b15865f1ac128e90", "convert_currency", expected_project_name="currency-converter", expected_cott_symbol="curriculum.currency_converter.convert_currency")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.currency_converter.convert_currency"
        if _error.span is None:
            _error.span = {"end_byte":3064,"end_column":1,"end_line":81,"start_byte":1771,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.currency_converter.convert_currency", phase="implementation-call", span={"end_byte":3064,"end_column":1,"end_line":81,"start_byte":1771,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.currency_converter.convert_currency", phase="implementation-call", span={"end_byte":3064,"end_column":1,"end_line":81,"start_byte":1771,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, CurrencyError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.currency_converter.convert_currency", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CurrencyError_NonFiniteQuantity, CurrencyError_NegativeQuantity, CurrencyError_InvalidCurrencyCode, CurrencyError_NonFiniteRate, CurrencyError_NonPositiveRate, CurrencyError_DuplicateRate, CurrencyError_MissingRate, CurrencyError_NonFiniteResult,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.currency_converter.convert_currency", phase="error", span={"end_byte":3064,"end_column":1,"end_line":81,"start_byte":1771,"start_column":1,"start_line":52}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.currency_converter.convert_currency", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return ((value >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.currency_converter.convert_currency", clause="ensures:1", phase="ensures", span={"end_byte":2727,"end_column":45,"end_line":69,"start_byte":2687,"start_column":5,"start_line":69}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[F64, CurrencyError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ConversionRequest", "CurrencyError", "CurrencyError_DuplicateRate", "CurrencyError_InvalidCurrencyCode", "CurrencyError_MissingRate", "CurrencyError_NegativeQuantity", "CurrencyError_NonFiniteQuantity", "CurrencyError_NonFiniteRate", "CurrencyError_NonFiniteResult", "CurrencyError_NonPositiveRate", "Rate", "convert_currency", "validate_conversion_request"]
