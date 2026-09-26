from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong.files_types import DecompressError as DecompressError, DecompressError_Corrupt as DecompressError_Corrupt, FindResult as FindResult, SaveError as SaveError, SaveError_WriteFailed as SaveError_WriteFailed, SourceError as SourceError, SourceError_NotFound as SourceError_NotFound, SourceError_OpenFailed as SourceError_OpenFailed, TailChunk as TailChunk, TimeJump as TimeJump, TimestampAt as TimestampAt, TimestampBatch as TimestampBatch
from real.toolong.model_types import ByteSpan, Compression, Compression_Uncompressed, FindQuery, LogSource, LogTimestamp, TabIndex, TimeUnit
"""The compression Toolong detects from a file name (CPython 3.14
mimetypes.guess_type(name, strict=False) encodings, restated because the
mimetypes module is not importable here). Let ext be the final suffix of
name (os.path.splitext). First, while ext.lower() is ".svgz", ".tgz",
".taz", ".tz", ".tbz2" or ".txz", replace that suffix by ".svg.gz",
".tar.gz", ".tar.gz", ".tar.gz", ".tar.bz2" or ".tar.xz" respectively and
take the new final suffix. Then an ext of exactly ".gz" (case sensitive)
is Gzip, exactly ".bz2" is Bzip2, and anything else is Uncompressed."""
def detect_compression(name: str) -> Compression: ...

"""Decompress whole-file content: Gzip with gzip.decompress (multi-member
files concatenate), Bzip2 with bz2.decompress, Uncompressed returns data
unchanged. A decompression failure is DecompressError.Corrupt with str() of
the exception, for example "Not a gzipped file (b'no')"."""
def decompress(data: bytes, compression: Compression) -> Result[bytes, DecompressError]: ...

"""Open a log file the way Toolong's LogFile.open does. name is the final
component of path (pathlib name) and compression is
real.toolong.files.detect_compression(name).

Outside a Cott scenario (the fixture read adapter reports that adapters
are inactive): an Uncompressed file is opened read-only with os.open, its
size is found by seeking its descriptor to the end, descriptor is Some of
that descriptor and can_tail is true. A compressed file is decompressed
with gzip.open / bz2.open in 256 KiB chunks into an anonymous temporary
file (tempfile.TemporaryFile); descriptor is Some of a descriptor on that
unlinked temporary file (the temporary file object itself is closed), size
is the number of decompressed bytes and can_tail is false.

While a Cott scenario file-system fixture is active, path is read through
the fixture, compressed content is decompressed with
real.toolong.files.decompress, descriptor is Nothing, size is the content
length and can_tail is true only for Uncompressed files.

A missing file is SourceError.NotFound(name, message); any other failure
to open, read or decompress is SourceError.OpenFailed(name, message).
message is str() of the underlying exception, e.g. "[Errno 2] No such file
or directory: 'x.log'" (for fixture failures, of the adapter's OSError
cause), or the DecompressError.Corrupt message."""
def open_source(path: Path) -> Result[LogSource, SourceError]: ...

"""Close source.descriptor with os.close when it is Some, ignoring OSError.
Nothing to do when it is Nothing."""
def close_source(source: LogSource) -> Unit: ...

"""Toolong's get_raw: the content bytes [span.start, span.end). Empty when
start >= end. With Some(descriptor) read them with os.pread (fewer bytes
near the end of the content). With Nothing, read source.path through the
active scenario file-system fixture, decompress it as source.compression
says, and slice. Read failures give empty bytes."""
def read_span(source: LogSource, span: ByteSpan) -> bytes: ...

"""Toolong's get_line for every span, in order: the span's bytes
(real.toolong.files.read_span) decoded as UTF-8 with errors="replace",
with every leading and trailing LF and CR removed (str.strip("\\n\\r")) and
tabs expanded with str.expandtabs(4)."""
def read_lines(source: LogSource, spans: CottList[ByteSpan]) -> CottList[str]: ...

"""The offsets of every LF byte in the content range [start, min(end,
source.size)), ascending, as an opaque tuple of U64s. Read the range in
bounded chunks with os.pread when source.descriptor is Some; with Nothing,
use the fixture content as real.toolong.files.read_span does."""
def scan_breaks(source: LogSource, start: U64, end: U64) -> Opaque[Literal["file_breaks"]]: ...

"""One poll of Toolong's tail watcher: read up to 65536 bytes of content
starting at position (os.pread with a descriptor; the fixture content
otherwise). The result position is position plus the number of bytes read
and breaks are the offsets (position + index) of the LF bytes read, in
order. Nothing read gives position unchanged and no breaks. Content that
shrank below position (truncation) is not detected, exactly as upstream."""
def poll_source(source: LogSource, position: U64) -> TailChunk: ...

