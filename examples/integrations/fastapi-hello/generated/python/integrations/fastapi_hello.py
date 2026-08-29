from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from integrations.fastapi_hello_types import HelloResponse, HttpRequest

def read_root(request: HttpRequest) -> HelloResponse:
    """Return FastAPI's official `Hello World` message and the injected request method."""
    request = _cott_validate_abi(request, HttpRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/integrations/fastapi_hello/read_root.py", "c0e1c9772f66d60a5bb9ec4e8ae3f8d0ce776ec97d0604e5f9d0af2861e97721", "read_root", expected_project_name="fastapi-hello", expected_cott_symbol="integrations.fastapi_hello.read_root")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "integrations.fastapi_hello.read_root"
        if _error.span is None:
            _error.span = {"end_byte":347,"end_column":1,"end_line":18,"start_byte":128,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="integrations.fastapi_hello.read_root", phase="implementation-call", span={"end_byte":347,"end_column":1,"end_line":18,"start_byte":128,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="integrations.fastapi_hello.read_root", phase="implementation-call", span={"end_byte":347,"end_column":1,"end_line":18,"start_byte":128,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HelloResponse, path="$.return")
    if not (((_result).message == "Hello World")):
        raise CottContractViolation("ensures clause failed", symbol="integrations.fastapi_hello.read_root", clause="ensures:1", phase="ensures", span={"end_byte":330,"end_column":44,"end_line":15,"start_byte":291,"start_column":5,"start_line":15}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, HelloResponse, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["HelloResponse", "HttpRequest", "read_root"]
