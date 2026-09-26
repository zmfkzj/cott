from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""A terminal color. Default is the color the surrounding widget would use
(the base foreground or background of the text being drawn). Indexed is an
xterm 256-color palette entry (0-15 are the ANSI colors: 0 black, 1 red,
2 green, 3 yellow, 4 blue, 5 magenta, 6 cyan, 7 white, 8-15 their bright
variants). Rgb is a 24-bit color."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TermColor_Default:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TermColor_Indexed:
    __hash__ = None
    index: U8

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TermColor_Rgb:
    __hash__ = None
    red: U8
    green: U8
    blue: U8

TermColor: TypeAlias = Union[TermColor_Default, TermColor_Indexed, TermColor_Rgb]

"""A style applied to the code points [start, end) of a StyledText. Offsets
count Unicode code points (Python str indexes), not bytes or cells.

style is a style code: the canonical text form of one rich-style layer, kept
as a single string so that densely highlighted lines stay far below the
1024-node ABI traversal limit. It is the space-separated sequence of these
optional tokens, in this order: "fg:" + COLOR (foreground set), "bg:" +
COLOR (background set), then for each attribute in the order bold, dim,
italic, underline, reverse either the attribute name (set true) or "no" +
the name (explicitly cleared, e.g. "noitalic"); an attribute not mentioned
is not set by this layer and inherits from the layers below. The empty code
sets nothing. COLOR is "default" for TermColor.Default, for TermColor.Indexed
0-15 the prompt_toolkit ANSI name "ansiblack", "ansired", "ansigreen",
"ansiyellow", "ansiblue", "ansimagenta", "ansicyan", "ansigray",
"ansibrightblack", "ansibrightred", "ansibrightgreen", "ansibrightyellow",
"ansibrightblue", "ansibrightmagenta", "ansibrightcyan", "ansiwhite" (in
index order), and otherwise "#" + the lowercase two-digit hex of red, green
and blue: Rgb as given, Indexed 16-231 from the xterm 6x6x6 cube with
channel levels 0, 95, 135, 175, 215, 255 (index 16 + 36r + 6g + b) and
Indexed 232-255 as gray 8 + 10 * (index - 232). Example: foreground
Indexed(6), bold true, italic false is "fg:ansicyan bold noitalic"."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StyledSpan:
    __hash__ = None
    start: U32
    end: U32
    style: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "start", _cott_validate_abi(self.start, U32, path="$.start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "end", _cott_validate_abi(self.end, U32, path="$.end"))
        if not _cott_validated_construction():
            object.__setattr__(self, "style", _cott_validate_abi(self.style, str, path="$.style"))
        if not (_cott_contract_condition((((self).start <= (self).end)), "real.toolong.model.StyledSpan", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.StyledSpan", clause="invariant:0", phase="invariant", span={"end_byte":2017,"end_column":37,"end_line":43,"start_byte":1985,"start_column":5,"start_line":43}, expected="true", actual="false")

"""Styled text in the rich 13.7.0 Text model: plain text plus style spans. When
the text is drawn, the spans are layered over the base style in list order,
so a later span's set attributes and colors override earlier ones for the
code points it covers."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StyledText:
    __hash__ = None
    text: str
    spans: CottList[StyledSpan]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "spans", _cott_validate_abi(self.spans, CottList[StyledSpan], path="$.spans"))

"""Consecutive terminal cells sharing one style. text is the characters drawn
left to right; a double-width character occupies two cells. style is a cell
code: the style code (see StyledSpan) of a fully resolved cell, which always
has "fg:" and "bg:" tokens and lists only the attributes that are on (never a
"no" token), in the StyledSpan token order. A cell code is exactly a
prompt_toolkit style string, e.g. "fg:#e1e1e1 bg:#1e1e1e bold". "default"
colors mean the terminal's own default color."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StyledRun:
    __hash__ = None
    text: str
    style: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "style", _cott_validate_abi(self.style, str, path="$.style"))

"""One terminal row as runs drawn left to right from column 0. Adjacent runs
always have different styles and the runs cover exactly the frame width in
cells."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ScreenRow:
    __hash__ = None
    runs: CottList[StyledRun]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "runs", _cott_validate_abi(self.runs, CottList[StyledRun], path="$.runs"))

