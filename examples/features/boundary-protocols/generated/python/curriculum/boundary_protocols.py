from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.boundary_protocols_types import HandleBundle, HandleError, HandleError_InvalidHandle, TextBuffer

def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]:
    """Wrap a nonzero connection ID in a client-session opaque handle."""
    raw_id = _cott_validate_abi(raw_id, U64, path="$.raw_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((raw_id == 0)), "curriculum.boundary_protocols.wrap_handle", "error:2:condition")):
        _expected_error = HandleError_InvalidHandle
        _expected_error_span = {"end_byte":463,"end_column":53,"end_line":19,"start_byte":415,"start_column":5,"start_line":19}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/wrap_handle.py", "b2e20037b9eac6ad02803bfc760482df4c9e41b86064c2b99a01fd1da4286dd9", "wrap_handle", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.wrap_handle")
        _result = _implementation(raw_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.wrap_handle"
        if _error.span is None:
            _error.span = {"end_byte":481,"end_column":1,"end_line":23,"start_byte":176,"start_column":1,"start_line":12}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.wrap_handle", phase="implementation-call", span={"end_byte":481,"end_column":1,"end_line":23,"start_byte":176,"start_column":1,"start_line":12}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.wrap_handle", phase="implementation-call", span={"end_byte":481,"end_column":1,"end_line":23,"start_byte":176,"start_column":1,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HandleBundle, HandleError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.boundary_protocols.wrap_handle", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.boundary_protocols.wrap_handle", phase="error", span={"end_byte":481,"end_column":1,"end_line":23,"start_byte":176,"start_column":1,"start_line":12}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.boundary_protocols.wrap_handle", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.boundary_protocols.wrap_handle", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            bundle = _cott_match_value.value
            return (_cott_contract_condition(((((bundle).raw_id == raw_id) and ((bundle).raw_id > 0))), "curriculum.boundary_protocols.wrap_handle", "ensures:1"))
        _cott_contract_condition((False), "curriculum.boundary_protocols.wrap_handle", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.boundary_protocols.wrap_handle", clause="ensures:1", phase="ensures", span={"end_byte":409,"end_column":79,"end_line":17,"start_byte":335,"start_column":5,"start_line":17}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HandleBundle, HandleError], path="$.return", validator=_cott_validate_abi)
    return _result

def extract_handle_id(bundle: HandleBundle) -> U64:
    """Explicitly adapt a client-session opaque handle to its Python ID."""
    bundle = _cott_validate_abi(bundle, HandleBundle, path="$.bundle")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/extract_handle_id.py", "87b167df10d73fffa5279541354f2fe01dbeb3f36713d173f0ec19d3c263bc7c", "extract_handle_id", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.extract_handle_id")
        _result = _implementation(bundle)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.extract_handle_id"
        if _error.span is None:
            _error.span = {"end_byte":663,"end_column":1,"end_line":32,"start_byte":481,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.extract_handle_id", phase="implementation-call", span={"end_byte":663,"end_column":1,"end_line":32,"start_byte":481,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.extract_handle_id", phase="implementation-call", span={"end_byte":663,"end_column":1,"end_line":32,"start_byte":481,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    if not (_cott_contract_condition(((_result > 0)), "curriculum.boundary_protocols.extract_handle_id", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.boundary_protocols.extract_handle_id", clause="ensures:1", phase="ensures", span={"end_byte":645,"end_column":23,"end_line":28,"start_byte":627,"start_column":5,"start_line":28}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=_cott_validate_abi)
    return _result

def adapt_unknown(value: Any) -> object:
    """Deliberately adapt an unconstrained value to an explicitly narrowed boundary value."""
    value = _cott_validate_abi(value, Any, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/adapt_unknown.py", "f8cd3a661e133fb532fd2ad3acdb0ceb651cd558bdf927a9ebbf00053b4b4178", "adapt_unknown", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.adapt_unknown")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.adapt_unknown"
        if _error.span is None:
            _error.span = {"end_byte":829,"end_column":1,"end_line":39,"start_byte":663,"start_column":1,"start_line":32}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.adapt_unknown", phase="implementation-call", span={"end_byte":829,"end_column":1,"end_line":39,"start_byte":663,"start_column":1,"start_line":32}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.adapt_unknown", phase="implementation-call", span={"end_byte":829,"end_column":1,"end_line":39,"start_byte":663,"start_column":1,"start_line":32}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, object, path="$.return")
    _result = _cott_wrap_async_protocol(_result, object, path="$.return", validator=_cott_validate_abi)
    return _result

def iter_lines(buffer: TextBuffer) -> Iterator[str]:
    """Lazily yield buffer lines without trailing line endings."""
    buffer = _cott_validate_abi(buffer, TextBuffer, path="$.buffer")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/iter_lines.py", "185f2ff6951ec19b4565616c5368025fb79c99ea3924450b30ce2f52efaaa586", "iter_lines", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.iter_lines")
        _result = _implementation(buffer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.iter_lines"
        if _error.span is None:
            _error.span = {"end_byte":979,"end_column":1,"end_line":46,"start_byte":829,"start_column":1,"start_line":39}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.iter_lines", phase="implementation-call", span={"end_byte":979,"end_column":1,"end_line":46,"start_byte":829,"start_column":1,"start_line":39}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.iter_lines", phase="implementation-call", span={"end_byte":979,"end_column":1,"end_line":46,"start_byte":829,"start_column":1,"start_line":39}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Iterator[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Iterator[str], path="$.return", validator=_cott_validate_abi)
    return _result

def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]:
    """Yield each value, discard sent unknown values, and return the yield count."""
    values = _cott_validate_abi(values, Iterator[Any], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/echo_values.py", "fd44eae6f28832e3bce49f3d941ebf8d3734a3de36b65ba311d91fe9120b5b0e", "echo_values", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.echo_values")
        _result = _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.echo_values"
        if _error.span is None:
            _error.span = {"end_byte":1166,"end_column":1,"end_line":53,"start_byte":979,"start_column":1,"start_line":46}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.echo_values", phase="implementation-call", span={"end_byte":1166,"end_column":1,"end_line":53,"start_byte":979,"start_column":1,"start_line":46}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.echo_values", phase="implementation-call", span={"end_byte":1166,"end_column":1,"end_line":53,"start_byte":979,"start_column":1,"start_line":46}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Generator[Any, object, U64], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Generator[Any, object, U64], path="$.return", validator=_cott_validate_abi)
    return _result

async def async_lines(values: AsyncIterator[str]) -> AsyncIterator[str]:
    """Return the supplied async iterator."""
    values = _cott_validate_abi(values, AsyncIterator[str], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/async_lines.py", "6938b95bbc831cd3fd0c007505b384472624af99d3143e191750d3e1cbf80bcf", "async_lines", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.async_lines")
        _result = await _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.async_lines"
        if _error.span is None:
            _error.span = {"end_byte":1315,"end_column":1,"end_line":60,"start_byte":1166,"start_column":1,"start_line":53}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.async_lines", phase="implementation-call", span={"end_byte":1315,"end_column":1,"end_line":60,"start_byte":1166,"start_column":1,"start_line":53}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.async_lines", phase="implementation-call", span={"end_byte":1315,"end_column":1,"end_line":60,"start_byte":1166,"start_column":1,"start_line":53}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, AsyncIterator[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, AsyncIterator[str], path="$.return", validator=_cott_validate_abi)
    return _result

async def echo_async(values: AsyncGenerator[Any, object]) -> AsyncGenerator[Any, object]:
    """Return the supplied async generator."""
    values = _cott_validate_abi(values, AsyncGenerator[Any, object], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/echo_async.py", "6f7283139a8889bb77f745c3d294f1da65559046438372f5a5ff871650b12f32", "echo_async", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.echo_async")
        _result = await _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.echo_async"
        if _error.span is None:
            _error.span = {"end_byte":1483,"end_column":1,"end_line":66,"start_byte":1315,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.echo_async", phase="implementation-call", span={"end_byte":1483,"end_column":1,"end_line":66,"start_byte":1315,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.echo_async", phase="implementation-call", span={"end_byte":1483,"end_column":1,"end_line":66,"start_byte":1315,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, AsyncGenerator[Any, object], path="$.return")
    _result = _cott_wrap_async_protocol(_result, AsyncGenerator[Any, object], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["HandleBundle", "HandleError", "HandleError_InvalidHandle", "TextBuffer", "adapt_unknown", "async_lines", "echo_async", "echo_values", "extract_handle_id", "iter_lines", "wrap_handle"]
