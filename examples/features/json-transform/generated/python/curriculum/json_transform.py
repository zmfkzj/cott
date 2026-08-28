from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.json_transform_types import JsonChain, JsonChain_End, JsonChain_Link, JsonTransformError, JsonTransformError_MissingField, JsonTransformError_NotAnObject

async def wrap_scalar_json(key: str, value: str) -> JsonValue:
    """Wrap a string key-value pair into a structured JsonValue object."""
    key = _cott_validate_abi(key, str, path="$.key")
    value = _cott_validate_abi(value, str, path="$.value")
    if not ((len(key) > 0)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.json_transform.wrap_scalar_json", clause="requires:1", phase="requires", span={"end_byte":357,"end_column":25,"end_line":16,"start_byte":337,"start_column":5,"start_line":16}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_transform/wrap_scalar_json.py", "cc780ae75bdfa330553729f1da036b1c28229fea17b8737941699234719b9d6d", "wrap_scalar_json", expected_project_name="json-transform", expected_cott_symbol="curriculum.json_transform.wrap_scalar_json")
        _result = await _implementation(key, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_transform.wrap_scalar_json"
        if _error.span is None:
            _error.span = {"end_byte":375,"end_column":1,"end_line":20,"start_byte":181,"start_column":1,"start_line":11}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_transform.wrap_scalar_json", phase="implementation-call", span={"end_byte":375,"end_column":1,"end_line":20,"start_byte":181,"start_column":1,"start_line":11}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_transform.wrap_scalar_json", phase="implementation-call", span={"end_byte":375,"end_column":1,"end_line":20,"start_byte":181,"start_column":1,"start_line":11}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, JsonValue, path="$.return")
    _result = _cott_wrap_async_protocol(_result, JsonValue, path="$.return", validator=_cott_validate_abi)
    return _result

def extract_string_field(payload: JsonValue, field: str) -> Result[str, JsonTransformError]:
    """Extract a string field value from a JSON object payload."""
    payload = _cott_validate_abi(payload, JsonValue, path="$.payload")
    field = _cott_validate_abi(field, str, path="$.field")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_transform/extract_string_field.py", "5166254c4d3ba44dd546175722f33cf10cc8544a187c335245eaf5cdf852d95d", "extract_string_field", expected_project_name="json-transform", expected_cott_symbol="curriculum.json_transform.extract_string_field")
        _result = _implementation(payload, field)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_transform.extract_string_field"
        if _error.span is None:
            _error.span = {"end_byte":564,"end_column":1,"end_line":26,"start_byte":375,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_transform.extract_string_field", phase="implementation-call", span={"end_byte":564,"end_column":1,"end_line":26,"start_byte":375,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_transform.extract_string_field", phase="implementation-call", span={"end_byte":564,"end_column":1,"end_line":26,"start_byte":375,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, JsonTransformError], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Result[str, JsonTransformError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["JsonChain", "JsonChain_End", "JsonChain_Link", "JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject", "extract_string_field", "wrap_scalar_json"]