"""A rectangle of terminal cells: columns [x, x + width), rows [y, y + height)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rect:
    __hash__ = None
    x: U16
    y: U16
    width: U16
    height: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "x", _cott_validate_abi(self.x, U16, path="$.x"))
        if not _cott_validated_construction():
            object.__setattr__(self, "y", _cott_validate_abi(self.y, U16, path="$.y"))
        if not _cott_validated_construction():
            object.__setattr__(self, "width", _cott_validate_abi(self.width, U16, path="$.width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "height", _cott_validate_abi(self.height, U16, path="$.height"))

"""A timestamp found in a log line, holding exactly the fields of the CPython
datetime it was parsed into. utc_offset_seconds is Nothing for a naive
datetime and the whole-second UTC offset for an aware one."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogTimestamp:
    __hash__ = None
    year: U16
    month: U8
    day: U8
    hour: U8
    minute: U8
    second: U8
    microsecond: U32
    utc_offset_seconds: Option[I32]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "year", _cott_validate_abi(self.year, U16, path="$.year"))
        if not _cott_validated_construction():
            object.__setattr__(self, "month", _cott_validate_abi(self.month, U8, path="$.month"))
        if not _cott_validated_construction():
            object.__setattr__(self, "day", _cott_validate_abi(self.day, U8, path="$.day"))
        if not _cott_validated_construction():
            object.__setattr__(self, "hour", _cott_validate_abi(self.hour, U8, path="$.hour"))
        if not _cott_validated_construction():
            object.__setattr__(self, "minute", _cott_validate_abi(self.minute, U8, path="$.minute"))
        if not _cott_validated_construction():
            object.__setattr__(self, "second", _cott_validate_abi(self.second, U8, path="$.second"))
        if not _cott_validated_construction():
            object.__setattr__(self, "microsecond", _cott_validate_abi(self.microsecond, U32, path="$.microsecond"))
        if not _cott_validated_construction():
            object.__setattr__(self, "utc_offset_seconds", _cott_validate_abi(self.utc_offset_seconds, Option[I32], path="$.utc_offset_seconds"))
        if not (_cott_contract_condition(((((self).year >= 1) and ((self).year <= 9999))), "real.toolong.model.LogTimestamp", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:0", phase="invariant", span={"end_byte":3696,"end_column":51,"end_line":100,"start_byte":3650,"start_column":5,"start_line":100}, expected="true", actual="false")
        if not (_cott_contract_condition(((((self).month >= 1) and ((self).month <= 12))), "real.toolong.model.LogTimestamp", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:1", phase="invariant", span={"end_byte":3747,"end_column":51,"end_line":101,"start_byte":3701,"start_column":5,"start_line":101}, expected="true", actual="false")
        if not (_cott_contract_condition(((((self).day >= 1) and ((self).day <= 31))), "real.toolong.model.LogTimestamp", "invariant:2")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:2", phase="invariant", span={"end_byte":3794,"end_column":47,"end_line":102,"start_byte":3752,"start_column":5,"start_line":102}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).hour <= 23)), "real.toolong.model.LogTimestamp", "invariant:3")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:3", phase="invariant", span={"end_byte":3824,"end_column":30,"end_line":103,"start_byte":3799,"start_column":5,"start_line":103}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).minute <= 59)), "real.toolong.model.LogTimestamp", "invariant:4")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:4", phase="invariant", span={"end_byte":3856,"end_column":32,"end_line":104,"start_byte":3829,"start_column":5,"start_line":104}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).second <= 59)), "real.toolong.model.LogTimestamp", "invariant:5")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:5", phase="invariant", span={"end_byte":3888,"end_column":32,"end_line":105,"start_byte":3861,"start_column":5,"start_line":105}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).microsecond <= 999999)), "real.toolong.model.LogTimestamp", "invariant:6")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.model.LogTimestamp", clause="invariant:6", phase="invariant", span={"end_byte":3929,"end_column":41,"end_line":106,"start_byte":3893,"start_column":5,"start_line":106}, expected="true", actual="false")

"""The result of one timestamp scan: the timestamp found, if any, and the
scanner's format order after the scan (most recently matched format first)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TimestampScan:
    __hash__ = None
    timestamp: Option[LogTimestamp]
    order: CottList[U8]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "timestamp", _cott_validate_abi(self.timestamp, Option[LogTimestamp], path="$.timestamp"))
        if not _cott_validated_construction():
            object.__setattr__(self, "order", _cott_validate_abi(self.order, CottList[U8], path="$.order"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TimeUnit_Minute:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TimeUnit_Hour:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TimeUnit_Day:
    pass

TimeUnit: TypeAlias = Union[TimeUnit_Minute, TimeUnit_Hour, TimeUnit_Day]

"""The log line formats of Toolong's format parser."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineFormat_Json:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineFormat_CommonLog:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineFormat_CombinedLog:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineFormat_Plain:
    pass

