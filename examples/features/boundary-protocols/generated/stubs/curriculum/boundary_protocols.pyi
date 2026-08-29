from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.boundary_protocols_types import HandleBundle as HandleBundle, HandleError as HandleError, HandleError_InvalidHandle as HandleError_InvalidHandle, TextBuffer as TextBuffer
"""Wrap a nonzero connection ID in a client-session opaque handle."""
def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]: ...

"""Explicitly adapt a client-session opaque handle to its Python ID."""
def extract_handle_id(bundle: HandleBundle) -> U64: ...

"""Deliberately adapt an unconstrained value to an explicitly narrowed boundary value."""
def adapt_unknown(value: Any) -> object: ...

"""Lazily yield buffer lines without trailing line endings."""
def iter_lines(buffer: TextBuffer) -> Iterator[str]: ...

"""Yield each value, discard sent unknown values, and return the yield count."""
def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]: ...

"""Return the supplied async iterator."""
async def async_lines(values: AsyncIterator[str]) -> AsyncIterator[str]: ...

"""Return the supplied async generator."""
async def echo_async(values: AsyncGenerator[Any, object]) -> AsyncGenerator[Any, object]: ...

__all__ = ["HandleBundle", "HandleError", "HandleError_InvalidHandle", "TextBuffer", "adapt_unknown", "async_lines", "echo_async", "echo_values", "extract_handle_id", "iter_lines", "wrap_handle"]
