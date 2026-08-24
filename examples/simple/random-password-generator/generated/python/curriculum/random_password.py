from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.random_password_types import PasswordError, PasswordError_InsufficientDraws, PasswordError_InvalidLength

def required_password_draws(length: I64) -> Result[I64, PasswordError]:
    """For a length n from 1 through 128 inclusive, returns
2n + floor(n / 2) - 1, the exact number of draws generate_password
consumes. Every other length returns InvalidLength."""
    length = _cott_validate_abi(length, I64, path="$.length")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((length < 1) or (length > 128))):
        _expected_error = PasswordError_InvalidLength
        _expected_error_span = {"end_byte":441,"end_column":70,"end_line":14,"start_byte":376,"start_column":5,"start_line":14}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/random_password/required_password_draws.py", "2fb803c2da2aae14e73c6dd503b72a0bc6478642e9229e657c84b8cd6a17dc6e", "required_password_draws", expected_project_name="random-password-generator", expected_cott_symbol="curriculum.random_password.required_password_draws")
        _result = _implementation(length)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.random_password.required_password_draws"
        if _error.span is None:
            _error.span = {"end_byte":443,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":7}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.random_password.required_password_draws", phase="implementation-call", span={"end_byte":443,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":7}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.random_password.required_password_draws", phase="implementation-call", span={"end_byte":443,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":7}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[I64, PasswordError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.random_password.required_password_draws", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.random_password.required_password_draws", phase="error", span={"end_byte":443,"end_column":1,"end_line":16,"start_byte":96,"start_column":1,"start_line":7}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.random_password.required_password_draws", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def generate_password(length: I64, draws: CottList[I64]) -> Result[str, PasswordError]:
    """Validates length before inspecting draws, so a length outside 1 through 128
returns InvalidLength even when draws are insufficient. For a valid length
n, exactly 2n + floor(n / 2) - 1 draws are required; a shorter list returns
InsufficientDraws without indexing it, and later draws are ignored.

The password contains floor(n / 2) letters, ceil(3n / 10) digits, and
n minus those two counts special characters. Draws are consumed as two per
letter, then one per digit, then one per special character, followed by
n - 1 shuffle draws. For each letter, the first draw's least nonnegative
remainder modulo 26 selects from "abcdefghijklmnopqrstuvwxyz"; the second
draw's remainder modulo 2 chooses lowercase for 0 or uppercase for 1.
Digit draws select from "0123456789" modulo 10, and special-character draws
select from "@#$%&*" modulo 6.

Letters, digits, and special characters are first concatenated in that
order. Fisher-Yates then visits indices i from n - 1 down through 1 and
swaps each with the index selected by the next draw's least nonnegative
remainder modulo i + 1. Success returns the resulting n-character string."""
    length = _cott_validate_abi(length, I64, path="$.length")
    draws = _cott_validate_abi(draws, CottList[I64], path="$.draws")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((length < 1) or (length > 128))):
        _expected_error = PasswordError_InvalidLength
        _expected_error_span = {"end_byte":1893,"end_column":70,"end_line":40,"start_byte":1828,"start_column":5,"start_line":40}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/random_password/generate_password.py", "45cd9803794dce2444234cf43a22951ec4ce137c2c9c7de7004550d36cb58949", "generate_password", expected_project_name="random-password-generator", expected_cott_symbol="curriculum.random_password.generate_password")
        _result = _implementation(length, draws)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.random_password.generate_password"
        if _error.span is None:
            _error.span = {"end_byte":1936,"end_column":1,"end_line":42,"start_byte":443,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.random_password.generate_password", phase="implementation-call", span={"end_byte":1936,"end_column":1,"end_line":42,"start_byte":443,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.random_password.generate_password", phase="implementation-call", span={"end_byte":1936,"end_column":1,"end_line":42,"start_byte":443,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, PasswordError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.random_password.generate_password", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PasswordError_InsufficientDraws,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.random_password.generate_password", phase="error", span={"end_byte":1936,"end_column":1,"end_line":42,"start_byte":443,"start_column":1,"start_line":16}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.random_password.generate_password", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        password = _result.value
        if not (((len(password) >= 1) and (len(password) <= 128))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.random_password.generate_password", clause="ensures:1", phase="ensures", span={"end_byte":1822,"end_column":77,"end_line":38,"start_byte":1750,"start_column":5,"start_line":38}, expected="true", actual="false")
    return _result

__all__ = ["PasswordError", "PasswordError_InsufficientDraws", "PasswordError_InvalidLength", "generate_password", "required_password_draws"]
