from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.opaque_resource_types import HandleError as HandleError, HandleError_InvalidHandle as HandleError_InvalidHandle
"""Wrap a raw connection id into a typed opaque handle with tag client_session."""
def wrap_handle(raw_id: U64) -> Result[Opaque[Literal["client_session"]], HandleError]: ...

"""Extract the identifier from a client session opaque handle."""
def extract_handle_id(handle: Opaque[Literal["client_session"]]) -> U64: ...

__all__ = ["HandleError", "HandleError_InvalidHandle", "extract_handle_id", "wrap_handle"]
