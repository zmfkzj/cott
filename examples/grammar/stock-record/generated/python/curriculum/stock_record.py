from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.stock_record_types import StockRecord, StockRecordError, StockRecordError_EmptyName, StockRecordError_NegativePrice, StockRecordError_NegativeShares, StockRecordError_NonFinitePrice, StockRecordError_ValuationOverflow

def value_record(record: StockRecord) -> Result[F64, StockRecordError]:
    """Computes the value of a validated stock record.

The caller supplies non-negative shares and a non-negative price.
ValuationOverflow is returned when the binary64 product is not finite."""
    record = _cott_validate_abi(record, StockRecord, path="$.record")
    if not (((record).price >= 0)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.stock_record.value_record", clause="requires:1", phase="requires", span={"end_byte":540,"end_column":33,"end_line":23,"start_byte":512,"start_column":5,"start_line":23}, expected="true", actual="false")
    if not (((record).shares >= 0)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.stock_record.value_record", clause="requires:2", phase="requires", span={"end_byte":572,"end_column":32,"end_line":24,"start_byte":545,"start_column":5,"start_line":24}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/stock_record/value_record.py", "a7303aec861ffaef53fa9e0890c22ee28594674858eb18bc43516ead655c2403", "value_record", expected_project_name="stock-record", expected_cott_symbol="curriculum.stock_record.value_record")
        _result = _implementation(record)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.stock_record.value_record"
        if _error.span is None:
            _error.span = {"end_byte":666,"end_column":1,"end_line":30,"start_byte":214,"start_column":1,"start_line":15}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.stock_record.value_record", phase="implementation-call", span={"end_byte":666,"end_column":1,"end_line":30,"start_byte":214,"start_column":1,"start_line":15}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.stock_record.value_record", phase="implementation-call", span={"end_byte":666,"end_column":1,"end_line":30,"start_byte":214,"start_column":1,"start_line":15}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, StockRecordError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.stock_record.value_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StockRecordError_ValuationOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.stock_record.value_record", phase="error", span={"end_byte":666,"end_column":1,"end_line":30,"start_byte":214,"start_column":1,"start_line":15}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.stock_record.value_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return ((value >= 0))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.stock_record.value_record", clause="ensures:3", phase="ensures", span={"end_byte":618,"end_column":45,"end_line":26,"start_byte":578,"start_column":5,"start_line":26}, expected="true", actual="false")
    return _result

def value_stock_record(record: StockRecord) -> Result[F64, StockRecordError]:
    """Validates and values one raw stock record.

Validation reports EmptyName, NegativeShares, NonFinitePrice, then
NegativePrice in source order. A valid record is valued by value_record."""
    record = _cott_validate_abi(record, StockRecord, path="$.record")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((record).name) == 0)):
        _expected_error = StockRecordError_EmptyName
        _expected_error_span = {"end_byte":1072,"end_column":63,"end_line":40,"start_byte":1014,"start_column":5,"start_line":40}
        _expected_error_clause = "error:2"
    if _expected_error is None and (((record).shares < 0)):
        _expected_error = StockRecordError_NegativeShares
        _expected_error_span = {"end_byte":1137,"end_column":65,"end_line":41,"start_byte":1077,"start_column":5,"start_line":41}
        _expected_error_clause = "error:3"
    if _expected_error is None and (((record).price < 0)):
        _expected_error = StockRecordError_NegativePrice
        _expected_error_span = {"end_byte":1244,"end_column":65,"end_line":43,"start_byte":1184,"start_column":5,"start_line":43}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/stock_record/value_stock_record.py", "4c175897b8d2d60ee282f7a056583ef886e882b429f36d1ae7e0bfb4b03f3bae", "value_stock_record", expected_project_name="stock-record", expected_cott_symbol="curriculum.stock_record.value_stock_record")
        _result = _implementation(record)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.stock_record.value_stock_record"
        if _error.span is None:
            _error.span = {"end_byte":1290,"end_column":1,"end_line":45,"start_byte":666,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.stock_record.value_stock_record", phase="implementation-call", span={"end_byte":1290,"end_column":1,"end_line":45,"start_byte":666,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.stock_record.value_stock_record", phase="implementation-call", span={"end_byte":1290,"end_column":1,"end_line":45,"start_byte":666,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, StockRecordError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.stock_record.value_stock_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StockRecordError_NonFinitePrice, StockRecordError_ValuationOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.stock_record.value_stock_record", phase="error", span={"end_byte":1290,"end_column":1,"end_line":45,"start_byte":666,"start_column":1,"start_line":30}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.stock_record.value_stock_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return ((value >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.stock_record.value_stock_record", clause="ensures:1", phase="ensures", span={"end_byte":1008,"end_column":45,"end_line":38,"start_byte":968,"start_column":5,"start_line":38}, expected="true", actual="false")
    return _result

__all__ = ["StockRecord", "StockRecordError", "StockRecordError_EmptyName", "StockRecordError_NegativePrice", "StockRecordError_NegativeShares", "StockRecordError_NonFinitePrice", "StockRecordError_ValuationOverflow", "value_record", "value_stock_record"]
