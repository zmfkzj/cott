from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.stock_input_validation_types import Price, Shares, StockInput, StockInputError, StockInputError_EmptyName, StockInputError_NegativePrice, StockInputError_NegativeShares, StockInputError_NonFinitePrice, StockName

def validate_stock_input(name: str, shares: I64, price: F64) -> Result[StockInput, StockInputError]:
    """Validates raw stock fields and constructs StockName, Shares, Price, and
StockInput values, returning the first applicable error. Validation is
ordered as EmptyName for a zero-length name, NegativeShares for shares
below zero, NonFinitePrice for NaN or either infinity, then NegativePrice
for a finite price below zero. Whitespace-only names, zero shares, zero
price, and negative zero are accepted. Successful values preserve the raw
name, shares, and price exactly. This pure function performs no I/O and
terminates for every Str, I64, and F64 input."""
    name = _cott_validate_abi(name, str, path="$.name")
    shares = _cott_validate_abi(shares, I64, path="$.shares")
    price = _cott_validate_abi(price, F64, path="$.price")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(name) == 0)):
        _expected_error = StockInputError_EmptyName
        _expected_error_span = {"end_byte":1100,"end_column":55,"end_line":35,"start_byte":1050,"start_column":5,"start_line":35}
        _expected_error_clause = "error:1"
    if _expected_error is None and ((shares < 0)):
        _expected_error = StockInputError_NegativeShares
        _expected_error_span = {"end_byte":1157,"end_column":57,"end_line":36,"start_byte":1105,"start_column":5,"start_line":36}
        _expected_error_clause = "error:2"
    if _expected_error is None and ((price < 0)):
        _expected_error = StockInputError_NegativePrice
        _expected_error_span = {"end_byte":1255,"end_column":57,"end_line":38,"start_byte":1203,"start_column":5,"start_line":38}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/stock_input_validation/validate_stock_input.py", "b2dd473516cb62b3788a6d09120753c9c5440524ff31f22fb997bcfd7191d5dc", "validate_stock_input", expected_project_name="stock-input-validation", expected_cott_symbol="curriculum.stock_input_validation.validate_stock_input")
        _result = _implementation(name, shares, price)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.stock_input_validation.validate_stock_input"
        if _error.span is None:
            _error.span = {"end_byte":1256,"end_column":1,"end_line":39,"start_byte":341,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.stock_input_validation.validate_stock_input", phase="implementation-call", span={"end_byte":1256,"end_column":1,"end_line":39,"start_byte":341,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.stock_input_validation.validate_stock_input", phase="implementation-call", span={"end_byte":1256,"end_column":1,"end_line":39,"start_byte":341,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[StockInput, StockInputError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.stock_input_validation.validate_stock_input", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StockInputError_NonFinitePrice,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.stock_input_validation.validate_stock_input", phase="error", span={"end_byte":1256,"end_column":1,"end_line":39,"start_byte":341,"start_column":1,"start_line":23}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.stock_input_validation.validate_stock_input", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

__all__ = ["Price", "Shares", "StockInput", "StockInputError", "StockInputError_EmptyName", "StockInputError_NegativePrice", "StockInputError_NegativeShares", "StockInputError_NonFinitePrice", "StockName", "validate_stock_input"]
