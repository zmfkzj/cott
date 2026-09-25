from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from store.order_types import Order, OrderError, OrderError_EmptyOrder, OrderError_InvalidQuantity, OrderError_ItemUnavailable, OrderLine, OrderReceipt
from store.catalog_types import Catalog, CatalogError

def validate_line(line: OrderLine) -> Result[OrderLine, OrderError]:
    """Accept an order line with a positive quantity and return it unchanged."""
    line = _cott_validate_abi(line, OrderLine, path="$.line")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((line).quantity == 0)), "store.order.validate_line", "error:4:condition")):
        _expected_error = OrderError_InvalidQuantity
        _expected_error_span = {"end_byte":773,"end_column":61,"end_line":34,"start_byte":717,"start_column":5,"start_line":34}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/store/order/validate_line.py", "36a318de28bb71c54a3de790a7616b4f2c5ff9829016a003afcf606970519462", "validate_line", expected_project_name="order-management", expected_cott_symbol="store.order.validate_line")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "store.order.validate_line"
        if _error.span is None:
            _error.span = {"end_byte":791,"end_column":1,"end_line":38,"start_byte":397,"start_column":1,"start_line":25}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="store.order.validate_line", phase="implementation-call", span={"end_byte":791,"end_column":1,"end_line":38,"start_byte":397,"start_column":1,"start_line":25}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="store.order.validate_line", phase="implementation-call", span={"end_byte":791,"end_column":1,"end_line":38,"start_byte":397,"start_column":1,"start_line":25}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[OrderLine, OrderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="store.order.validate_line", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="store.order.validate_line", phase="error", span={"end_byte":791,"end_column":1,"end_line":38,"start_byte":397,"start_column":1,"start_line":25}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="store.order.validate_line", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "store.order.validate_line", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (_cott_contract_condition(((valid == line)), "store.order.validate_line", "ensures:1"))
        _cott_contract_condition((False), "store.order.validate_line", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="store.order.validate_line", clause="ensures:1", phase="ensures", span={"end_byte":606,"end_column":46,"end_line":30,"start_byte":565,"start_column":5,"start_line":30}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is OrderError_InvalidQuantity and True:
            rejected = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((rejected == (line).sku)), "store.order.validate_line", "ensures:2"))
        _cott_contract_condition((False), "store.order.validate_line", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="store.order.validate_line", clause="ensures:2", phase="ensures", span={"end_byte":691,"end_column":85,"end_line":31,"start_byte":611,"start_column":5,"start_line":31}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[OrderLine, OrderError], path="$.return", validator=_cott_validate_abi)
    return _result

def calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]:
    """Price an order against a catalog and summarize it as a receipt.

`total_items` is the sum of the line quantities, and `total_cents` is the sum over lines of
the quantity times the matching catalog item's `price_cents`; a SKU on several lines counts
once per line. Callers keep both totals within U32 and U64; larger orders are outside this
contract."""
    catalog = _cott_validate_abi(catalog, Catalog, path="$.catalog")
    order = _cott_validate_abi(order, Order, path="$.order")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len((order).lines) == 0)), "store.order.calculate_order", "error:2:condition")):
        _expected_error = OrderError_EmptyOrder
        _expected_error_span = {"end_byte":1401,"end_column":58,"end_line":50,"start_byte":1348,"start_column":5,"start_line":50}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/store/order/calculate_order.py", "6c4073f6a38540b9afe9e915fa3e84c4c4fd67e4b055b8dc981a855d8271fb35", "calculate_order", expected_project_name="order-management", expected_cott_symbol="store.order.calculate_order")
        _result = _implementation(catalog, order)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "store.order.calculate_order"
        if _error.span is None:
            _error.span = {"end_byte":1493,"end_column":1,"end_line":56,"start_byte":791,"start_column":1,"start_line":38}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="store.order.calculate_order", phase="implementation-call", span={"end_byte":1493,"end_column":1,"end_line":56,"start_byte":791,"start_column":1,"start_line":38}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="store.order.calculate_order", phase="implementation-call", span={"end_byte":1493,"end_column":1,"end_line":56,"start_byte":791,"start_column":1,"start_line":38}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[OrderReceipt, OrderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="store.order.calculate_order", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (OrderError_InvalidQuantity, OrderError_ItemUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="store.order.calculate_order", phase="error", span={"end_byte":1493,"end_column":1,"end_line":56,"start_byte":791,"start_column":1,"start_line":38}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="store.order.calculate_order", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "store.order.calculate_order", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is OrderError_InvalidQuantity:
        _cott_contract_condition(True, "store.order.calculate_order", "error:3")
    if type(_result) is Err and type(_result.error) is OrderError_ItemUnavailable:
        _cott_contract_condition(True, "store.order.calculate_order", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).order_id == (order).order_id)), "store.order.calculate_order", "ensures:1"))
        _cott_contract_condition((False), "store.order.calculate_order", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="store.order.calculate_order", clause="ensures:1", phase="ensures", span={"end_byte":1342,"end_column":69,"end_line":48,"start_byte":1278,"start_column":5,"start_line":48}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[OrderReceipt, OrderError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Order", "OrderError", "OrderError_EmptyOrder", "OrderError_InvalidQuantity", "OrderError_ItemUnavailable", "OrderLine", "OrderReceipt", "calculate_order", "validate_line"]
