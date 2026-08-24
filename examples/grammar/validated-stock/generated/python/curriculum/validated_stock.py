from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.validated_stock_types import Price, Shares, Stock, StockName, ValuationError, ValuationError_Overflow

def value_stock(stock: Stock) -> Result[F64, ValuationError]:
    """Computes the market value of one validated stock position. StockName
accepts every non-empty string; Shares accepts integers from zero through
9,223,372,036,854,775,807; Price accepts finite binary64 values from 0.0
through 1.7976931348623157e308 inclusive. Each nominal constructor
validates before value_stock is called; constructor failures are contract
violations, not ValuationError values. For a valid Stock, value_stock
multiplies shares by price exactly once and returns the finite binary64
product in Ok, including zero when either factor is zero. Overflow is
returned when multiplication produces infinity and is the only function
error."""
    stock = _cott_validate_abi(stock, Stock, path="$.stock")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/validated_stock/value_stock.py", "1b5d32d1e4c205bafa1771fd686816aec1a17e384b5c4b4278a069106c545435", "value_stock", expected_project_name="validated-stock", expected_cott_symbol="curriculum.validated_stock.value_stock")
        _result = _implementation(stock)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.validated_stock.value_stock"
        if _error.span is None:
            _error.span = {"end_byte":1192,"end_column":1,"end_line":37,"start_byte":306,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.validated_stock.value_stock", phase="implementation-call", span={"end_byte":1192,"end_column":1,"end_line":37,"start_byte":306,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.validated_stock.value_stock", phase="implementation-call", span={"end_byte":1192,"end_column":1,"end_line":37,"start_byte":306,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, ValuationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.validated_stock.value_stock", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ValuationError_Overflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.validated_stock.value_stock", phase="error", span={"end_byte":1192,"end_column":1,"end_line":37,"start_byte":306,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.validated_stock.value_stock", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        value = _result.value
        if not (((value >= 0) and (value <= 179769313486231570000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.validated_stock.value_stock", clause="ensures:1", phase="ensures", span={"end_byte":1156,"end_column":81,"end_line":34,"start_byte":1080,"start_column":5,"start_line":34}, expected="true", actual="false")
    return _result

__all__ = ["Price", "Shares", "Stock", "StockName", "ValuationError", "ValuationError_Overflow", "value_stock"]
