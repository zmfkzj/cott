from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.inventory_reorder_types import InventoryReorderError, InventoryReorderError_BlankSku, InventoryReorderError_ReservedExceedsOnHand, InventoryReorderError_TargetBelowReorderPoint, ReorderPlan, ReorderRequest

def available_stock(on_hand: U64, reserved: U64) -> Result[U64, InventoryReorderError]:
    """Compute stock available for reorder planning after reservations. Return
ReservedExceedsOnHand when reservations cannot be subtracted safely."""
    on_hand = _cott_validate_abi(on_hand, U64, path="$.on_hand")
    reserved = _cott_validate_abi(reserved, U64, path="$.reserved")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((reserved > on_hand)):
        _expected_error = InventoryReorderError_ReservedExceedsOnHand
        _expected_error_span = {"end_byte":706,"end_column":78,"end_line":27,"start_byte":633,"start_column":5,"start_line":27}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/inventory_reorder/available_stock.py", "21c90bffb32f7cc93acf3e2a29609b18c9d7e46ffc97b92f5892c967c40729eb", "available_stock", expected_project_name="inventory-reorder", expected_cott_symbol="curriculum.inventory_reorder.available_stock")
        _result = _implementation(on_hand, reserved)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.inventory_reorder.available_stock"
        if _error.span is None:
            _error.span = {"end_byte":724,"end_column":1,"end_line":31,"start_byte":303,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.inventory_reorder.available_stock", phase="implementation-call", span={"end_byte":724,"end_column":1,"end_line":31,"start_byte":303,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.inventory_reorder.available_stock", phase="implementation-call", span={"end_byte":724,"end_column":1,"end_line":31,"start_byte":303,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[U64, InventoryReorderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.inventory_reorder.available_stock", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.inventory_reorder.available_stock", phase="error", span={"end_byte":724,"end_column":1,"end_line":31,"start_byte":303,"start_column":1,"start_line":19}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.inventory_reorder.available_stock", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        available = _result.value
        if not ((available == (on_hand - reserved))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.inventory_reorder.available_stock", clause="ensures:1", phase="ensures", span={"end_byte":627,"end_column":68,"end_line":25,"start_byte":564,"start_column":5,"start_line":25}, expected="true", actual="false")
    return _result

def plan_reorder(request: ReorderRequest) -> Result[ReorderPlan, InventoryReorderError]:
    """Validate one inventory request and build its deterministic reorder plan.
A blank SKU is rejected before available stock is computed. An invalid
target is rejected afterward. Stock at or below the reorder point is
replenished to the target level; stock above it produces a zero-quantity
plan."""
    request = _cott_validate_abi(request, ReorderRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((request).sku) == 0)):
        _expected_error = InventoryReorderError_BlankSku
        _expected_error_span = {"end_byte":1532,"end_column":67,"end_line":43,"start_byte":1470,"start_column":5,"start_line":43}
        _expected_error_clause = "error:3"
    if _expected_error is None and (((len((request).sku) > 0) and ((request).reserved > (request).on_hand))):
        _expected_error = InventoryReorderError_ReservedExceedsOnHand
        _expected_error_span = {"end_byte":1652,"end_column":120,"end_line":44,"start_byte":1537,"start_column":5,"start_line":44}
        _expected_error_clause = "error:4"
    if _expected_error is None and ((((len((request).sku) > 0) and ((request).reserved <= (request).on_hand)) and ((request).target_level < (request).reorder_point))):
        _expected_error = InventoryReorderError_TargetBelowReorderPoint
        _expected_error_span = {"end_byte":1824,"end_column":172,"end_line":45,"start_byte":1657,"start_column":5,"start_line":45}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/inventory_reorder/plan_reorder.py", "52b079af6963d8b08b5cd0334dc0a5e52be37a671e590fe79a712bb745ce54af", "plan_reorder", expected_project_name="inventory-reorder", expected_cott_symbol="curriculum.inventory_reorder.plan_reorder")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.inventory_reorder.plan_reorder"
        if _error.span is None:
            _error.span = {"end_byte":1841,"end_column":1,"end_line":48,"start_byte":724,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.inventory_reorder.plan_reorder", phase="implementation-call", span={"end_byte":1841,"end_column":1,"end_line":48,"start_byte":724,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.inventory_reorder.plan_reorder", phase="implementation-call", span={"end_byte":1841,"end_column":1,"end_line":48,"start_byte":724,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ReorderPlan, InventoryReorderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.inventory_reorder.plan_reorder", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.inventory_reorder.plan_reorder", phase="error", span={"end_byte":1841,"end_column":1,"end_line":48,"start_byte":724,"start_column":1,"start_line":31}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.inventory_reorder.plan_reorder", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        plan = _result.value
        if not (((plan).sku == (request).sku)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.inventory_reorder.plan_reorder", clause="ensures:1", phase="ensures", span={"end_byte":1199,"end_column":55,"end_line":40,"start_byte":1149,"start_column":5,"start_line":40}, expected="true", actual="false")
    if type(_result) is Ok and True:
        plan = _result.value
        if not ((((((request).on_hand - (request).reserved) <= (request).reorder_point) and ((plan).order_qty == ((request).target_level - ((request).on_hand - (request).reserved)))) or ((((request).on_hand - (request).reserved) > (request).reorder_point) and ((plan).order_qty == 0)))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.inventory_reorder.plan_reorder", clause="ensures:2", phase="ensures", span={"end_byte":1464,"end_column":265,"end_line":41,"start_byte":1204,"start_column":5,"start_line":41}, expected="true", actual="false")
    return _result

__all__ = ["InventoryReorderError", "InventoryReorderError_BlankSku", "InventoryReorderError_ReservedExceedsOnHand", "InventoryReorderError_TargetBelowReorderPoint", "ReorderPlan", "ReorderRequest", "available_stock", "plan_reorder"]
