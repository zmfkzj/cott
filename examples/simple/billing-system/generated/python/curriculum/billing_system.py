from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.billing_system_types import BillTotals, BillingError, BillingError_DuplicateItem, BillingError_NegativeQuantity, BillingError_WrongCategory, BillingItem, BillingItem_Coke, BillingItem_Daal, BillingItem_Dettol, BillingItem_Fanta, BillingItem_Flour, BillingItem_FoodOil, BillingItem_HandGloves, BillingItem_Limka, BillingItem_Maggi, BillingItem_Mask, BillingItem_Mazza, BillingItem_MountainDuo, BillingItem_Newsprin, BillingItem_Rice, BillingItem_Sanitizer, BillingItem_Sprite, BillingItem_ThermalGun, BillingItem_Wheat, Quantity

def validate_bill_lines(medical: CottList[Quantity], grocery: CottList[Quantity], drinks: CottList[Quantity]) -> Result[Unit, BillingError]:
    """Validate all bill lines before any price or tax arithmetic. Validation makes three complete passes in priority order: any negative quantity returns NegativeQuantity; otherwise an item repeated anywhere across the three lists returns DuplicateItem; otherwise an item placed outside its medical, grocery, or drinks category returns WrongCategory. Zero quantities are valid and still participate in duplicate detection."""
    medical = _cott_validate_abi(medical, CottList[Quantity], path="$.medical")
    grocery = _cott_validate_abi(grocery, CottList[Quantity], path="$.grocery")
    drinks = _cott_validate_abi(drinks, CottList[Quantity], path="$.drinks")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/billing_system/validate_bill_lines.py", "9a4887b894a82d0157865f99e2c89dcd93cdcc9d94234e0e83a4596e6a95970e", "validate_bill_lines", expected_project_name="billing-system", expected_cott_symbol="curriculum.billing_system.validate_bill_lines")
        _result = _implementation(medical, grocery, drinks)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.billing_system.validate_bill_lines"
        if _error.span is None:
            _error.span = {"end_byte":1265,"end_column":1,"end_line":54,"start_byte":565,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.billing_system.validate_bill_lines", phase="implementation-call", span={"end_byte":1265,"end_column":1,"end_line":54,"start_byte":565,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.billing_system.validate_bill_lines", phase="implementation-call", span={"end_byte":1265,"end_column":1,"end_line":54,"start_byte":565,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, BillingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.billing_system.validate_bill_lines", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (BillingError_NegativeQuantity, BillingError_DuplicateItem, BillingError_WrongCategory,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.billing_system.validate_bill_lines", phase="error", span={"end_byte":1265,"end_column":1,"end_line":54,"start_byte":565,"start_column":1,"start_line":41}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.billing_system.validate_bill_lines", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    _result = _cott_wrap_async_protocol(_result, Result[Unit, BillingError], path="$.return", validator=_cott_validate_abi)
    return _result

def calculate_bill(medical: CottList[Quantity], grocery: CottList[Quantity], drinks: CottList[Quantity]) -> Result[BillTotals, BillingError]:
    """Validate the bill through validate_bill_lines, then calculate exact-cent subtotals and independently rounded taxes from this catalog of unit prices in cents: medical has Sanitizer 200, Mask 500, HandGloves 1200, Dettol 3000, Newsprin 500, and ThermalGun 1500; grocery has Rice 1000, FoodOil 1000, Wheat 1000, Daal 600, Flour 800, and Maggi 500; drinks has Sprite 1000, Limka 1000, Mazza 1000, Coke 1000, Fanta 1000, and MountainDuo 1000. Medical and grocery tax are 5 percent; drinks tax is 10 percent. Each tax is rounded to the nearest cent with ties to the even cent, and returned F64 fields are cent amounts divided by 100.

A validation error is returned unchanged. On success, the total is the sum of all three subtotals and all three rounded taxes."""
    medical = _cott_validate_abi(medical, CottList[Quantity], path="$.medical")
    grocery = _cott_validate_abi(grocery, CottList[Quantity], path="$.grocery")
    drinks = _cott_validate_abi(drinks, CottList[Quantity], path="$.drinks")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/billing_system/calculate_bill.py", "bcbb697dbd98168266fba4692c3158fc46cecb35e8a7bea2597a7802a5dfcd11", "calculate_bill", expected_project_name="billing-system", expected_cott_symbol="curriculum.billing_system.calculate_bill")
        _result = _implementation(medical, grocery, drinks)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.billing_system.calculate_bill"
        if _error.span is None:
            _error.span = {"end_byte":2366,"end_column":1,"end_line":70,"start_byte":1265,"start_column":1,"start_line":54}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.billing_system.calculate_bill", phase="implementation-call", span={"end_byte":2366,"end_column":1,"end_line":70,"start_byte":1265,"start_column":1,"start_line":54}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.billing_system.calculate_bill", phase="implementation-call", span={"end_byte":2366,"end_column":1,"end_line":70,"start_byte":1265,"start_column":1,"start_line":54}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[BillTotals, BillingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.billing_system.calculate_bill", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (BillingError_NegativeQuantity, BillingError_DuplicateItem, BillingError_WrongCategory,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.billing_system.calculate_bill", phase="error", span={"end_byte":2366,"end_column":1,"end_line":70,"start_byte":1265,"start_column":1,"start_line":54}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.billing_system.calculate_bill", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            totals = _cott_match_value.value
            return (((totals).total >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.billing_system.calculate_bill", clause="ensures:1", phase="ensures", span={"end_byte":2250,"end_column":53,"end_line":65,"start_byte":2202,"start_column":5,"start_line":65}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[BillTotals, BillingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["BillTotals", "BillingError", "BillingError_DuplicateItem", "BillingError_NegativeQuantity", "BillingError_WrongCategory", "BillingItem", "BillingItem_Coke", "BillingItem_Daal", "BillingItem_Dettol", "BillingItem_Fanta", "BillingItem_Flour", "BillingItem_FoodOil", "BillingItem_HandGloves", "BillingItem_Limka", "BillingItem_Maggi", "BillingItem_Mask", "BillingItem_Mazza", "BillingItem_MountainDuo", "BillingItem_Newsprin", "BillingItem_Rice", "BillingItem_Sanitizer", "BillingItem_Sprite", "BillingItem_ThermalGun", "BillingItem_Wheat", "Quantity", "calculate_bill", "validate_bill_lines"]
