from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.opaque_resource_types import HandleBundle as HandleBundle, HandleError as HandleError, HandleError_InvalidHandle as HandleError_InvalidHandle, TextBuffer as TextBuffer
"""Wrap a nonzero connection ID in a bundle containing a client-session handle."""
def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]: ...

"""Extract the client-session handle ID from a bundle returned by wrap_handle."""
def extract_handle_id(bundle: HandleBundle) -> U64: ...

"""Lazily yield the buffer's lines without their trailing line endings."""
def iter_lines(buffer: TextBuffer) -> Iterator[str]: ...

"""Yield each input value, ignore sent values, and return the yielded count."""
def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]: ...

__all__ = ["HandleBundle", "HandleError", "HandleError_InvalidHandle", "TextBuffer", "echo_values", "extract_handle_id", "iter_lines", "wrap_handle"]
