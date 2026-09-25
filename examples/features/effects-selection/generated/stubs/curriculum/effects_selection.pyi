from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.effects_selection_types import CopyReceipt as CopyReceipt, EffectError as EffectError, EffectError_InputMissing as EffectError_InputMissing, EffectError_OperationFailed as EffectError_OperationFailed, FileText as FileText, PageText as PageText
"""Read the file at source and decode its bytes as strict UTF-8. The result
pairs the decoded text with source. An absent source returns InputMissing
carrying source; any other read failure and bytes that are not valid UTF-8
return OperationFailed."""
def read_text(source: Path) -> Result[FileText, EffectError]: ...

"""Copy the text of source to destination as UTF-8 bytes. bytes_written is
the encoded byte count, not the character count. A read_text error is
returned unchanged and destination is left untouched."""
def copy_text(source: Path, destination: Path) -> Result[CopyReceipt, EffectError]: ...

"""GET url over HTTP, following redirects, and decode the final response body
as strict UTF-8. The result pairs the text with the requested url. An empty
url returns OperationFailed without sending a request; a connection or read
failure, a timeout, a final status outside 200-299 and a body that is not
valid UTF-8 return OperationFailed."""
def fetch_local(url: str) -> Result[PageText, EffectError]: ...

"""Store value under key in the SQLite database file at database, replacing
any previous value for key, then read the value stored under key back from
that database. Any SQLite failure returns OperationFailed."""
def store_and_load(database: Path, key: str, value: str) -> Result[str, EffectError]: ...

"""Read the compiler-owned clock fixture and return its time in nanoseconds.
The fixture is configured in milliseconds, so start_ms 17 reads as
17000000. Reading does not advance the clock."""
def clock_ns() -> U64: ...

"""Choose an index below limit from seed."""
def sample_index(limit: U8, seed: U64) -> U8: ...

"""Terminate the current process."""
def exit_with_code(code: U8) -> Never: ...

__all__ = ["CopyReceipt", "EffectError", "EffectError_InputMissing", "EffectError_OperationFailed", "FileText", "PageText", "clock_ns", "copy_text", "exit_with_code", "fetch_local", "read_text", "sample_index", "store_and_load"]
