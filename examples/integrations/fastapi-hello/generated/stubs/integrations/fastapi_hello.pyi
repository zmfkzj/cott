from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from integrations.fastapi_hello_types import HelloResponse as HelloResponse, HttpRequest as HttpRequest
"""Return FastAPI's official `Hello World` message and the injected request method."""
def read_root(request: HttpRequest) -> HelloResponse: ...

__all__ = ["HelloResponse", "HttpRequest", "read_root"]
