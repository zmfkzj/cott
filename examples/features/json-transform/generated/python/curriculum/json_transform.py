from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.json_transform_types import JsonChain, JsonChain_End, JsonChain_Link, JsonTransformError, JsonTransformError_MissingField, JsonTransformError_NotAnObject, StringField

async def wrap_scalar_json(key: str, value: str) -> JsonValue:
    """Wrap one string member into a JSON object."""
    key = _cott_validate_abi(key, str, path="$.key")
    value = _cott_validate_abi(value, str, path="$.value")
    if not (_cott_contract_condition(((len(key) > 0)), "curriculum.json_transform.wrap_scalar_json", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.json_transform.wrap_scalar_json", clause="requires:1", phase="requires", span={"end_byte":384,"end_column":25,"end_line":20,"start_byte":364,"start_column":5,"start_line":20}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_transform/wrap_scalar_json.py", "2531f8ef560180f03cb833a4a57e21ffbe0fc6921eac188559d1bf2298125331", "wrap_scalar_json", expected_project_name="json-transform", expected_cott_symbol="curriculum.json_transform.wrap_scalar_json")
        _result = await _implementation(key, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_transform.wrap_scalar_json"
        if _error.span is None:
            _error.span = {"end_byte":402,"end_column":1,"end_line":24,"start_byte":230,"start_column":1,"start_line":15}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_transform.wrap_scalar_json", phase="implementation-call", span={"end_byte":402,"end_column":1,"end_line":24,"start_byte":230,"start_column":1,"start_line":15}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_transform.wrap_scalar_json", phase="implementation-call", span={"end_byte":402,"end_column":1,"end_line":24,"start_byte":230,"start_column":1,"start_line":15}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, JsonValue, path="$.return")
    _result = _cott_wrap_async_protocol(_result, JsonValue, path="$.return", validator=_cott_validate_abi)
    return _result

def extract_string_field(payload: JsonValue, field: str) -> Result[StringField, JsonTransformError]:
    """Read the top-level member of a JSON object whose key equals `field` exactly
(no case folding, normalization or nested lookup). A payload that is not a
JSON object fails with `NotAnObject`, checked first. An object without that
member, or whose member is not a JSON string, fails with
`MissingField(field_name: field)`. Otherwise the result's `name` is `field`
and its `text` is the member's string value. Contract clauses cannot inspect
`JsonValue` structure, so both failures are declared without conditions."""
    payload = _cott_validate_abi(payload, JsonValue, path="$.payload")
    field = _cott_validate_abi(field, str, path="$.field")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_transform/extract_string_field.py", "d5ba77ecf38948c10ec1dff287da0ab50bfcdcaa0328d44361ff6b16591525f2", "extract_string_field", expected_project_name="json-transform", expected_cott_symbol="curriculum.json_transform.extract_string_field")
        _result = _implementation(payload, field)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_transform.extract_string_field"
        if _error.span is None:
            _error.span = {"end_byte":1293,"end_column":1,"end_line":43,"start_byte":402,"start_column":1,"start_line":24}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_transform.extract_string_field", phase="implementation-call", span={"end_byte":1293,"end_column":1,"end_line":43,"start_byte":402,"start_column":1,"start_line":24}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_transform.extract_string_field", phase="implementation-call", span={"end_byte":1293,"end_column":1,"end_line":43,"start_byte":402,"start_column":1,"start_line":24}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[StringField, JsonTransformError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.json_transform.extract_string_field", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (JsonTransformError_NotAnObject, JsonTransformError_MissingField,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.json_transform.extract_string_field", phase="error", span={"end_byte":1293,"end_column":1,"end_line":43,"start_byte":402,"start_column":1,"start_line":24}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.json_transform.extract_string_field", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.json_transform.extract_string_field", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is JsonTransformError_NotAnObject:
        _cott_contract_condition(True, "curriculum.json_transform.extract_string_field", "error:3")
    if type(_result) is Err and type(_result.error) is JsonTransformError_MissingField:
        _cott_contract_condition(True, "curriculum.json_transform.extract_string_field", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            found = _cott_match_value.value
            return (_cott_contract_condition((((found).name == field)), "curriculum.json_transform.extract_string_field", "ensures:1"))
        _cott_contract_condition((False), "curriculum.json_transform.extract_string_field", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.json_transform.extract_string_field", clause="ensures:1", phase="ensures", span={"end_byte":1112,"end_column":52,"end_line":35,"start_byte":1065,"start_column":5,"start_line":35}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is JsonTransformError_MissingField and True:
            name = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((name == field)), "curriculum.json_transform.extract_string_field", "ensures:2"))
        _cott_contract_condition((False), "curriculum.json_transform.extract_string_field", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.json_transform.extract_string_field", clause="ensures:2", phase="ensures", span={"end_byte":1191,"end_column":79,"end_line":36,"start_byte":1117,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[StringField, JsonTransformError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["JsonChain", "JsonChain_End", "JsonChain_Link", "JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject", "StringField", "extract_string_field", "wrap_scalar_json"]
