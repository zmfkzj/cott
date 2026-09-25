from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.boundary_protocols_types import ConnectionId as ConnectionId, HandleBundle as HandleBundle, TextBuffer as TextBuffer
"""Wrap a connection ID in a client-session opaque handle.

The handle's opaque payload is the U64 value carried by `raw_id`, not the `ConnectionId`
wrapper and not a target object derived from it. `HandleBundle.raw_id` repeats the same ID
as plain data."""
def wrap_handle(raw_id: ConnectionId) -> HandleBundle: ...

"""Explicitly adapt a client-session opaque handle back to its connection ID by reading the
handle's opaque payload. `bundle` comes from `wrap_handle`; a handle carrying any other
payload is outside this contract."""
def extract_handle_id(bundle: HandleBundle) -> ConnectionId: ...

"""Retype an unconstrained `Any` value as `Unknown`, so that callers must narrow it explicitly
before use."""
def adapt_unknown(value: Any) -> object: ...

"""Iterate the lines of a caller-owned text buffer. A line ends at LF, CR or CRLF, and the
terminator is not part of the yielded line. A final line without a terminator is still
yielded; an empty buffer yields nothing."""
def iter_lines(buffer: TextBuffer) -> Iterator[str]: ...

"""Re-yield the values of an iterator from a generator. Values sent into the generator are
ignored; its return value is the number of values it yielded."""
def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]: ...

"""Pass an async line iterator across the boundary."""
async def async_lines(values: AsyncIterator[str]) -> AsyncIterator[str]: ...

"""Pass an async generator across the boundary."""
async def echo_async(values: AsyncGenerator[Any, object]) -> AsyncGenerator[Any, object]: ...

__all__ = ["ConnectionId", "HandleBundle", "TextBuffer", "adapt_unknown", "async_lines", "echo_async", "echo_values", "extract_handle_id", "iter_lines", "wrap_handle"]