LineFormat: TypeAlias = Union[LineFormat_Json, LineFormat_CommonLog, LineFormat_CombinedLog, LineFormat_Plain]

"""One parsed log line: the format that accepted it, the line text that format
kept, its highlighted text, and the parser's format order after parsing
(most recently matched format first)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedLine:
    __hash__ = None
    format: LineFormat
    line: str
    text: StyledText
    order: CottList[LineFormat]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, LineFormat, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "line", _cott_validate_abi(self.line, str, path="$.line"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, StyledText, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "order", _cott_validate_abi(self.order, CottList[LineFormat], path="$.order"))

"""The find dialog query: the text typed, whether the Regex checkbox is on and
whether the Case sensitive checkbox is on."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FindQuery:
    __hash__ = None
    text: str
    regex: bool
    case_sensitive: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "regex", _cott_validate_abi(self.regex, bool, path="$.regex"))
        if not _cott_validated_construction():
            object.__setattr__(self, "case_sensitive", _cott_validate_abi(self.case_sensitive, bool, path="$.case_sensitive"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Compression_Uncompressed:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Compression_Gzip:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Compression_Bzip2:
    pass

Compression: TypeAlias = Union[Compression_Uncompressed, Compression_Gzip, Compression_Bzip2]

"""An opened log source. descriptor is the OS file descriptor holding the
(decompressed) content outside Cott scenarios; it is Nothing while a scenario
file-system fixture supplies the content, in which case readers re-read path
through the fixture and decompress it again when compression is not
Uncompressed. size is the content size in bytes when it was opened. name is
the final path component."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogSource:
    __hash__ = None
    path: Path
    name: str
    compression: Compression
    descriptor: Option[I32]
    size: U64
    can_tail: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "compression", _cott_validate_abi(self.compression, Compression, path="$.compression"))
        if not _cott_validated_construction():
            object.__setattr__(self, "descriptor", _cott_validate_abi(self.descriptor, Option[I32], path="$.descriptor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "size", _cott_validate_abi(self.size, U64, path="$.size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "can_tail", _cott_validate_abi(self.can_tail, bool, path="$.can_tail"))

"""Byte offsets [start, end) into a log source's content."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ByteSpan:
    __hash__ = None
    start: U64
    end: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "start", _cott_validate_abi(self.start, U64, path="$.start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "end", _cott_validate_abi(self.end, U64, path="$.end"))

"""Toolong's line index for one file. breaks is Opaque(tag="file_breaks",
value=tuple of U64 byte offsets); recursively validating a large log index
would exceed the bounded ABI traversal budget. Build it with
cott_runtime.Opaque(tag="file_breaks", value=tuple(offsets)) and read it as
typing.cast(tuple[int, ...], index.breaks.unwrap()) (unwrap() is typed
object): no per-element checks and no copy of the whole tuple per lookup.
Lines before scan_start are not indexed yet; scanned_size is the largest
content size reported by a finished scan or tail read."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileIndex:
    __hash__ = None
    breaks: Opaque[Literal["file_breaks"]]
    scan_start: U64
    scanned_size: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "breaks", _cott_validate_abi(self.breaks, Opaque[Literal["file_breaks"]], path="$.breaks"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scan_start", _cott_validate_abi(self.scan_start, U64, path="$.scan_start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scanned_size", _cott_validate_abi(self.scanned_size, U64, path="$.scanned_size"))

"""One line of a merged view: the POSIX seconds of its timestamp (0.0 when none
was found), its zero-based line number within its own file, and the index of
that file in the merged view's file list."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MergedLine:
    __hash__ = None
    seconds: F64
    line: U64
    file: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "seconds", _cott_validate_abi(self.seconds, F64, path="$.seconds"))
        if not _cott_validated_construction():
            object.__setattr__(self, "line", _cott_validate_abi(self.line, U64, path="$.line"))
        if not _cott_validated_construction():
            object.__setattr__(self, "file", _cott_validate_abi(self.file, U32, path="$.file"))

"""A merged view's index: lines is Opaque(tag="merged_lines", value=tuple of
MergedLine values in display order); breaks is Opaque(tag="merged_breaks",
value=tuple of per-file tuples of U64 line-end offsets), where breaks[i]
belongs to file i. scanned_size is the total file size. These handles keep
arbitrary-sized log indexes out of recursive ABI walks. Read them as
typing.cast(tuple[MergedLine, ...], index.lines.unwrap()) and
typing.cast(tuple[tuple[int, ...], ...], index.breaks.unwrap()), without
per-element checks or per-lookup copies."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MergedIndex:
    __hash__ = None
    lines: Opaque[Literal["merged_lines"]]
    breaks: Opaque[Literal["merged_breaks"]]
    scanned_size: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "lines", _cott_validate_abi(self.lines, Opaque[Literal["merged_lines"]], path="$.lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "breaks", _cott_validate_abi(self.breaks, Opaque[Literal["merged_breaks"]], path="$.breaks"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scanned_size", _cott_validate_abi(self.scanned_size, U64, path="$.scanned_size"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TabIndex_Single:
    __hash__ = None
    index: FileIndex

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TabIndex_Merged:
    __hash__ = None
    index: MergedIndex

TabIndex: TypeAlias = Union[TabIndex_Single, TabIndex_Merged]

"""Where a displayed line lives: the index of its file in the view's file list
and the byte span to read."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineLocation:
    __hash__ = None
    file: U32
    span: ByteSpan

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "file", _cott_validate_abi(self.file, U32, path="$.file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "span", _cott_validate_abi(self.span, ByteSpan, path="$.span"))

"""One timestamp-scan entry of a file: its zero-based line number, the byte
offset just after the line (after its LF when it has one) and the POSIX
seconds of the timestamp found on it, or 0.0 when none was found."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TimestampEntry:
    __hash__ = None
    line: U64
    end: U64
    seconds: F64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "line", _cott_validate_abi(self.line, U64, path="$.line"))
        if not _cott_validated_construction():
            object.__setattr__(self, "end", _cott_validate_abi(self.end, U64, path="$.end"))
        if not _cott_validated_construction():
            object.__setattr__(self, "seconds", _cott_validate_abi(self.seconds, F64, path="$.seconds"))

"""The timestamp scan of one file of a merged view. entries is
Opaque(tag="timestamp_entries", value=tuple of TimestampEntry values), read
as typing.cast(tuple[TimestampEntry, ...], entries.unwrap()) without
per-element checks. When opened is false the tuple is empty and size is 0.
The opaque handle bounds ABI validation independently of file length."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileTimestamps:
    __hash__ = None
    opened: bool
    size: U64
    entries: Opaque[Literal["timestamp_entries"]]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "opened", _cott_validate_abi(self.opened, bool, path="$.opened"))
        if not _cott_validated_construction():
            object.__setattr__(self, "size", _cott_validate_abi(self.size, U64, path="$.size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "entries", _cott_validate_abi(self.entries, Opaque[Literal["timestamp_entries"]], path="$.entries"))

"""One tab of the viewer: its title, the files it shows and whether they are
merged into a single timestamp-ordered view."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TabPlan:
    __hash__ = None
    title: str
    paths: CottList[Path]
    merged: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "paths", _cott_validate_abi(self.paths, CottList[Path], path="$.paths"))
        if not _cott_validated_construction():
            object.__setattr__(self, "merged", _cott_validate_abi(self.merged, bool, path="$.merged"))

"""Piped standard input being copied into the file the viewer shows: the
descriptor to read the pipe from and the path of the file to append to."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PipeFeed:
    __hash__ = None
    descriptor: I32
    path: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "descriptor", _cott_validate_abi(self.descriptor, I32, path="$.descriptor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))

"""Everything the interactive viewer needs: its tabs, where to save the merged
lines (only used by a merged tab) and an optional piped input to copy."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerSetup:
    __hash__ = None
    tabs: CottList[TabPlan]
    save_merge: Option[Path]
    pipe: Option[PipeFeed]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "tabs", _cott_validate_abi(self.tabs, CottList[TabPlan], path="$.tabs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "save_merge", _cott_validate_abi(self.save_merge, Option[Path], path="$.save_merge"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pipe", _cott_validate_abi(self.pipe, Option[PipeFeed], path="$.pipe"))

__all__ = ["ByteSpan", "Compression", "Compression_Bzip2", "Compression_Gzip", "Compression_Uncompressed", "FileIndex", "FileTimestamps", "FindQuery", "LineFormat", "LineFormat_CombinedLog", "LineFormat_CommonLog", "LineFormat_Json", "LineFormat_Plain", "LineLocation", "LogSource", "LogTimestamp", "MergedIndex", "MergedLine", "ParsedLine", "PipeFeed", "Rect", "ScreenRow", "StyledRun", "StyledSpan", "StyledText", "TabIndex", "TabIndex_Merged", "TabIndex_Single", "TabPlan", "TermColor", "TermColor_Default", "TermColor_Indexed", "TermColor_Rgb", "TimeUnit", "TimeUnit_Day", "TimeUnit_Hour", "TimeUnit_Minute", "TimestampEntry", "TimestampScan", "ViewerSetup"]
