from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.style_types import StyledLine

"""A pyarrow.Table holding the rows one statement returned, in the order the
database returned them, with duplicate column names already made unique (the
second "a" becomes "a0", a third "a1", and so on, as Harlequin's backend
renames them). The payload is exactly a pyarrow.Table; nothing else is stored
in the wrapper. Tables are immutable and may be shared."""
ArrowTable: TypeAlias = Opaque[Literal["harlequin.arrow_table"]]

"""One result column: its (deduplicated) name and the adapter's short type label
(for example "#" for an integer or "s" for a string; "" when the adapter has
none)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ColumnInfo:
    __hash__ = None
    name: str
    type_label: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "type_label", _cott_validate_abi(self.type_label, str, path="$.type_label"))

"""The data one statement returned.
statement is the SQL text that produced it. data holds every fetched row (the
overflow-probe row excluded). fetched_row_count is data's row count.
row_count is how many rows the Results Viewer holds and navigates: data's row
count capped by the viewer's max rows. truncated is true when a hard limit
stopped the fetch and the database had more rows. elapsed_ms is time spent
executing and fetching.
Field data (ArrowTable): A pyarrow.Table holding the rows one statement returned, in the order the
database returned them, with duplicate column names already made unique (the
second "a" becomes "a0", a third "a1", and so on, as Harlequin's backend
renames them). The payload is exactly a pyarrow.Table; nothing else is stored
in the wrapper. Tables are immutable and may be shared."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ResultSet:
    __hash__ = None
    statement: str
    columns: CottList[ColumnInfo]
    data: Opaque[Literal["harlequin.arrow_table"]]
    row_count: U64
    fetched_row_count: U64
    truncated: bool
    elapsed_ms: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "statement", _cott_validate_abi(self.statement, str, path="$.statement"))
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[ColumnInfo], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "data", _cott_validate_abi(self.data, Opaque[Literal["harlequin.arrow_table"]], path="$.data"))
        if not _cott_validated_construction():
            object.__setattr__(self, "row_count", _cott_validate_abi(self.row_count, U64, path="$.row_count"))
        if not _cott_validated_construction():
            object.__setattr__(self, "fetched_row_count", _cott_validate_abi(self.fetched_row_count, U64, path="$.fetched_row_count"))
        if not _cott_validated_construction():
            object.__setattr__(self, "truncated", _cott_validate_abi(self.truncated, bool, path="$.truncated"))
        if not _cott_validated_construction():
            object.__setattr__(self, "elapsed_ms", _cott_validate_abi(self.elapsed_ms, U64, path="$.elapsed_ms"))
        if not (_cott_contract_condition((((self).row_count <= (self).fetched_row_count)), "real.harlequin.results.ResultSet", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.harlequin.results.ResultSet", clause="invariant:0", phase="invariant", span={"end_byte":1788,"end_column":55,"end_line":46,"start_byte":1738,"start_column":5,"start_line":46}, expected="true", actual="false")

"""A value for building a small result set directly (tests, listings, hsql
reports). Each maps to the natural Arrow type: Null -> null, Boolean -> bool,
Integer -> int64, Real -> float64, Text -> string, Blob -> binary."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellValue_Null:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellValue_Boolean:
    __hash__ = None
    value: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellValue_Integer:
    __hash__ = None
    value: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellValue_Real:
    __hash__ = None
    value: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellValue_Text:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellValue_Blob:
    __hash__ = None
    value: bytes

CellValue: TypeAlias = Union[CellValue_Null, CellValue_Boolean, CellValue_Integer, CellValue_Real, CellValue_Text, CellValue_Blob]

"""How numbers are written in the Results Viewer, derived once from the process
locale: the LC_NUMERIC thousands separator, decimal point and grouping (as in
locale.localeconv(); grouping entries are group sizes from the right, the last
one repeating; an empty list means no grouping)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NumberFormat:
    __hash__ = None
    thousands_separator: str
    decimal_point: str
    grouping: CottList[U64]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "thousands_separator", _cott_validate_abi(self.thousands_separator, str, path="$.thousands_separator"))
        if not _cott_validated_construction():
            object.__setattr__(self, "decimal_point", _cott_validate_abi(self.decimal_point, str, path="$.decimal_point"))
        if not _cott_validated_construction():
            object.__setattr__(self, "grouping", _cott_validate_abi(self.grouping, CottList[U64], path="$.grouping"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridPosition:
    __hash__ = None
    row: U64
    column: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "row", _cott_validate_abi(self.row, U64, path="$.row"))
        if not _cott_validated_construction():
            object.__setattr__(self, "column", _cott_validate_abi(self.column, U64, path="$.column"))

"""The state of one results tab. cursor is the focused cell; anchor is the other
corner of the range selection (equal to cursor when only one cell is
selected). first_row and first_column are the scroll position: the first data
row and the first column drawn."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ResultsGrid:
    __hash__ = None
    result: ResultSet
    cursor: GridPosition
    anchor: GridPosition
    first_row: U64
    first_column: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "result", _cott_validate_abi(self.result, ResultSet, path="$.result"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, GridPosition, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "anchor", _cott_validate_abi(self.anchor, GridPosition, path="$.anchor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_row", _cott_validate_abi(self.first_row, U64, path="$.first_row"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_column", _cott_validate_abi(self.first_column, U64, path="$.first_column"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_Up:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_Down:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_Left:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_Right:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_RowStart:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_RowEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_ColumnStart:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_ColumnEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_NextCell:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_PreviousCell:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_PageUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_PageDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_TableStart:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_TableEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridMotion_SelectAll:
    pass

GridMotion: TypeAlias = Union[GridMotion_Up, GridMotion_Down, GridMotion_Left, GridMotion_Right, GridMotion_RowStart, GridMotion_RowEnd, GridMotion_ColumnStart, GridMotion_ColumnEnd, GridMotion_NextCell, GridMotion_PreviousCell, GridMotion_PageUp, GridMotion_PageDown, GridMotion_TableStart, GridMotion_TableEnd, GridMotion_SelectAll]

"""One drawn frame of a results grid, and the scroll position it was drawn at
(the caller stores it back into the grid)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GridFrame:
    __hash__ = None
    lines: CottList[StyledLine]
    first_row: U64
    first_column: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "lines", _cott_validate_abi(self.lines, CottList[StyledLine], path="$.lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_row", _cott_validate_abi(self.first_row, U64, path="$.first_row"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_column", _cott_validate_abi(self.first_column, U64, path="$.first_column"))

"""The full value under the cursor, for the View Cell dialog."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CellView:
    __hash__ = None
    column: str
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "column", _cott_validate_abi(self.column, str, path="$.column"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

"""Build a ResultSet from literal rows. Each row supplies one CellValue per
column, in column order (a row with fewer values is padded with Null, extra
values are ignored). Column Arrow types come from the first non-Null value of
each column (CellValue mapping above); an all-Null column is Arrow null type.
A value of another variant than the column's type is converted to its text
and the column becomes string. Column names are deduplicated like ArrowTable
documents, and the returned columns carry the deduplicated names with the
given type labels. fetched_row_count is rows.len, row_count is that capped by
viewer_max_rows when Some, truncated is false."""
"""The C locale's number format: thousands_separator "", decimal_point ".",
grouping empty."""
"""Localize a plain decimal number text such as "-1234567.25" or "1e+06":
group the digits of the integer part (after an optional leading "-") by
number_format.grouping from the right, joining groups with
thousands_separator (a grouping entry of 0 repeats the previous size; a size
of 127 or more stops further grouping), and replace the "." decimal point
with decimal_point. Exponent suffixes and fraction digits are unchanged."""
"""The one-line cell text for a literal CellValue, following Harlequin's
results table formatting:
Null -> "∅ null"; Boolean true -> "✓ True", false -> "X False";
Integer -> the decimal digits, localized with format_number_text unless
id_column; Real -> Python format(value, "g") localized with
format_number_text ("nan", "inf" and "-inf" stay as written); Text -> its
first line (up to the first CR or LF) followed by "…⏎" when more lines
follow; Blob -> repr() of its first 32 bytes, followed by " (+N bytes)" when
it has N more bytes."""
"""Whether a column holds identifiers, whose integers are printed without
digit grouping: the name matches the regular expression (\\b|_)id\\b
case-insensitively, or [a-z]I[dD]\\b case-sensitively."""
"""A results tab showing result with the cursor and anchor at row 0 column 0
and no scroll."""
"""Move the cursor like Harlequin's results table. With no rows or no columns
the grid is returned unchanged. Let last_row = row_count - 1 and last_column
= columns.len - 1.
Up/Down/Left/Right move one cell, stopping at the edges. RowStart and RowEnd
go to column 0 and last_column in the same row. ColumnStart and ColumnEnd go
to row 0 and last_row in the same column. NextCell moves right, wrapping to
column 0 of the next row, and stays put at the last cell; PreviousCell moves
left, wrapping to last_column of the previous row, and stays put at (0, 0).
PageUp and PageDown move max(page_rows, 1) rows, clamped. TableStart goes to
(0, 0) and TableEnd to (last_row, last_column). SelectAll puts the anchor at
(0, 0) and the cursor at (last_row, last_column) regardless of extend.
For every other motion, extend false moves the anchor with the cursor and
extend true leaves the anchor where it was, extending the range selection.
result, first_row and first_column are unchanged."""
"""Draw one frame of the results table into width x height character cells.
Values come from grid.result.data rows [first_row, ...) via pyarrow
(Table.slice(...).to_pylist()), limited to row_count.
Cell text of a Python value: None -> "∅ null"; bool -> "✓ True" / "X False";
int -> str(value) localized with format_number_text unless the column is an
id column (is_id_column(name)); float -> format(value, "g") localized;
decimal.Decimal -> format(value, "f") localized; datetime/time ->
isoformat(timespec="milliseconds") with a "+00:00" suffix written "Z";
date -> isoformat(); timedelta -> str(); str -> first line, plus "…⏎" when
more lines follow; bytes -> repr of the first 32 bytes plus " (+N bytes)"
when longer; anything else -> str() first line.
Right-aligned values: bool, int, float, Decimal, date, time, datetime,
timedelta. Everything else is left-aligned; null text is centered.
Widths are measured in terminal cells with wcwidth.wcswidth (a negative
result counts as len). Column header text is name + " " + type_label (just
name when type_label is ""). A column's content width is the widest of its
header text and the cell text of the first 1000 held rows, capped at
max(20, width // 2 - 2), and at least 1. Each column occupies content width
+ 2 cells: one space of padding on each side. Text wider than the content
width is cut to fit and ends with "…".
The row-label gutter shows 1-based row numbers right-aligned, one space of
padding on each side; its content width is the digit count of row_count
(at least 1).
Scroll: data_rows = height - 1. first_row is grid.first_row, moved minimally
so the cursor row is inside [first_row, first_row + data_rows); first_column
is grid.first_column, moved minimally so the cursor column is the first
column or ends within width. The returned frame carries these values.
Lines: the header line, then one line per held row from first_row, at most
data_rows lines. Every line is a list of spans: first the gutter span, then
one span per drawn column holding its padded text. Header spans (the gutter
is blank there) are styled "class:hq.header". A data cell's
style is "class:hq.cell", plus " class:hq.cell.null" for nulls or
" class:hq.cell.number" for numbers, plus " class:hq.selection" when it lies
in the rectangle spanned by anchor and cursor and that rectangle has more than
one cell, plus " class:hq.cursor" for the cursor cell when focused. Gutter
spans use "class:hq.rownumber". Columns are drawn from first_column while they
start within width; each line is cut at width cells. Nothing is drawn below
the last row. width or height of 0 draws no lines. A result with no columns
draws the single line "Query returned no columns" styled "class:hq.muted"."""
"""The Copy Selection text: the values in the rectangle spanned by anchor and
cursor, rows top to bottom, each row's values left to right joined by TAB,
rows joined by LF. A value is Python str() of the value pyarrow returns
(so SQL NULL is "None"). An empty result copies ""."""
"""The View Cell dialog content for the cursor: the column's name and the full
value text (every line; None -> "∅ null"; bytes -> repr of all bytes; other
values as render_grid formats them but without first-line truncation and
without localization). Nothing when the result has no rows or no columns."""
"""The results viewer's border title after a query, as Harlequin shows it,
with counts localized by format_number_text:
- row_count == 0 and fetched_row_count == 0: "Query Returned No Records";
- truncated: "Query Results (Showing {row_count} of >{fetched_row_count} Records)";
- row_count < fetched_row_count: "Query Results (Showing {row_count} of {fetched_row_count} Records)";
- otherwise "Query Results ({fetched_row_count} Records)"."""
__all__ = ["ArrowTable", "CellValue", "CellValue_Blob", "CellValue_Boolean", "CellValue_Integer", "CellValue_Null", "CellValue_Real", "CellValue_Text", "CellView", "ColumnInfo", "GridFrame", "GridMotion", "GridMotion_ColumnEnd", "GridMotion_ColumnStart", "GridMotion_Down", "GridMotion_Left", "GridMotion_NextCell", "GridMotion_PageDown", "GridMotion_PageUp", "GridMotion_PreviousCell", "GridMotion_Right", "GridMotion_RowEnd", "GridMotion_RowStart", "GridMotion_SelectAll", "GridMotion_TableEnd", "GridMotion_TableStart", "GridMotion_Up", "GridPosition", "NumberFormat", "ResultSet", "ResultsGrid"]
