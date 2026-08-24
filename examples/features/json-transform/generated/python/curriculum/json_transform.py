from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.json_transform_types import JsonTransformError, JsonTransformError_MissingField, JsonTransformError_NotAnObject

def wrap_scalar_json(key: str, value: str) -> JsonValue:
    """Wrap a string key-value pair into a structured JsonValue object."""
    key = _cott_validate_abi(key, str, path="$.key")
    value = _cott_validate_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_transform/wrap_scalar_json.py", "e072a720cc970cd8cb876d0579af6ea6b76e2db44903c885884f336847bccc0a", "wrap_scalar_json", expected_project_name="json-transform", expected_cott_symbol="curriculum.json_transform.wrap_scalar_json")
        _result = _implementation(key, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_transform.wrap_scalar_json"
        if _error.span is None:
            _error.span = {"end_byte":272,"end_column":1,"end_line":14,"start_byte":110,"start_column":1,"start_line":7}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_transform.wrap_scalar_json", phase="implementation-call", span={"end_byte":272,"end_column":1,"end_line":14,"start_byte":110,"start_column":1,"start_line":7}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_transform.wrap_scalar_json", phase="implementation-call", span={"end_byte":272,"end_column":1,"end_line":14,"start_byte":110,"start_column":1,"start_line":7}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, JsonValue, path="$.return")
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
            _error.span = {"end_byte":461,"end_column":1,"end_line":20,"start_byte":272,"start_column":1,"start_line":14}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_transform.extract_string_field", phase="implementation-call", span={"end_byte":461,"end_column":1,"end_line":20,"start_byte":272,"start_column":1,"start_line":14}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_transform.extract_string_field", phase="implementation-call", span={"end_byte":461,"end_column":1,"end_line":20,"start_byte":272,"start_column":1,"start_line":14}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, JsonTransformError], path="$.return")
    return _result

__all__ = ["JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject", "extract_string_field", "wrap_scalar_json"]
