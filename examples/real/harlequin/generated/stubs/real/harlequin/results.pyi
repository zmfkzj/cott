from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.results_types import ArrowTable as ArrowTable, CellValue as CellValue, CellValue_Blob as CellValue_Blob, CellValue_Boolean as CellValue_Boolean, CellValue_Integer as CellValue_Integer, CellValue_Null as CellValue_Null, CellValue_Real as CellValue_Real, CellValue_Text as CellValue_Text, CellView as CellView, ColumnInfo as ColumnInfo, GridFrame as GridFrame, GridMotion as GridMotion, GridMotion_ColumnEnd as GridMotion_ColumnEnd, GridMotion_ColumnStart as GridMotion_ColumnStart, GridMotion_Down as GridMotion_Down, GridMotion_Left as GridMotion_Left, GridMotion_NextCell as GridMotion_NextCell, GridMotion_PageDown as GridMotion_PageDown, GridMotion_PageUp as GridMotion_PageUp, GridMotion_PreviousCell as GridMotion_PreviousCell, GridMotion_Right as GridMotion_Right, GridMotion_RowEnd as GridMotion_RowEnd, GridMotion_RowStart as GridMotion_RowStart, GridMotion_SelectAll as GridMotion_SelectAll, GridMotion_TableEnd as GridMotion_TableEnd, GridMotion_TableStart as GridMotion_TableStart, GridMotion_Up as GridMotion_Up, GridPosition as GridPosition, NumberFormat as NumberFormat, ResultSet as ResultSet, ResultsGrid as ResultsGrid
from real.harlequin.style_types import StyledLine
"""Build a ResultSet from literal rows. Each row supplies one CellValue per
column, in column order (a row with fewer values is padded with Null, extra
values are ignored). Column Arrow types come from the first non-Null value of
each column (CellValue mapping above); an all-Null column is Arrow null type.
A value of another variant than the column's type is converted to its text
and the column becomes string. Column names are deduplicated like ArrowTable
documents, and the returned columns carry the deduplicated names with the
given type labels. fetched_row_count is rows.len, row_count is that capped by
viewer_max_rows when Some, truncated is false."""
def result_set_from_rows(statement: str, columns: CottList[ColumnInfo], rows: CottList[CottList[CellValue]], viewer_max_rows: Option[U64], elapsed_ms: U64) -> ResultSet: ...

"""The C locale's number format: thousands_separator "", decimal_point ".",
grouping empty."""
def default_number_format() -> NumberFormat: ...

"""Localize a plain decimal number text such as "-1234567.25" or "1e+06":
group the digits of the integer part (after an optional leading "-") by
number_format.grouping from the right, joining groups with
thousands_separator (a grouping entry of 0 repeats the previous size; a size
of 127 or more stops further grouping), and replace the "." decimal point
with decimal_point. Exponent suffixes and fraction digits are unchanged."""
def format_number_text(digits: str, number_format: NumberFormat) -> str: ...

"""The one-line cell text for a literal CellValue, following Harlequin's
results table formatting:
Null -> "∅ null"; Boolean true -> "✓ True", false -> "X False";
Integer -> the decimal digits, localized with format_number_text unless
id_column; Real -> Python format(value, "g") localized with
format_number_text ("nan", "inf" and "-inf" stay as written); Text -> its
first line (up to the first CR or LF) followed by "…⏎" when more lines
follow; Blob -> repr() of its first 32 bytes, followed by " (+N bytes)" when
it has N more bytes."""
def display_value_text(value: CellValue, number_format: NumberFormat, id_column: bool) -> str: ...

"""Whether a column holds identifiers, whose integers are printed without
digit grouping: the name matches the regular expression (\\b|_)id\\b
case-insensitively, or [a-z]I[dD]\\b case-sensitively."""
def is_id_column(name: str) -> bool: ...

"""A results tab showing result with the cursor and anchor at row 0 column 0
and no scroll."""
def new_grid(result: ResultSet) -> ResultsGrid: ...

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
def move_grid(grid: ResultsGrid, motion: GridMotion, extend: bool, page_rows: U64) -> ResultsGrid: ...

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
def render_grid(grid: ResultsGrid, width: U64, height: U64, focused: bool, number_format: NumberFormat) -> GridFrame: ...

"""The Copy Selection text: the values in the rectangle spanned by anchor and
cursor, rows top to bottom, each row's values left to right joined by TAB,
rows joined by LF. A value is Python str() of the value pyarrow returns
(so SQL NULL is "None"). An empty result copies ""."""
def selection_text(grid: ResultsGrid) -> str: ...

"""The View Cell dialog content for the cursor: the column's name and the full
value text (every line; None -> "∅ null"; bytes -> repr of all bytes; other
values as render_grid formats them but without first-line truncation and
without localization). Nothing when the result has no rows or no columns."""
def cursor_cell(grid: ResultsGrid) -> Option[CellView]: ...

"""The results viewer's border title after a query, as Harlequin shows it,
with counts localized by format_number_text:
- row_count == 0 and fetched_row_count == 0: "Query Returned No Records";
- truncated: "Query Results (Showing {row_count} of >{fetched_row_count} Records)";
- row_count < fetched_row_count: "Query Results (Showing {row_count} of {fetched_row_count} Records)";
- otherwise "Query Results ({fetched_row_count} Records)"."""
def results_title(result: ResultSet, number_format: NumberFormat) -> str: ...

__all__ = ["ArrowTable", "CellValue", "CellValue_Blob", "CellValue_Boolean", "CellValue_Integer", "CellValue_Null", "CellValue_Real", "CellValue_Text", "CellView", "ColumnInfo", "GridFrame", "GridMotion", "GridMotion_ColumnEnd", "GridMotion_ColumnStart", "GridMotion_Down", "GridMotion_Left", "GridMotion_NextCell", "GridMotion_PageDown", "GridMotion_PageUp", "GridMotion_PreviousCell", "GridMotion_Right", "GridMotion_RowEnd", "GridMotion_RowStart", "GridMotion_SelectAll", "GridMotion_TableEnd", "GridMotion_TableStart", "GridMotion_Up", "GridPosition", "NumberFormat", "ResultSet", "ResultsGrid", "cursor_cell", "default_number_format", "display_value_text", "format_number_text", "is_id_column", "move_grid", "new_grid", "render_grid", "result_set_from_rows", "results_title", "selection_text"]
