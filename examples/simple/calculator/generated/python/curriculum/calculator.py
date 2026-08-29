from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.calculator_types import CalculatorError, CalculatorError_DivideByZero, CalculatorOp, CalculatorOp_Add, CalculatorOp_Divide, CalculatorOp_Multiply, CalculatorOp_Subtract

def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]:
    """Apply one arithmetic operation and reject division by zero."""
    left = _cott_validate_abi(left, F64, path="$.left")
    operator = _cott_validate_abi(operator, CalculatorOp, path="$.operator")
    right = _cott_validate_abi(right, F64, path="$.right")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((operator == CalculatorOp_Divide()) and (right == 0))):
        _expected_error = CalculatorError_DivideByZero
        _expected_error_span = {"end_byte":707,"end_column":93,"end_line":19,"start_byte":619,"start_column":5,"start_line":19}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/calculator/calculate.py", "987fc97088de287ad24161f6cad118c7f1a960e4a2b1d43f8af3fedd949662ce", "calculate", expected_project_name="calculator", expected_cott_symbol="curriculum.calculator.calculate")
        _result = _implementation(left, operator, right)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.calculator.calculate"
        if _error.span is None:
            _error.span = {"end_byte":708,"end_column":1,"end_line":20,"start_byte":135,"start_column":1,"start_line":12}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.calculator.calculate", phase="implementation-call", span={"end_byte":708,"end_column":1,"end_line":20,"start_byte":135,"start_column":1,"start_line":12}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.calculator.calculate", phase="implementation-call", span={"end_byte":708,"end_column":1,"end_line":20,"start_byte":135,"start_column":1,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, CalculatorError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.calculator.calculate", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.calculator.calculate", phase="error", span={"end_byte":708,"end_column":1,"end_line":20,"start_byte":135,"start_column":1,"start_line":12}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.calculator.calculate", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return ((((((operator == CalculatorOp_Add()) and (value == (left + right))) or ((operator == CalculatorOp_Subtract()) and (value == (left - right)))) or ((operator == CalculatorOp_Multiply()) and (value == (left * right)))) or (((operator == CalculatorOp_Divide()) and (right != 0)) and (value == (left / right)))))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.calculator.calculate", clause="ensures:1", phase="ensures", span={"end_byte":613,"end_column":301,"end_line":17,"start_byte":317,"start_column":5,"start_line":17}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[F64, CalculatorError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CalculatorError", "CalculatorError_DivideByZero", "CalculatorOp", "CalculatorOp_Add", "CalculatorOp_Divide", "CalculatorOp_Multiply", "CalculatorOp_Subtract", "calculate"]
