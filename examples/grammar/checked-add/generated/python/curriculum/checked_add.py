from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

def checked_add(left: I32, right: I32) -> I64:
    """Compute the exact mathematical sum of two signed 32-bit integers as a signed 64-bit integer.
Each input is in the inclusive range -2,147,483,648 through 2,147,483,647, so the result is in the inclusive range -4,294,967,296 through 4,294,967,294 and cannot overflow I64.
The function performs no additional validation, raises no declared errors, and deterministically returns left plus right."""
    left = _cott_validate_abi(left, I32, path="$.left")
    right = _cott_validate_abi(right, I32, path="$.right")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/checked_add/checked_add.py", "8625a6dddae67245780eb19ebe6960f6f35d496c692e1ad42b872526c8408581", "checked_add", expected_project_name="checked-add", expected_cott_symbol="curriculum.checked_add.checked_add")
        _result = _implementation(left, right)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.checked_add.checked_add"
        if _error.span is None:
            _error.span = {"end_byte":569,"end_column":1,"end_line":12,"start_byte":31,"start_column":1,"start_line":3}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.checked_add.checked_add", phase="implementation-call", span={"end_byte":569,"end_column":1,"end_line":12,"start_byte":31,"start_column":1,"start_line":3}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.checked_add.checked_add", phase="implementation-call", span={"end_byte":569,"end_column":1,"end_line":12,"start_byte":31,"start_column":1,"start_line":3}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, I64, path="$.return")
    if not ((_result >= (-4294967296))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.checked_add.checked_add", clause="ensures:1", phase="ensures", span={"end_byte":535,"end_column":34,"end_line":10,"start_byte":506,"start_column":5,"start_line":10}, expected="true", actual="false")
    if not ((_result <= 4294967294)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.checked_add.checked_add", clause="ensures:2", phase="ensures", span={"end_byte":568,"end_column":33,"end_line":11,"start_byte":540,"start_column":5,"start_line":11}, expected="true", actual="false")
    return _result

__all__ = ["checked_add"]
