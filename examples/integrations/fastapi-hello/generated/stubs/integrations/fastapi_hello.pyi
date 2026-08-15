from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from integrations.fastapi_hello_types import HelloResponse as HelloResponse
"""Return the {HelloResponse} from FastAPI's official First Steps GET `/` example.
The response message is always exactly `Hello World`."""
def read_root() -> HelloResponse: ...

__all__ = ["HelloResponse", "read_root"]
