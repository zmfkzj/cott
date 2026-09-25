from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.decimal_binary_types import Conversion, ConversionError, ConversionError_InvalidBinary, ConversionError_NegativeDecimal, ConversionError_Overflow, ConversionResult, ConversionResult_Binary, ConversionResult_Decimal, Conversion_BinaryToDecimal, Conversion_DecimalToBinary

def decimal_to_binary(value: I64) -> Result[str, ConversionError]:
    """Converts one decimal I64 to canonical binary text.

Every nonnegative value succeeds with the shortest sequence of ASCII `0`
and `1` digits, without leading zeros; zero is exactly `"0"`. A negative
value returns `NegativeDecimal`."""
    value = _cott_validate_abi(value, I64, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((value < 0)), "curriculum.decimal_binary.decimal_to_binary", "error:4:condition")):
        _expected_error = ConversionError_NegativeDecimal
        _expected_error_span = {"end_byte":831,"end_column":57,"end_line":29,"start_byte":779,"start_column":5,"start_line":29}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/decimal_binary/decimal_to_binary.py", "5e54ade431020ff72a43e12cf361a832cb63cc6de31f329b8fdc1d1a9caf028b", "decimal_to_binary", expected_project_name="decimal-binary", expected_cott_symbol="curriculum.decimal_binary.decimal_to_binary")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.decimal_binary.decimal_to_binary"
        if _error.span is None:
            _error.span = {"end_byte":833,"end_column":1,"end_line":31,"start_byte":263,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.decimal_binary.decimal_to_binary", phase="implementation-call", span={"end_byte":833,"end_column":1,"end_line":31,"start_byte":263,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.decimal_binary.decimal_to_binary", phase="implementation-call", span={"end_byte":833,"end_column":1,"end_line":31,"start_byte":263,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ConversionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.decimal_binary.decimal_to_binary", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.decimal_binary.decimal_to_binary", phase="error", span={"end_byte":833,"end_column":1,"end_line":31,"start_byte":263,"start_column":1,"start_line":16}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.decimal_binary.decimal_to_binary", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.decimal_binary.decimal_to_binary", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            digits = _cott_match_value.value
            return (_cott_contract_condition(((len(digits) > 0)), "curriculum.decimal_binary.decimal_to_binary", "ensures:1"))
        _cott_contract_condition((False), "curriculum.decimal_binary.decimal_to_binary", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.decimal_to_binary", clause="ensures:1", phase="ensures", span={"end_byte":648,"end_column":48,"end_line":25,"start_byte":605,"start_column":5,"start_line":25}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            digits = _cott_match_value.value
            return (_cott_contract_condition((((not (value == 0)) or (digits == "0"))), "curriculum.decimal_binary.decimal_to_binary", "ensures:2"))
        _cott_contract_condition((False), "curriculum.decimal_binary.decimal_to_binary", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.decimal_to_binary", clause="ensures:2", phase="ensures", span={"end_byte":711,"end_column":63,"end_line":26,"start_byte":653,"start_column":5,"start_line":26}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            digits = _cott_match_value.value
            return (_cott_contract_condition((((not (value > 0)) or (digits != "0"))), "curriculum.decimal_binary.decimal_to_binary", "ensures:3"))
        _cott_contract_condition((False), "curriculum.decimal_binary.decimal_to_binary", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.decimal_to_binary", clause="ensures:3", phase="ensures", span={"end_byte":773,"end_column":62,"end_line":27,"start_byte":716,"start_column":5,"start_line":27}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, ConversionError], path="$.return", validator=_cott_validate_abi)
    return _result

def binary_to_decimal(digits: str) -> Result[I64, ConversionError]:
    """Converts binary text to a nonnegative decimal I64.

The input must be nonempty and contain only ASCII `0` and `1`; leading
zeros are allowed and ignored. Any other input returns `InvalidBinary`.
After the entire string is validated, more than 63 significant digits
returns `Overflow`, so invalid characters take priority over overflow."""
    digits = _cott_validate_abi(digits, str, path="$.digits")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/decimal_binary/binary_to_decimal.py", "be473999a0c33b58b50f9093a05f53fef8bacdb0f37d0f3583fceffc59e23c6d", "binary_to_decimal", expected_project_name="decimal-binary", expected_cott_symbol="curriculum.decimal_binary.binary_to_decimal")
        _result = _implementation(digits)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.decimal_binary.binary_to_decimal"
        if _error.span is None:
            _error.span = {"end_byte":2198,"end_column":1,"end_line":61,"start_byte":1568,"start_column":1,"start_line":45}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.decimal_binary.binary_to_decimal", phase="implementation-call", span={"end_byte":2198,"end_column":1,"end_line":61,"start_byte":1568,"start_column":1,"start_line":45}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.decimal_binary.binary_to_decimal", phase="implementation-call", span={"end_byte":2198,"end_column":1,"end_line":61,"start_byte":1568,"start_column":1,"start_line":45}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[I64, ConversionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.decimal_binary.binary_to_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConversionError_InvalidBinary, ConversionError_Overflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.decimal_binary.binary_to_decimal", phase="error", span={"end_byte":2198,"end_column":1,"end_line":61,"start_byte":1568,"start_column":1,"start_line":45}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.decimal_binary.binary_to_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.decimal_binary.binary_to_decimal", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConversionError_InvalidBinary:
        _cott_contract_condition(True, "curriculum.decimal_binary.binary_to_decimal", "error:3")
    if type(_result) is Err and type(_result.error) is ConversionError_Overflow:
        _cott_contract_condition(True, "curriculum.decimal_binary.binary_to_decimal", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return (_cott_contract_condition(((value >= 0)), "curriculum.decimal_binary.binary_to_decimal", "ensures:1"))
        _cott_contract_condition((False), "curriculum.decimal_binary.binary_to_decimal", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.binary_to_decimal", clause="ensures:1", phase="ensures", span={"end_byte":2058,"end_column":43,"end_line":55,"start_byte":2020,"start_column":5,"start_line":55}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return (_cott_contract_condition((((not (digits == "0")) or (value == 0))), "curriculum.decimal_binary.binary_to_decimal", "ensures:2"))
        _cott_contract_condition((False), "curriculum.decimal_binary.binary_to_decimal", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.binary_to_decimal", clause="ensures:2", phase="ensures", span={"end_byte":2120,"end_column":62,"end_line":56,"start_byte":2063,"start_column":5,"start_line":56}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[I64, ConversionError], path="$.return", validator=_cott_validate_abi)
    return _result

def convert_binary_decimal(operation: Conversion) -> Result[ConversionResult, ConversionError]:
    """Route DecimalToBinary through curriculum.decimal_binary.decimal_to_binary
and wrap its successful digits in ConversionResult.Binary; do not call
binary_to_decimal on this branch. Route BinaryToDecimal through
curriculum.decimal_binary.binary_to_decimal and wrap its successful value
in ConversionResult.Decimal; do not call decimal_to_binary on this branch.
Return the selected leaf's NegativeDecimal, InvalidBinary or Overflow
unchanged, without trying the opposite conversion."""
    operation = _cott_validate_abi(operation, Conversion, path="$.operation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/decimal_binary/convert_binary_decimal.py", "94689bc3e6b355983902c39fd4659f7d36396260024c9bba2ce7ad8472127238", "convert_binary_decimal", expected_project_name="decimal-binary", expected_cott_symbol="curriculum.decimal_binary.convert_binary_decimal")
        _result = _implementation(operation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.decimal_binary.convert_binary_decimal"
        if _error.span is None:
            _error.span = {"end_byte":4208,"end_column":1,"end_line":97,"start_byte":3324,"start_column":1,"start_line":79}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.decimal_binary.convert_binary_decimal", phase="implementation-call", span={"end_byte":4208,"end_column":1,"end_line":97,"start_byte":3324,"start_column":1,"start_line":79}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.decimal_binary.convert_binary_decimal", phase="implementation-call", span={"end_byte":4208,"end_column":1,"end_line":97,"start_byte":3324,"start_column":1,"start_line":79}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConversionResult, ConversionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.decimal_binary.convert_binary_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConversionError_NegativeDecimal, ConversionError_InvalidBinary, ConversionError_Overflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.decimal_binary.convert_binary_decimal", phase="error", span={"end_byte":4208,"end_column":1,"end_line":97,"start_byte":3324,"start_column":1,"start_line":79}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.decimal_binary.convert_binary_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.decimal_binary.convert_binary_decimal", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConversionError_NegativeDecimal:
        _cott_contract_condition(True, "curriculum.decimal_binary.convert_binary_decimal", "error:3")
    if type(_result) is Err and type(_result.error) is ConversionError_InvalidBinary:
        _cott_contract_condition(True, "curriculum.decimal_binary.convert_binary_decimal", "error:4")
    if type(_result) is Err and type(_result.error) is ConversionError_Overflow:
        _cott_contract_condition(True, "curriculum.decimal_binary.convert_binary_decimal", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is ConversionResult_Binary and True:
            digits = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((len(digits) > 0)), "curriculum.decimal_binary.convert_binary_decimal", "ensures:1"))
        _cott_contract_condition((False), "curriculum.decimal_binary.convert_binary_decimal", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.convert_binary_decimal", clause="ensures:1", phase="ensures", span={"end_byte":4019,"end_column":73,"end_line":90,"start_byte":3951,"start_column":5,"start_line":90}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is ConversionResult_Decimal and True:
            value = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((value >= 0)), "curriculum.decimal_binary.convert_binary_decimal", "ensures:2"))
        _cott_contract_condition((False), "curriculum.decimal_binary.convert_binary_decimal", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.convert_binary_decimal", clause="ensures:2", phase="ensures", span={"end_byte":4088,"end_column":69,"end_line":91,"start_byte":4024,"start_column":5,"start_line":91}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConversionResult, ConversionError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Conversion", "ConversionError", "ConversionError_InvalidBinary", "ConversionError_NegativeDecimal", "ConversionError_Overflow", "ConversionResult", "ConversionResult_Binary", "ConversionResult_Decimal", "Conversion_BinaryToDecimal", "Conversion_DecimalToBinary", "binary_to_decimal", "convert_binary_decimal", "decimal_to_binary"]
