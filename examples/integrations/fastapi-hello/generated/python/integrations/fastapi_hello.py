from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from integrations.fastapi_hello_types import HelloResponse, HttpRequest

def read_root(request: HttpRequest) -> HelloResponse:
    """Answer FastAPI's tutorial root route. `message` is the fixed greeting `Hello World`.
`method` is the HTTP method token of `request` exactly as received (for example `GET`),
neither normalized nor replaced by a default."""
    request = _cott_validate_abi(request, HttpRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/integrations/fastapi_hello/read_root.py", "2c6dc1bc7dbb7298d4396900a0f92746f1f651d0fa9f2bed1c6ec8c813f2e24c", "read_root", expected_project_name="fastapi-hello", expected_cott_symbol="integrations.fastapi_hello.read_root")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "integrations.fastapi_hello.read_root"
        if _error.span is None:
            _error.span = {"end_byte":651,"end_column":1,"end_line":23,"start_byte":128,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="integrations.fastapi_hello.read_root", phase="implementation-call", span={"end_byte":651,"end_column":1,"end_line":23,"start_byte":128,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="integrations.fastapi_hello.read_root", phase="implementation-call", span={"end_byte":651,"end_column":1,"end_line":23,"start_byte":128,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HelloResponse, path="$.return")
    if not (_cott_contract_condition((((_result).message == "Hello World")), "integrations.fastapi_hello.read_root", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="integrations.fastapi_hello.read_root", clause="ensures:1", phase="ensures", span={"end_byte":476,"end_column":44,"end_line":17,"start_byte":437,"start_column":5,"start_line":17}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, HelloResponse, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["HelloResponse", "HttpRequest", "read_root"]
