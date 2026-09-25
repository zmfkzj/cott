from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.stock_record_types import MAX_F64, StockRecord, StockRecordError, StockRecordError_EmptyName, StockRecordError_NegativePrice, StockRecordError_NegativeShares, StockRecordError_NonFinitePrice, StockRecordError_ValuationOverflow

def value_record(record: StockRecord) -> Result[F64, StockRecordError]:
    """Computes the value of a validated stock record: the share count converted
to the nearest binary64 value, multiplied by the price with binary64
round-to-nearest, ties-to-even. The name does not affect the value.
ValuationOverflow is returned when the product is not finite."""
    record = _cott_validate_abi(record, StockRecord, path="$.record")
    if not (_cott_contract_condition((((record).shares >= 0)), "curriculum.stock_record.value_record", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.stock_record.value_record", clause="requires:1", phase="requires", span={"end_byte":671,"end_column":32,"end_line":25,"start_byte":644,"start_column":5,"start_line":25}, expected="true", actual="false")
    if not (_cott_contract_condition((((record).price >= 0)), "curriculum.stock_record.value_record", "requires:2")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.stock_record.value_record", clause="requires:2", phase="requires", span={"end_byte":704,"end_column":33,"end_line":26,"start_byte":676,"start_column":5,"start_line":26}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/stock_record/value_record.py", "7689ed3bae6806c28da8cd17cf5e83fda1f2ff3a7e502e2ebf074cd05725caea", "value_record", expected_project_name="stock-record", expected_cott_symbol="curriculum.stock_record.value_record")
        _result = _implementation(record)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.stock_record.value_record"
        if _error.span is None:
            _error.span = {"end_byte":809,"end_column":1,"end_line":32,"start_byte":259,"start_column":1,"start_line":17}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.stock_record.value_record", phase="implementation-call", span={"end_byte":809,"end_column":1,"end_line":32,"start_byte":259,"start_column":1,"start_line":17}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.stock_record.value_record", phase="implementation-call", span={"end_byte":809,"end_column":1,"end_line":32,"start_byte":259,"start_column":1,"start_line":17}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, StockRecordError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.stock_record.value_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StockRecordError_ValuationOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.stock_record.value_record", phase="error", span={"end_byte":809,"end_column":1,"end_line":32,"start_byte":259,"start_column":1,"start_line":17}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.stock_record.value_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.stock_record.value_record", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StockRecordError_ValuationOverflow:
        _cott_contract_condition(True, "curriculum.stock_record.value_record", "error:4")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return (_cott_contract_condition(((0 <= value <= MAX_F64)), "curriculum.stock_record.value_record", "ensures:3"))
        _cott_contract_condition((False), "curriculum.stock_record.value_record", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.stock_record.value_record", clause="ensures:3", phase="ensures", span={"end_byte":761,"end_column":56,"end_line":28,"start_byte":710,"start_column":5,"start_line":28}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[F64, StockRecordError], path="$.return", validator=_cott_validate_abi)
    return _result

def value_stock_record(record: StockRecord) -> Result[F64, StockRecordError]:
    """Validates one raw stock record and values it. For a record that passes
every validation clause, it calls the public
curriculum.stock_record.value_record facade and returns that result,
including ValuationOverflow, unchanged."""
    record = _cott_validate_abi(record, StockRecord, path="$.record")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len((record).name) == 0)), "curriculum.stock_record.value_stock_record", "error:2:condition")):
        _expected_error = StockRecordError_EmptyName
        _expected_error_span = {"end_byte":1267,"end_column":63,"end_line":42,"start_byte":1209,"start_column":5,"start_line":42}
        _expected_error_clause = "error:2"
    if _expected_error is None and (_cott_contract_condition((((record).shares < 0)), "curriculum.stock_record.value_stock_record", "error:3:condition")):
        _expected_error = StockRecordError_NegativeShares
        _expected_error_span = {"end_byte":1332,"end_column":65,"end_line":43,"start_byte":1272,"start_column":5,"start_line":43}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition(((not ((-MAX_F64) <= (record).price <= MAX_F64))), "curriculum.stock_record.value_stock_record", "error:4:condition")):
        _expected_error = StockRecordError_NonFinitePrice
        _expected_error_span = {"end_byte":1421,"end_column":89,"end_line":44,"start_byte":1337,"start_column":5,"start_line":44}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition((((record).price < 0)), "curriculum.stock_record.value_stock_record", "error:5:condition")):
        _expected_error = StockRecordError_NegativePrice
        _expected_error_span = {"end_byte":1486,"end_column":65,"end_line":45,"start_byte":1426,"start_column":5,"start_line":45}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/stock_record/value_stock_record.py", "f58d3429f4a0636fa300335291d707b42ec74989ef7177d49359188622d6fa5d", "value_stock_record", expected_project_name="stock-record", expected_cott_symbol="curriculum.stock_record.value_stock_record")
        _result = _implementation(record)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.stock_record.value_stock_record"
        if _error.span is None:
            _error.span = {"end_byte":1533,"end_column":1,"end_line":48,"start_byte":809,"start_column":1,"start_line":32}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.stock_record.value_stock_record", phase="implementation-call", span={"end_byte":1533,"end_column":1,"end_line":48,"start_byte":809,"start_column":1,"start_line":32}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.stock_record.value_stock_record", phase="implementation-call", span={"end_byte":1533,"end_column":1,"end_line":48,"start_byte":809,"start_column":1,"start_line":32}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, StockRecordError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.stock_record.value_stock_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StockRecordError_ValuationOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.stock_record.value_stock_record", phase="error", span={"end_byte":1533,"end_column":1,"end_line":48,"start_byte":809,"start_column":1,"start_line":32}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.stock_record.value_stock_record", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.stock_record.value_stock_record", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StockRecordError_ValuationOverflow:
        _cott_contract_condition(True, "curriculum.stock_record.value_stock_record", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return (_cott_contract_condition(((0 <= value <= MAX_F64)), "curriculum.stock_record.value_stock_record", "ensures:1"))
        _cott_contract_condition((False), "curriculum.stock_record.value_stock_record", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.stock_record.value_stock_record", clause="ensures:1", phase="ensures", span={"end_byte":1203,"end_column":56,"end_line":40,"start_byte":1152,"start_column":5,"start_line":40}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[F64, StockRecordError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["MAX_F64", "StockRecord", "StockRecordError", "StockRecordError_EmptyName", "StockRecordError_NegativePrice", "StockRecordError_NegativeShares", "StockRecordError_NonFinitePrice", "StockRecordError_ValuationOverflow", "value_record", "value_stock_record"]
