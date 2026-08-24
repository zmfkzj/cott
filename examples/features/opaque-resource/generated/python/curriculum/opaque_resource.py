from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.opaque_resource_types import HandleBundle, HandleError, HandleError_InvalidHandle, TextBuffer

def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]:
    """Wrap a nonzero connection ID in a bundle containing a client-session handle."""
    raw_id = _cott_validate_abi(raw_id, U64, path="$.raw_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((raw_id == 0)):
        _expected_error = HandleError_InvalidHandle
        _expected_error_span = {"end_byte":377,"end_column":53,"end_line":16,"start_byte":329,"start_column":5,"start_line":16}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/opaque_resource/wrap_handle.py", "f6d87fe4a862acd9454c4d4ad066295fc4e22b32c357e3d22b6c3d594f6a68c0", "wrap_handle", expected_project_name="opaque-resource", expected_cott_symbol="curriculum.opaque_resource.wrap_handle")
        _result = _implementation(raw_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.opaque_resource.wrap_handle"
        if _error.span is None:
            _error.span = {"end_byte":395,"end_column":1,"end_line":20,"start_byte":157,"start_column":1,"start_line":11}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.opaque_resource.wrap_handle", phase="implementation-call", span={"end_byte":395,"end_column":1,"end_line":20,"start_byte":157,"start_column":1,"start_line":11}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.opaque_resource.wrap_handle", phase="implementation-call", span={"end_byte":395,"end_column":1,"end_line":20,"start_byte":157,"start_column":1,"start_line":11}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HandleBundle, HandleError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.opaque_resource.wrap_handle", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.opaque_resource.wrap_handle", phase="error", span={"end_byte":395,"end_column":1,"end_line":20,"start_byte":157,"start_column":1,"start_line":11}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.opaque_resource.wrap_handle", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def extract_handle_id(bundle: HandleBundle) -> U64:
    """Extract the client-session handle ID from a bundle returned by wrap_handle."""
    bundle = _cott_validate_abi(bundle, HandleBundle, path="$.bundle")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/opaque_resource/extract_handle_id.py", "578b4680ac0a09e9fa1351fbbedd769acb00a2110510e3cee49e6c44d95a900e", "extract_handle_id", expected_project_name="opaque-resource", expected_cott_symbol="curriculum.opaque_resource.extract_handle_id")
        _result = _implementation(bundle)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.opaque_resource.extract_handle_id"
        if _error.span is None:
            _error.span = {"end_byte":587,"end_column":1,"end_line":29,"start_byte":395,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.opaque_resource.extract_handle_id", phase="implementation-call", span={"end_byte":587,"end_column":1,"end_line":29,"start_byte":395,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.opaque_resource.extract_handle_id", phase="implementation-call", span={"end_byte":587,"end_column":1,"end_line":29,"start_byte":395,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    if not ((_result > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.opaque_resource.extract_handle_id", clause="ensures:1", phase="ensures", span={"end_byte":569,"end_column":23,"end_line":25,"start_byte":551,"start_column":5,"start_line":25}, expected="true", actual="false")
    return _result

def iter_lines(buffer: TextBuffer) -> Iterator[str]:
    """Lazily yield the buffer's lines without their trailing line endings."""
    buffer = _cott_validate_abi(buffer, TextBuffer, path="$.buffer")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/opaque_resource/iter_lines.py", "0e9812ffc66efa513316737acd909e95e85cc9508545627275f3c1f62d7e389c", "iter_lines", expected_project_name="opaque-resource", expected_cott_symbol="curriculum.opaque_resource.iter_lines")
        _result = _implementation(buffer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.opaque_resource.iter_lines"
        if _error.span is None:
            _error.span = {"end_byte":749,"end_column":1,"end_line":36,"start_byte":587,"start_column":1,"start_line":29}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.opaque_resource.iter_lines", phase="implementation-call", span={"end_byte":749,"end_column":1,"end_line":36,"start_byte":587,"start_column":1,"start_line":29}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.opaque_resource.iter_lines", phase="implementation-call", span={"end_byte":749,"end_column":1,"end_line":36,"start_byte":587,"start_column":1,"start_line":29}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Iterator[str], path="$.return")
    return _result

def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]:
    """Yield each input value, ignore sent values, and return the yielded count."""
    values = _cott_validate_abi(values, Iterator[Any], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/opaque_resource/echo_values.py", "292acbb71eca91b9f16e9cb9de89797f171bccf6a7367b97984a64b83945df98", "echo_values", expected_project_name="opaque-resource", expected_cott_symbol="curriculum.opaque_resource.echo_values")
        _result = _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.opaque_resource.echo_values"
        if _error.span is None:
            _error.span = {"end_byte":934,"end_column":1,"end_line":42,"start_byte":749,"start_column":1,"start_line":36}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.opaque_resource.echo_values", phase="implementation-call", span={"end_byte":934,"end_column":1,"end_line":42,"start_byte":749,"start_column":1,"start_line":36}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.opaque_resource.echo_values", phase="implementation-call", span={"end_byte":934,"end_column":1,"end_line":42,"start_byte":749,"start_column":1,"start_line":36}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Generator[Any, object, U64], path="$.return")
    return _result

__all__ = ["HandleBundle", "HandleError", "HandleError_InvalidHandle", "TextBuffer", "echo_values", "extract_handle_id", "iter_lines", "wrap_handle"]
