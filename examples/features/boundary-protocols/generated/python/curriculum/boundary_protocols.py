from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.boundary_protocols_types import ConnectionId, HandleBundle, TextBuffer

def wrap_handle(raw_id: ConnectionId) -> HandleBundle:
    """Wrap a connection ID in a client-session opaque handle.

The handle's opaque payload is the U64 value carried by `raw_id`, not the `ConnectionId`
wrapper and not a target object derived from it. `HandleBundle.raw_id` repeats the same ID
as plain data."""
    raw_id = _cott_validate_abi(raw_id, ConnectionId, path="$.raw_id")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/wrap_handle.py", "1ac6e71ff6b181be7c77b49203d47a13b86ccfeeda29bcc10b80d464f24b8ab5", "wrap_handle", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.wrap_handle")
        _result = _implementation(raw_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.wrap_handle"
        if _error.span is None:
            _error.span = {"end_byte":594,"end_column":1,"end_line":25,"start_byte":194,"start_column":1,"start_line":12}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.wrap_handle", phase="implementation-call", span={"end_byte":594,"end_column":1,"end_line":25,"start_byte":194,"start_column":1,"start_line":12}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.wrap_handle", phase="implementation-call", span={"end_byte":594,"end_column":1,"end_line":25,"start_byte":194,"start_column":1,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HandleBundle, path="$.return")
    if not (_cott_contract_condition(((((_result).raw_id).value == (raw_id).value)), "curriculum.boundary_protocols.wrap_handle", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.boundary_protocols.wrap_handle", clause="ensures:1", phase="ensures", span={"end_byte":576,"end_column":36,"end_line":21,"start_byte":545,"start_column":5,"start_line":21}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, HandleBundle, path="$.return", validator=_cott_validate_abi)
    return _result

def extract_handle_id(bundle: HandleBundle) -> ConnectionId:
    """Explicitly adapt a client-session opaque handle back to its connection ID by reading the
handle's opaque payload. `bundle` comes from `wrap_handle`; a handle carrying any other
payload is outside this contract."""
    bundle = _cott_validate_abi(bundle, HandleBundle, path="$.bundle")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/extract_handle_id.py", "0c65a881d7d9113ac1be045893320671818e084f355f4cf231d1a35603aab0c4", "extract_handle_id", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.extract_handle_id")
        _result = _implementation(bundle)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.extract_handle_id"
        if _error.span is None:
            _error.span = {"end_byte":914,"end_column":1,"end_line":34,"start_byte":594,"start_column":1,"start_line":25}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.extract_handle_id", phase="implementation-call", span={"end_byte":914,"end_column":1,"end_line":34,"start_byte":594,"start_column":1,"start_line":25}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.extract_handle_id", phase="implementation-call", span={"end_byte":914,"end_column":1,"end_line":34,"start_byte":594,"start_column":1,"start_line":25}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, ConnectionId, path="$.return")
    _result = _cott_wrap_async_protocol(_result, ConnectionId, path="$.return", validator=_cott_validate_abi)
    return _result

def adapt_unknown(value: Any) -> object:
    """Retype an unconstrained `Any` value as `Unknown`, so that callers must narrow it explicitly
before use."""
    value = _cott_validate_abi(value, Any, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/adapt_unknown.py", "f8cd3a661e133fb532fd2ad3acdb0ceb651cd558bdf927a9ebbf00053b4b4178", "adapt_unknown", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.adapt_unknown")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.adapt_unknown"
        if _error.span is None:
            _error.span = {"end_byte":1104,"end_column":1,"end_line":42,"start_byte":914,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.adapt_unknown", phase="implementation-call", span={"end_byte":1104,"end_column":1,"end_line":42,"start_byte":914,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.adapt_unknown", phase="implementation-call", span={"end_byte":1104,"end_column":1,"end_line":42,"start_byte":914,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, object, path="$.return")
    _result = _cott_wrap_async_protocol(_result, object, path="$.return", validator=_cott_validate_abi)
    return _result

def iter_lines(buffer: TextBuffer) -> Iterator[str]:
    """Iterate the lines of a caller-owned text buffer. A line ends at LF, CR or CRLF, and the
terminator is not part of the yielded line. A final line without a terminator is still
yielded; an empty buffer yields nothing."""
    buffer = _cott_validate_abi(buffer, TextBuffer, path="$.buffer")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/iter_lines.py", "e1a2b47d12dc69e2f82e0fcd9422472f86881a895b4cedf220691a11c137b9f2", "iter_lines", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.iter_lines")
        _result = _implementation(buffer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.iter_lines"
        if _error.span is None:
            _error.span = {"end_byte":1421,"end_column":1,"end_line":51,"start_byte":1104,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.iter_lines", phase="implementation-call", span={"end_byte":1421,"end_column":1,"end_line":51,"start_byte":1104,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.iter_lines", phase="implementation-call", span={"end_byte":1421,"end_column":1,"end_line":51,"start_byte":1104,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Iterator[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Iterator[str], path="$.return", validator=_cott_validate_abi)
    return _result

def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]:
    """Re-yield the values of an iterator from a generator. Values sent into the generator are
ignored; its return value is the number of values it yielded."""
    values = _cott_validate_abi(values, Iterator[Any], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/echo_values.py", "fd44eae6f28832e3bce49f3d941ebf8d3734a3de36b65ba311d91fe9120b5b0e", "echo_values", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.echo_values")
        _result = _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.echo_values"
        if _error.span is None:
            _error.span = {"end_byte":1687,"end_column":1,"end_line":59,"start_byte":1421,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.echo_values", phase="implementation-call", span={"end_byte":1687,"end_column":1,"end_line":59,"start_byte":1421,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.echo_values", phase="implementation-call", span={"end_byte":1687,"end_column":1,"end_line":59,"start_byte":1421,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Generator[Any, object, U64], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Generator[Any, object, U64], path="$.return", validator=_cott_validate_abi)
    return _result

async def async_lines(values: AsyncIterator[str]) -> AsyncIterator[str]:
    """Pass an async line iterator across the boundary."""
    values = _cott_validate_abi(values, AsyncIterator[str], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/async_lines.py", "6938b95bbc831cd3fd0c007505b384472624af99d3143e191750d3e1cbf80bcf", "async_lines", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.async_lines")
        _result = await _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.async_lines"
        if _error.span is None:
            _error.span = {"end_byte":1849,"end_column":1,"end_line":66,"start_byte":1687,"start_column":1,"start_line":59}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.async_lines", phase="implementation-call", span={"end_byte":1849,"end_column":1,"end_line":66,"start_byte":1687,"start_column":1,"start_line":59}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.async_lines", phase="implementation-call", span={"end_byte":1849,"end_column":1,"end_line":66,"start_byte":1687,"start_column":1,"start_line":59}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, AsyncIterator[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, AsyncIterator[str], path="$.return", validator=_cott_validate_abi)
    return _result

async def echo_async(values: AsyncGenerator[Any, object]) -> AsyncGenerator[Any, object]:
    """Pass an async generator across the boundary."""
    values = _cott_validate_abi(values, AsyncGenerator[Any, object], path="$.values")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/echo_async.py", "6f7283139a8889bb77f745c3d294f1da65559046438372f5a5ff871650b12f32", "echo_async", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.echo_async")
        _result = await _implementation(values)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.boundary_protocols.echo_async"
        if _error.span is None:
            _error.span = {"end_byte":2026,"end_column":1,"end_line":73,"start_byte":1849,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.boundary_protocols.echo_async", phase="implementation-call", span={"end_byte":2026,"end_column":1,"end_line":73,"start_byte":1849,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.boundary_protocols.echo_async", phase="implementation-call", span={"end_byte":2026,"end_column":1,"end_line":73,"start_byte":1849,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, AsyncGenerator[Any, object], path="$.return")
    _result = _cott_wrap_async_protocol(_result, AsyncGenerator[Any, object], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ConnectionId", "HandleBundle", "TextBuffer", "adapt_unknown", "async_lines", "echo_async", "echo_values", "extract_handle_id", "iter_lines", "wrap_handle"]
