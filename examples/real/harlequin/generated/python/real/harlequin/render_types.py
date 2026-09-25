from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult, SavedFile

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Table:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Vertical:
    pass

RenderLayout: TypeAlias = Union[RenderLayout_Table, RenderLayout_Vertical]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Csv:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Tsv:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Json:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Markdown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Sql:
    pass

ExportFormat: TypeAlias = Union[ExportFormat_Csv, ExportFormat_Tsv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Sql]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderOptions:
    __hash__ = None
    layout: RenderLayout
    terminal_width: U16
    maximum_cell_width: U16
    maximum_rows: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "layout", _cott_validate_abi(self.layout, RenderLayout, path="$.layout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_width", _cott_validate_abi(self.terminal_width, U16, path="$.terminal_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "maximum_cell_width", _cott_validate_abi(self.maximum_cell_width, U16, path="$.maximum_cell_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "maximum_rows", _cott_validate_abi(self.maximum_rows, U32, path="$.maximum_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    __hash__ = None
    name: str
    foreground: str
    background: str
    accent: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "foreground", _cott_validate_abi(self.foreground, str, path="$.foreground"))
        if not _cott_validated_construction():
            object.__setattr__(self, "background", _cott_validate_abi(self.background, str, path="$.background"))
        if not _cott_validated_construction():
            object.__setattr__(self, "accent", _cott_validate_abi(self.accent, str, path="$.accent"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeyBinding:
    __hash__ = None
    key: str
    command: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "command", _cott_validate_abi(self.command, str, path="$.command"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Keymap:
    __hash__ = None
    name: str
    bindings: CottList[KeyBinding]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bindings", _cott_validate_abi(self.bindings, CottList[KeyBinding], path="$.bindings"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRequest:
    __hash__ = None
    result: QueryResult
    format: ExportFormat
    destination: FileReference

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "result", _cott_validate_abi(self.result, QueryResult, path="$.result"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, ExportFormat, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, FileReference, path="$.destination"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_InvalidWidth:
    __hash__ = None
    width: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_UnsupportedCell:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_DestinationDenied:
    __hash__ = None
    destination: FileReference

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_ExportFailed:
    __hash__ = None
    destination: FileReference
    message: str

RenderError: TypeAlias = Union[RenderError_InvalidWidth, RenderError_UnsupportedCell, RenderError_DestinationDenied, RenderError_ExportFailed]

"""Format Cell.Null as NULL, Integer/Real as str(value), Text as its stored text,
and Blob as lowercase hexadecimal. Emit a header joined by " | " when columns
is nonempty, then one similarly joined line for each row in input order.
Join lines with LF without a trailing LF. No columns and no rows returns "".
This function applies no row or width limit."""
"""For each row, starting at one, emit "Row N" followed by "column: value" lines
for paired columns and values. Use the same cell text mapping as render_table.
Preserve order, join with LF without a trailing LF; no rows returns "".
Pair only the common length if columns and values differ."""
"""terminal_width or maximum_cell_width zero returns InvalidWidth with that zero
width. Keep only the first maximum_rows rows, preserving columns and order.
A NUL in a column name or in a Text cell of a kept row is UnsupportedCell.
Use the render_table cell mapping, truncating every column/cell string to
maximum_cell_width Unicode code points before formatting. Table uses " | "
headers/rows; Vertical uses "Row N" and "column: value" lines.
Clip each resulting line to terminal_width code points without ellipsis.
Join with LF and no trailing LF. If output would be empty or whitespace only,
use "(no rows)" clipped to terminal_width so successful output is nonempty."""
"""One line per relation in input order: "table NAME" or "view NAME". Stored SQL is
not shown. Lines are joined with LF without a trailing LF; empty input is ""."""
"""One line per column in input order: RELATION.NAME, then " " and declared_type
when it is nonempty, " NOT NULL" when not_null, " DEFAULT " and default_sql when
present, and " PRIMARY KEY " followed by primary_key_position when it is nonzero.
ordinal is not shown. Lines are joined with LF without a trailing LF; empty input
is ""."""
"""One line per match in input order: "relation NAME" for a Relation match and
"column RELATION.NAME" for a Column match. Lines are joined with LF without a
trailing LF; empty input is ""."""
"""Return exactly these built-in themes, in this order, as
name | foreground | background | accent:
harlequin | #DDDDDD | #0C0C0C | #FEFFAC
monokai | #F8F8F2 | #272822 | #F92672
dracula | #F8F8F2 | #282A36 | #BD93F9
nord | #D8DEE9 | #2E3440 | #88C0D0"""
"""Return exactly two built-in keymaps, in this order. "default" contains
ctrl+enter -> execute, ctrl+s -> save, ctrl+q -> quit.
"vim" contains ctrl+enter -> execute, :w -> save, :q -> quit.
Preserve the listed binding order and exact spelling. These are this Cott
client's static defaults, not a runtime scan of upstream packages or plugins."""
"""Return Some containing the first Theme whose name exactly equals name,
case-sensitively; return Nothing when there is no match."""
"""Return Some containing the first Keymap whose name exactly equals name,
case-sensitively; return Nothing when there is no match."""
"""Serialize request.result in request.format as UTF-8 text and write it to
request.destination. Every line, including the last, ends with LF. A field's
text is "" for Null, the decimal integer, the float's Python repr, the stored
text, or lowercase hexadecimal for a blob.
Csv: a header line of column names, then one line per row, fields separated by
"," and enclosed in '"' (inner quotes doubled) when they contain ",", '"', CR or
LF.
Tsv: the same lines separated by TAB without quoting; TAB, LF, CR and backslash
in a field are written as \\t, \\n, \\r and \\\\.
Json: one line holding {"columns":[...],"rows":[[...],...]} with no whitespace
between tokens and non-ASCII characters unescaped; cells are null, numbers,
strings, and lowercase hexadecimal strings for blobs.
Markdown: "| " + fields joined by " | " + " |" for the header, then "| --- |"
with " --- |" repeated for each further column, then each row the same way; "|"
in a field is written as "\\|" and each CR LF, LF or CR as "<br>".
Sql: one line per row, INSERT INTO "result" ("a", "b") VALUES (...); with names
double-quoted (inner quotes doubled) and values NULL, the integer, the float's
repr, single-quoted text (inner quotes doubled) or X'hex' for blobs.
A result without columns produces empty text in Csv, Tsv, Markdown and Sql.
Json and Sql reject a non-finite float as UnsupportedCell(message).
A destination that is not writable is DestinationDenied(destination) before any
I/O; an access refusal by the filesystem or S3 is DestinationDenied too. A Local
destination is written to a temporary file in the same directory and atomically
replaces path; S3 puts the object key into bucket with boto3. Other failures are
ExportFailed(destination, message) with a fixed message that contains no
credential or service response text. The receipt reports the destination and the
number of UTF-8 bytes written.
A Local destination is replaced in the file system the program runs against: the
fs fixture root while a Cott scenario with an fs fixture is active, otherwise the
host file system; the replacement is atomic in both. While such a fixture is
active the host file system is never used, even when the fixture write fails."""
__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme"]
