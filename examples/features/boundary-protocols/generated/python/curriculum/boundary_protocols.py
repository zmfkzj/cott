from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.boundary_protocols_types import HandleBundle, HandleError, HandleError_InvalidHandle, TextBuffer

def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]:
    """Wrap a nonzero connection ID in a client-session opaque handle."""
    raw_id = _cott_validate_abi(raw_id, U64, path="$.raw_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((raw_id == 0)):
        _expected_error = HandleError_InvalidHandle
        _expected_error_span = {"end_byte":463,"end_column":53,"end_line":19,"start_byte":415,"start_column":5,"start_line":19}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/wrap_handle.py", "b0256a4b130d02c23b0b20f708831ec4822bc0da1b87afbbf742a2e6f4510b05", "wrap_handle", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.wrap_handle")
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
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            bundle = _cott_match_value.value
            return ((((bundle).raw_id == raw_id) and ((bundle).raw_id > 0)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.boundary_protocols.wrap_handle", clause="ensures:1", phase="ensures", span={"end_byte":409,"end_column":79,"end_line":17,"start_byte":335,"start_column":5,"start_line":17}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HandleBundle, HandleError], path="$.return", validator=_cott_validate_abi)
    return _result

def extract_handle_id(bundle: HandleBundle) -> U64:
    """Explicitly adapt a client-session opaque handle to its Python ID."""
    bundle = _cott_validate_abi(bundle, HandleBundle, path="$.bundle")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/extract_handle_id.py", "15ee436d80ae7b210c709d632b0b32c5149535f4bf6b712ca9007e077b1ac294", "extract_handle_id", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.extract_handle_id")
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
    if not ((_result > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.boundary_protocols.extract_handle_id", clause="ensures:1", phase="ensures", span={"end_byte":645,"end_column":23,"end_line":28,"start_byte":627,"start_column":5,"start_line":28}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=_cott_validate_abi)
    return _result

def adapt_unknown(value: Any) -> object:
    """Deliberately adapt an unconstrained value to an explicitly narrowed boundary value."""
    value = _cott_validate_abi(value, Any, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/adapt_unknown.py", "f66f20ebacad682b1a537e45facf398893520c8c3dfde2a260d7ccb5b27daf49", "adapt_unknown", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.adapt_unknown")
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
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/iter_lines.py", "28df24e128403596de810439057c10a166dcf04df22adc8605f1948911105cc6", "iter_lines", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.iter_lines")
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
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/echo_values.py", "292acbb71eca91b9f16e9cb9de89797f171bccf6a7367b97984a64b83945df98", "echo_values", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.echo_values")
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
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/async_lines.py", "4362cf9bd2b06dc09a460e23b558ae4ee23eb4654a56e59466fab58e05b67e68", "async_lines", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.async_lines")
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
        _implementation = _cott_load("_cott_impl/curriculum/boundary_protocols/echo_async.py", "dfda4da00567053b60962e3490fe43836695fa831392cb792105e043b848819e", "echo_async", expected_project_name="boundary-protocols", expected_cott_symbol="curriculum.boundary_protocols.echo_async")
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