"""One batch of Toolong's merge scan. Starting at position, read up to limit
lines the way a binary readline does: a line is the bytes up to and
including the next LF, or the remaining bytes when no LF follows; reading
stops at the end of the content (source.size). Each line, decoded as UTF-8
with errors="replace" and still ending with its LF, is scanned with
real.toolong.timestamps.scan_timestamp using the current order, which
carries over from line to line. Entry k has line first_line + k, end the
offset just after the line, and seconds
real.toolong.timestamps.timestamp_seconds of the timestamp found or 0.0.
The result position is the offset after the last line read and order is
the final order. Return entries as an opaque tuple of TimestampEntry so
a 10000-line batch is safe across the facade boundary."""
def scan_timestamps(source: LogSource, position: U64, first_line: U64, limit: U64, order: CottList[U8]) -> TimestampBatch: ...

"""Toolong's advance_search while the find dialog is shown. Examine lines
start, start + 1, ..., line_count - 1 when direction is positive, or start,
start - 1, ..., 0 when it is not (no lines when start is negative or, going
forward, not below line_count). For each line, locate it with
real.toolong.index.line_location, read its raw bytes with
real.toolong.files.read_span from sources[location.file] (an empty string
when that file is missing), decode them as UTF-8 with errors="replace"
without stripping anything (so lines after the first of a single file
start with the preceding LF), and test them with
real.toolong.text.line_matches. The first line that matches is the result
line; invalid_regex is true when that test reported an invalid regular
expression."""
def find_line(sources: CottList[LogSource], index: TabIndex, line_count: U64, start: I64, direction: I8, query: FindQuery) -> FindResult: ...

"""Toolong's get_timestamp: locate line with real.toolong.index.line_location,
read its text as real.toolong.files.read_lines does from
sources[location.file] (the empty string when that file is missing) and
scan it with real.toolong.timestamps.scan_timestamp using that file's
order. orders holds one order per file; before scanning, missing entries up
to the file's index are filled with
real.toolong.timestamps.default_timestamp_order(). The result orders are
the (filled) orders with that file's order replaced by the scan's order."""
def line_timestamp(sources: CottList[LogSource], index: TabIndex, line: U64, orders: CottList[CottList[U8]]) -> TimestampAt: ...

"""Toolong's timestamp navigation (keys m/M, h/H, d/D) from from_line, using
real.toolong.files.line_timestamp for every timestamp read and threading
the orders through all reads.

Starting at line = from_line, while the line has no timestamp: advance line
by one and count the step; when the count reaches line_count or exceeds 10,
the result line is Nothing (bell). With the timestamp t found, let
direction be +1 when steps > 0 and -1 otherwise, move line by direction,
and compute the target real.toolong.timestamps.shift_timestamp(t, steps,
unit) (Nothing: the result line is Nothing).

Forward: while line < line_count, stop at the first line whose timestamp
compares (real.toolong.timestamps.compare_timestamps) greater than or equal
to the target; otherwise advance. Backward: while line > 0, stop at the
first line whose timestamp compares less than or equal to the target;
otherwise go back one line. Incomparable timestamps (naive against aware)
never stop the walk. The result line is where the walk stopped (possibly
line_count or 0)."""
def locate_time(sources: CottList[LogSource], index: TabIndex, line_count: U64, from_line: U64, steps: I32, unit: TimeUnit, orders: CottList[CottList[U8]]) -> TimeJump: ...

"""Toolong's save of a merged view (--output-merge): for each line 0 ..
line_count - 1 in order, read its text as real.toolong.files.read_lines
does (locating it with real.toolong.index.line_location; missing files
give ""), and write every non-empty line followed by LF, UTF-8 encoded, to
path, replacing any existing file. Outside a Cott scenario write with the
host file system (open(path, "w", encoding="utf-8")); while a scenario
file-system fixture is active write through the fixture instead. Ok holds
the number of lines written. Any failure is SaveError.WriteFailed with
str() of the exception (of the adapter's OSError cause for fixture
failures)."""
def save_lines(sources: CottList[LogSource], index: TabIndex, line_count: U64, path: Path) -> Result[U64, SaveError]: ...

__all__ = ["DecompressError", "DecompressError_Corrupt", "FindResult", "SaveError", "SaveError_WriteFailed", "SourceError", "SourceError_NotFound", "SourceError_OpenFailed", "TailChunk", "TimeJump", "TimestampAt", "TimestampBatch", "close_source", "decompress", "detect_compression", "find_line", "line_timestamp", "locate_time", "open_source", "poll_source", "read_lines", "read_span", "save_lines", "scan_breaks", "scan_timestamps"]
