from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong_types import EntryKind as EntryKind, EntryKind_Access as EntryKind_Access, EntryKind_Error as EntryKind_Error, EntryKind_Json as EntryKind_Json, EntryKind_Plain as EntryKind_Plain, LogEntry as LogEntry, LogPage as LogPage, LogSource as LogSource, ToolongError as ToolongError, ToolongError_CompressedAppendUnsupported as ToolongError_CompressedAppendUnsupported, ToolongError_DecodeFailed as ToolongError_DecodeFailed, ToolongError_InvalidIndent as ToolongError_InvalidIndent, ToolongError_InvalidLimit as ToolongError_InvalidLimit, ToolongError_InvalidOffset as ToolongError_InvalidOffset, ToolongError_OpenFailed as ToolongError_OpenFailed
def load_log(source: LogSource, limit: U64) -> Result[LogPage, ToolongError]: ...

def render_jsonl(entries: CottList[LogEntry], indent: U8) -> Result[CottList[str], ToolongError]: ...

def merge_pages(pages: CottList[LogPage], limit: U64) -> Result[CottList[LogEntry], ToolongError]: ...

def search_entries(entries: CottList[LogEntry], needle: str, limit: U64) -> Result[CottList[LogEntry], ToolongError]: ...

def read_appended(source: LogSource, from_byte: U64, limit: U64) -> Result[LogPage, ToolongError]: ...

__all__ = ["EntryKind", "EntryKind_Access", "EntryKind_Error", "EntryKind_Json", "EntryKind_Plain", "LogEntry", "LogPage", "LogSource", "ToolongError", "ToolongError_CompressedAppendUnsupported", "ToolongError_DecodeFailed", "ToolongError_InvalidIndent", "ToolongError_InvalidLimit", "ToolongError_InvalidOffset", "ToolongError_OpenFailed", "load_log", "merge_pages", "read_appended", "render_jsonl", "search_entries"]
