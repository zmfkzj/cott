from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from integrations.fastapi_hello_types import HelloResponse

def read_root() -> HelloResponse:
    """Return the {HelloResponse} from FastAPI's official First Steps GET `/` example.
The response message is always exactly `Hello World`."""
    try:
        _implementation = _cott_load("_cott_impl/integrations/fastapi_hello/read_root.py", "b7223859b84b51eaee0515e7ad3617368a2056b4de23ca7d111cc59ce9394b9c", "read_root", expected_project_name="fastapi-hello", expected_cott_symbol="integrations.fastapi_hello.read_root")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "integrations.fastapi_hello.read_root"
        if _error.span is None:
            _error.span = {"end_byte":341,"end_column":1,"end_line":16,"start_byte":85,"start_column":1,"start_line":7}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="integrations.fastapi_hello.read_root", phase="implementation-call", span={"end_byte":341,"end_column":1,"end_line":16,"start_byte":85,"start_column":1,"start_line":7}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="integrations.fastapi_hello.read_root", phase="implementation-call", span={"end_byte":341,"end_column":1,"end_line":16,"start_byte":85,"start_column":1,"start_line":7}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HelloResponse, path="$.return")
    if not (((_result).message == "Hello World")):
        raise CottContractViolation("ensures clause failed", symbol="integrations.fastapi_hello.read_root", clause="ensures:1", phase="ensures", span={"end_byte":324,"end_column":44,"end_line":13,"start_byte":285,"start_column":5,"start_line":13}, expected="true", actual="false")
    return _result

__all__ = ["HelloResponse", "read_root"]
