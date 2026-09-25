from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong_types import LogEntry as LogEntry, ToolongError as ToolongError, ToolongError_InvalidArguments as ToolongError_InvalidArguments, ToolongError_ReadFailed as ToolongError_ReadFailed, ViewerOptions as ViewerOptions
"""Parse the command line [--contains TEXT] PATH... . Only the first argument
can be the option: when it is exactly "--contains", the second argument is
TEXT (any string, including an empty one or one starting with "--") and
contains is Option.Some(TEXT); every later argument is a path. Otherwise
contains is Option.Nothing and every argument, including a later
"--contains", is a path. Each path argument becomes one source, in argument
order. InvalidArguments: no arguments, "--contains" without TEXT, or no path."""
def parse_arguments(arguments: CottList[str]) -> Result[ViewerOptions, ToolongError]: ...

"""Split the text of one log file into entries. Split text at every LF; drop the
last piece when it is empty (text ending in LF, or empty text); then remove
one trailing CR from each remaining piece. Empty lines in the middle are
kept. No other character (CR alone, VT, FF, NEL, U+2028, U+2029) separates
lines. Entry i, counted from one in piece order, has this source, line i and
the piece as text."""
def parse_log(source: Path, text: str) -> CottList[LogEntry]: ...

"""Read each source completely, in list order, and decode its bytes as strict
UTF-8. Each source path is read from the file system the program runs
against: the fs fixture root while a Cott scenario with an fs fixture is
active, otherwise the host file system, where a relative path is relative to
the process working directory. The result is the concatenation of
real.toolong.parse_log(source, text) for every source, so numbering restarts
at one for each source. The first source that is missing, cannot be opened
or read, or is not strict UTF-8 stops loading with ToolongError.ReadFailed
whose path is that source; no entries are returned then. While a scenario fs
fixture is active, a path the fixture does not permit (absolute, or outside
the fixture root) is a contract violation raised by the fixture, not a read
failure."""
def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]: ...

"""Without a filter return entries unchanged. With a filter keep, in their
original order and multiplicity, exactly the entries whose text contains the
filter as a substring after mapping the ASCII letters A-Z to a-z in both
strings. Every other code point compares exactly: there is no Unicode case
folding or normalization. An empty filter keeps every entry."""
def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]: ...

"""Render one line per entry in order: the source path text, ":", the decimal
line number, one space and the text. Lines are joined with LF and there is no
trailing LF, so no entries render as the empty string."""
def render_entries(entries: CottList[LogEntry]) -> str: ...

"""The toolong composition root. Call real.toolong.parse_arguments with
arguments, then real.toolong.load_entries with its sources, then
real.toolong.filter_entries with the loaded entries and its contains value,
and return real.toolong.render_entries of the kept entries. An error from
parse_arguments is returned unchanged before any file is read; an error from
load_entries is returned unchanged and nothing is filtered or rendered."""
def execute(arguments: CottList[str]) -> Result[str, ToolongError]: ...

__all__ = ["LogEntry", "ToolongError", "ToolongError_InvalidArguments", "ToolongError_ReadFailed", "ViewerOptions", "execute", "filter_entries", "load_entries", "parse_arguments", "parse_log", "render_entries"]
