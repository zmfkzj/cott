from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from store.order_types import Order, OrderError, OrderError_EmptyOrder, OrderError_InvalidQuantity, OrderError_ItemUnavailable, OrderLine, OrderReceipt
from store.catalog_types import Catalog, CatalogError

def validate_line(line: OrderLine) -> Result[OrderLine, OrderError]:
    """Ensure an order line has positive quantity."""
    line = _cott_validate_abi(line, OrderLine, path="$.line")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((line).quantity == 0)):
        _expected_error = OrderError_InvalidQuantity
        _expected_error_span = {"end_byte":614,"end_column":61,"end_line":30,"start_byte":558,"start_column":5,"start_line":30}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/store/order/validate_line.py", "36a318de28bb71c54a3de790a7616b4f2c5ff9829016a003afcf606970519462", "validate_line", expected_project_name="order-management", expected_cott_symbol="store.order.validate_line")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "store.order.validate_line"
        if _error.span is None:
            _error.span = {"end_byte":616,"end_column":1,"end_line":32,"start_byte":365,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="store.order.validate_line", phase="implementation-call", span={"end_byte":616,"end_column":1,"end_line":32,"start_byte":365,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="store.order.validate_line", phase="implementation-call", span={"end_byte":616,"end_column":1,"end_line":32,"start_byte":365,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[OrderLine, OrderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="store.order.validate_line", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="store.order.validate_line", phase="error", span={"end_byte":616,"end_column":1,"end_line":32,"start_byte":365,"start_column":1,"start_line":23}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="store.order.validate_line", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (((valid).quantity > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="store.order.validate_line", clause="ensures:1", phase="ensures", span={"end_byte":552,"end_column":51,"end_line":28,"start_byte":506,"start_column":5,"start_line":28}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[OrderLine, OrderError], path="$.return", validator=_cott_validate_abi)
    return _result

def calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]:
    """Validate all order lines, lookup item prices, and produce a receipt."""
    catalog = _cott_validate_abi(catalog, Catalog, path="$.catalog")
    order = _cott_validate_abi(order, Order, path="$.order")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((order).lines) == 0)):
        _expected_error = OrderError_EmptyOrder
        _expected_error_span = {"end_byte":925,"end_column":58,"end_line":39,"start_byte":872,"start_column":5,"start_line":39}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/store/order/calculate_order.py", "cc9319adbf323ba6594a669f824c4f58718173d73d4f8d5a1f76b6c033fd7900", "calculate_order", expected_project_name="order-management", expected_cott_symbol="store.order.calculate_order")
        _result = _implementation(catalog, order)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "store.order.calculate_order"
        if _error.span is None:
            _error.span = {"end_byte":1000,"end_column":1,"end_line":42,"start_byte":616,"start_column":1,"start_line":32}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="store.order.calculate_order", phase="implementation-call", span={"end_byte":1000,"end_column":1,"end_line":42,"start_byte":616,"start_column":1,"start_line":32}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="store.order.calculate_order", phase="implementation-call", span={"end_byte":1000,"end_column":1,"end_line":42,"start_byte":616,"start_column":1,"start_line":32}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[OrderReceipt, OrderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="store.order.calculate_order", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (OrderError_InvalidQuantity, OrderError_ItemUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="store.order.calculate_order", phase="error", span={"end_byte":1000,"end_column":1,"end_line":42,"start_byte":616,"start_column":1,"start_line":32}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="store.order.calculate_order", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).order_id == (order).order_id))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="store.order.calculate_order", clause="ensures:1", phase="ensures", span={"end_byte":866,"end_column":69,"end_line":37,"start_byte":802,"start_column":5,"start_line":37}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[OrderReceipt, OrderError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Order", "OrderError", "OrderError_EmptyOrder", "OrderError_InvalidQuantity", "OrderError_ItemUnavailable", "OrderLine", "OrderReceipt", "calculate_order", "validate_line"]
