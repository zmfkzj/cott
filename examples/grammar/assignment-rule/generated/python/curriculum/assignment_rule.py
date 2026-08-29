from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.assignment_rule_types import AccessCodeError, AccessCodeError_EmptyCode, AccessCodeError_LegacyFormat, AccessCodeError_TooShort, BaseAccessCodeRule, StrictAccessCodeRule

def validate_access_code(code: str) -> Result[str, AccessCodeError]:
    """Trim an access code and require at least four characters."""
    code = _cott_validate_abi(code, str, path="$.code")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/assignment_rule/validate_access_code.py", "8b8a450163f78215f0ea405c487bc9f05ef2a5fe9d0762bbb70c39fe71283623", "validate_access_code", expected_project_name="assignment-rule", expected_cott_symbol="curriculum.assignment_rule.validate_access_code")
        _result = _implementation(code)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.assignment_rule.validate_access_code"
        if _error.span is None:
            _error.span = {"end_byte":691,"end_column":1,"end_line":31,"start_byte":510,"start_column":1,"start_line":25}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.assignment_rule.validate_access_code", phase="implementation-call", span={"end_byte":691,"end_column":1,"end_line":31,"start_byte":510,"start_column":1,"start_line":25}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.assignment_rule.validate_access_code", phase="implementation-call", span={"end_byte":691,"end_column":1,"end_line":31,"start_byte":510,"start_column":1,"start_line":25}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, AccessCodeError], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Result[str, AccessCodeError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["AccessCodeError", "AccessCodeError_EmptyCode", "AccessCodeError_LegacyFormat", "AccessCodeError_TooShort", "BaseAccessCodeRule", "StrictAccessCodeRule", "validate_access_code"]
