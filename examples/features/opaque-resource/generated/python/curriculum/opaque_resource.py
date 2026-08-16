from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.opaque_resource_types import HandleError, HandleError_InvalidHandle

def wrap_handle(raw_id: U64) -> Result[Opaque[Literal["client_session"]], HandleError]:
    """Wrap a raw connection id into a typed opaque handle with tag client_session."""
    raw_id = _cott_validate_abi(raw_id, U64, path="$.raw_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((raw_id == 0)):
        _expected_error = HandleError_InvalidHandle
        _expected_error_span = {"end_byte":304,"end_column":53,"end_line":11,"start_byte":256,"start_column":5,"start_line":11}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/opaque_resource/wrap_handle.py", "f4606a1503eb3cc76f35d797335952b60302bec390cccfe87de41e39807daf34", "wrap_handle", expected_project_name="opaque-resource", expected_cott_symbol="curriculum.opaque_resource.wrap_handle")
        _result = _implementation(raw_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.opaque_resource.wrap_handle"
        if _error.span is None:
            _error.span = {"end_byte":322,"end_column":1,"end_line":15,"start_byte":72,"start_column":1,"start_line":6}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.opaque_resource.wrap_handle", phase="implementation-call", span={"end_byte":322,"end_column":1,"end_line":15,"start_byte":72,"start_column":1,"start_line":6}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.opaque_resource.wrap_handle", phase="implementation-call", span={"end_byte":322,"end_column":1,"end_line":15,"start_byte":72,"start_column":1,"start_line":6}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Opaque[Literal["client_session"]], HandleError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.opaque_resource.wrap_handle", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.opaque_resource.wrap_handle", phase="error", span={"end_byte":322,"end_column":1,"end_line":15,"start_byte":72,"start_column":1,"start_line":6}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.opaque_resource.wrap_handle", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def extract_handle_id(handle: Opaque[Literal["client_session"]]) -> U64:
    """Extract the identifier from a client session opaque handle."""
    handle = _cott_validate_abi(handle, Opaque[Literal["client_session"]], path="$.handle")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/opaque_resource/extract_handle_id.py", "d8f9e7c36336795df4d681101942ed0de17a8a4e4e55001e2695d79f76d14461", "extract_handle_id", expected_project_name="opaque-resource", expected_cott_symbol="curriculum.opaque_resource.extract_handle_id")
        _result = _implementation(handle)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.opaque_resource.extract_handle_id"
        if _error.span is None:
            _error.span = {"end_byte":509,"end_column":1,"end_line":23,"start_byte":322,"start_column":1,"start_line":15}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.opaque_resource.extract_handle_id", phase="implementation-call", span={"end_byte":509,"end_column":1,"end_line":23,"start_byte":322,"start_column":1,"start_line":15}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.opaque_resource.extract_handle_id", phase="implementation-call", span={"end_byte":509,"end_column":1,"end_line":23,"start_byte":322,"start_column":1,"start_line":15}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    if not ((_result > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.opaque_resource.extract_handle_id", clause="ensures:1", phase="ensures", span={"end_byte":492,"end_column":23,"end_line":20,"start_byte":474,"start_column":5,"start_line":20}, expected="true", actual="false")
    return _result

__all__ = ["HandleError", "HandleError_InvalidHandle", "extract_handle_id", "wrap_handle"]
