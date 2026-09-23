from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong_types import LogEntry as LogEntry, ToolongError as ToolongError, ToolongError_InvalidArguments as ToolongError_InvalidArguments, ToolongError_ReadFailed as ToolongError_ReadFailed, ViewerOptions as ViewerOptions
"""Parse [--contains TEXT] followed by one or more log paths."""
def parse_arguments(arguments: CottList[str]) -> Result[ViewerOptions, ToolongError]: ...

"""Read UTF-8 log lines in source order and number each source from one."""
def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]: ...

"""Keep all entries without a filter; otherwise keep case-insensitive substring matches."""
def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]: ...

"""Render path:line and text for each entry, separated by newlines."""
def render_entries(entries: CottList[LogEntry]) -> str: ...

"""Call real.toolong.parse_arguments, then real.toolong.load_entries on its
sources. Pass the entries and parsed contains option to real.toolong.filter_entries
and return real.toolong.render_entries of those matches.
Return an error from parsing or loading unchanged; do not load files after
argument parsing fails."""
def execute(arguments: CottList[str]) -> Result[str, ToolongError]: ...

__all__ = ["LogEntry", "ToolongError", "ToolongError_InvalidArguments", "ToolongError_ReadFailed", "ViewerOptions", "execute", "filter_entries", "load_entries", "parse_arguments", "render_entries"]
