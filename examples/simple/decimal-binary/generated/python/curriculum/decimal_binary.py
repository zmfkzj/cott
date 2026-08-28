from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

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
    if _expected_error is None and ((value < 0)):
        _expected_error = ConversionError_NegativeDecimal
        _expected_error_span = {"end_byte":706,"end_column":57,"end_line":27,"start_byte":654,"start_column":5,"start_line":27}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/decimal_binary/decimal_to_binary.py", "25609f36dfdefbf79bccbc2a2b03978ddf06304ede2e128104641bd9aacc739a", "decimal_to_binary", expected_project_name="decimal-binary", expected_cott_symbol="curriculum.decimal_binary.decimal_to_binary")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.decimal_binary.decimal_to_binary"
        if _error.span is None:
            _error.span = {"end_byte":708,"end_column":1,"end_line":29,"start_byte":263,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.decimal_binary.decimal_to_binary", phase="implementation-call", span={"end_byte":708,"end_column":1,"end_line":29,"start_byte":263,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.decimal_binary.decimal_to_binary", phase="implementation-call", span={"end_byte":708,"end_column":1,"end_line":29,"start_byte":263,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ConversionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.decimal_binary.decimal_to_binary", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.decimal_binary.decimal_to_binary", phase="error", span={"end_byte":708,"end_column":1,"end_line":29,"start_byte":263,"start_column":1,"start_line":16}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.decimal_binary.decimal_to_binary", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            digits = _cott_match_value.value
            return ((len(digits) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.decimal_to_binary", clause="ensures:1", phase="ensures", span={"end_byte":648,"end_column":48,"end_line":25,"start_byte":605,"start_column":5,"start_line":25}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/curriculum/decimal_binary/binary_to_decimal.py", "71f7577df389fb955989419fbd7f9c9d6b62acb31a5975f183dcf062696a86e0", "binary_to_decimal", expected_project_name="decimal-binary", expected_cott_symbol="curriculum.decimal_binary.binary_to_decimal")
        _result = _implementation(digits)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.decimal_binary.binary_to_decimal"
        if _error.span is None:
            _error.span = {"end_byte":1276,"end_column":1,"end_line":44,"start_byte":708,"start_column":1,"start_line":29}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.decimal_binary.binary_to_decimal", phase="implementation-call", span={"end_byte":1276,"end_column":1,"end_line":44,"start_byte":708,"start_column":1,"start_line":29}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.decimal_binary.binary_to_decimal", phase="implementation-call", span={"end_byte":1276,"end_column":1,"end_line":44,"start_byte":708,"start_column":1,"start_line":29}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[I64, ConversionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.decimal_binary.binary_to_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConversionError_InvalidBinary, ConversionError_Overflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.decimal_binary.binary_to_decimal", phase="error", span={"end_byte":1276,"end_column":1,"end_line":44,"start_byte":708,"start_column":1,"start_line":29}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.decimal_binary.binary_to_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return ((value >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.binary_to_decimal", clause="ensures:1", phase="ensures", span={"end_byte":1198,"end_column":43,"end_line":39,"start_byte":1160,"start_column":5,"start_line":39}, expected="true", actual="false")
    return _result

def convert_binary_decimal(operation: Conversion) -> Result[ConversionResult, ConversionError]:
    """Routes a tagged conversion through the matching decimal or binary
conversion operation and wraps its successful scalar result.

Errors from the selected operation are returned unchanged."""
    operation = _cott_validate_abi(operation, Conversion, path="$.operation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/decimal_binary/convert_binary_decimal.py", "0c47f2431ac0aea34b93eb2a292ea379ce9abba08f132b1a72ca917d47c8493b", "convert_binary_decimal", expected_project_name="decimal-binary", expected_cott_symbol="curriculum.decimal_binary.convert_binary_decimal")
        _result = _implementation(operation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.decimal_binary.convert_binary_decimal"
        if _error.span is None:
            _error.span = {"end_byte":1855,"end_column":1,"end_line":58,"start_byte":1276,"start_column":1,"start_line":44}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.decimal_binary.convert_binary_decimal", phase="implementation-call", span={"end_byte":1855,"end_column":1,"end_line":58,"start_byte":1276,"start_column":1,"start_line":44}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.decimal_binary.convert_binary_decimal", phase="implementation-call", span={"end_byte":1855,"end_column":1,"end_line":58,"start_byte":1276,"start_column":1,"start_line":44}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConversionResult, ConversionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.decimal_binary.convert_binary_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConversionError_NegativeDecimal, ConversionError_InvalidBinary, ConversionError_Overflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.decimal_binary.convert_binary_decimal", phase="error", span={"end_byte":1855,"end_column":1,"end_line":58,"start_byte":1276,"start_column":1,"start_line":44}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.decimal_binary.convert_binary_decimal", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is ConversionResult_Binary and True:
            digits = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return ((len(digits) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.convert_binary_decimal", clause="ensures:1", phase="ensures", span={"end_byte":1667,"end_column":73,"end_line":52,"start_byte":1599,"start_column":5,"start_line":52}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is ConversionResult_Decimal and True:
            value = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return ((value >= 0))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.decimal_binary.convert_binary_decimal", clause="ensures:2", phase="ensures", span={"end_byte":1736,"end_column":69,"end_line":53,"start_byte":1672,"start_column":5,"start_line":53}, expected="true", actual="false")
    return _result

__all__ = ["Conversion", "ConversionError", "ConversionError_InvalidBinary", "ConversionError_NegativeDecimal", "ConversionError_Overflow", "ConversionResult", "ConversionResult_Binary", "ConversionResult_Decimal", "Conversion_BinaryToDecimal", "Conversion_DecimalToBinary", "binary_to_decimal", "convert_binary_decimal", "decimal_to_binary"]
