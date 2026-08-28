from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.calculator_types import CalculatorError, CalculatorError_DivideByZero, CalculatorError_NonFinite, CalculatorError_Overflow, CalculatorError_PowerDomain, CalculatorOp, CalculatorOp_Add, CalculatorOp_Divide, CalculatorOp_Multiply, CalculatorOp_Power, CalculatorOp_Subtract

def validate_calculation(left: F64, operator: CalculatorOp, right: F64) -> Result[Unit, CalculatorError]:
    """Validates one calculator request before evaluation.
Errors have this priority: NonFinite when either operand is NaN or
infinity, DivideByZero when division uses either sign of zero as the
divisor, then PowerDomain when zero has a negative exponent or a negative
base has a non-integral exponent."""
    left = _cott_validate_abi(left, F64, path="$.left")
    operator = _cott_validate_abi(operator, CalculatorOp, path="$.operator")
    right = _cott_validate_abi(right, F64, path="$.right")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((operator == CalculatorOp_Divide()) and (right == 0))):
        _expected_error = CalculatorError_DivideByZero
        _expected_error_span = {"end_byte":773,"end_column":93,"end_line":30,"start_byte":685,"start_column":5,"start_line":30}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/calculator/validate_calculation.py", "f380063d78dc704238bf812bd0d884f787cc3c2a84e7eae80f88c5c9f7857e27", "validate_calculation", expected_project_name="calculator", expected_cott_symbol="curriculum.calculator.validate_calculation")
        _result = _implementation(left, operator, right)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.calculator.validate_calculation"
        if _error.span is None:
            _error.span = {"end_byte":829,"end_column":1,"end_line":35,"start_byte":188,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.calculator.validate_calculation", phase="implementation-call", span={"end_byte":829,"end_column":1,"end_line":35,"start_byte":188,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.calculator.validate_calculation", phase="implementation-call", span={"end_byte":829,"end_column":1,"end_line":35,"start_byte":188,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, CalculatorError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.calculator.validate_calculation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CalculatorError_NonFinite, CalculatorError_PowerDomain,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.calculator.validate_calculation", phase="error", span={"end_byte":829,"end_column":1,"end_line":35,"start_byte":188,"start_column":1,"start_line":16}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.calculator.validate_calculation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    _result = _cott_wrap_async_protocol(_result, Result[Unit, CalculatorError], path="$.return", validator=_cott_validate_abi)
    return _result

def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]:
    """Validates and evaluates Add, Subtract, Multiply, Divide, or Power on two
binary64 operands. Validation errors are returned unchanged. A finite
result, including underflowed and signed zero values, is returned
unchanged; a non-finite result from finite operands returns Overflow.
Zero to the zero power is 1, and no operation returns a complex value."""
    left = _cott_validate_abi(left, F64, path="$.left")
    operator = _cott_validate_abi(operator, CalculatorOp, path="$.operator")
    right = _cott_validate_abi(right, F64, path="$.right")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((operator == CalculatorOp_Divide()) and (right == 0))):
        _expected_error = CalculatorError_DivideByZero
        _expected_error_span = {"end_byte":1441,"end_column":93,"end_line":45,"start_byte":1353,"start_column":5,"start_line":45}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/calculator/calculate.py", "6c06c023071d2f2d968b576a5f50e1c0b917d3c0669eb4676b9087dd88c7d796", "calculate", expected_project_name="calculator", expected_cott_symbol="curriculum.calculator.calculate")
        _result = _implementation(left, operator, right)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.calculator.calculate"
        if _error.span is None:
            _error.span = {"end_byte":1531,"end_column":1,"end_line":50,"start_byte":829,"start_column":1,"start_line":35}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.calculator.calculate", phase="implementation-call", span={"end_byte":1531,"end_column":1,"end_line":50,"start_byte":829,"start_column":1,"start_line":35}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.calculator.calculate", phase="implementation-call", span={"end_byte":1531,"end_column":1,"end_line":50,"start_byte":829,"start_column":1,"start_line":35}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, CalculatorError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.calculator.calculate", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CalculatorError_NonFinite, CalculatorError_PowerDomain, CalculatorError_Overflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.calculator.calculate", phase="error", span={"end_byte":1531,"end_column":1,"end_line":50,"start_byte":829,"start_column":1,"start_line":35}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.calculator.calculate", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    _result = _cott_wrap_async_protocol(_result, Result[F64, CalculatorError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CalculatorError", "CalculatorError_DivideByZero", "CalculatorError_NonFinite", "CalculatorError_Overflow", "CalculatorError_PowerDomain", "CalculatorOp", "CalculatorOp_Add", "CalculatorOp_Divide", "CalculatorOp_Multiply", "CalculatorOp_Power", "CalculatorOp_Subtract", "calculate", "validate_calculation"]
