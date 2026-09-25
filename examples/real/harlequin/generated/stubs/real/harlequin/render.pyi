from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.render_types import ExportFormat as ExportFormat, ExportFormat_Csv as ExportFormat_Csv, ExportFormat_Json as ExportFormat_Json, ExportFormat_Markdown as ExportFormat_Markdown, ExportFormat_Sql as ExportFormat_Sql, ExportFormat_Tsv as ExportFormat_Tsv, ExportRequest as ExportRequest, KeyBinding as KeyBinding, Keymap as Keymap, RenderError as RenderError, RenderError_DestinationDenied as RenderError_DestinationDenied, RenderError_ExportFailed as RenderError_ExportFailed, RenderError_InvalidWidth as RenderError_InvalidWidth, RenderError_UnsupportedCell as RenderError_UnsupportedCell, RenderLayout as RenderLayout, RenderLayout_Table as RenderLayout_Table, RenderLayout_Vertical as RenderLayout_Vertical, RenderOptions as RenderOptions, Theme as Theme
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult, SavedFile
"""Format Cell.Null as NULL, Integer/Real as str(value), Text as its stored text,
and Blob as lowercase hexadecimal. Emit a header joined by " | " when columns
is nonempty, then one similarly joined line for each row in input order.
Join lines with LF without a trailing LF. No columns and no rows returns "".
This function applies no row or width limit."""
def render_table(result: QueryResult) -> str: ...

"""For each row, starting at one, emit "Row N" followed by "column: value" lines
for paired columns and values. Use the same cell text mapping as render_table.
Preserve order, join with LF without a trailing LF; no rows returns "".
Pair only the common length if columns and values differ."""
def render_vertical(result: QueryResult) -> str: ...

"""terminal_width or maximum_cell_width zero returns InvalidWidth with that zero
width. Keep only the first maximum_rows rows, preserving columns and order.
A NUL in a column name or in a Text cell of a kept row is UnsupportedCell.
Use the render_table cell mapping, truncating every column/cell string to
maximum_cell_width Unicode code points before formatting. Table uses " | "
headers/rows; Vertical uses "Row N" and "column: value" lines.
Clip each resulting line to terminal_width code points without ellipsis.
Join with LF and no trailing LF. If output would be empty or whitespace only,
use "(no rows)" clipped to terminal_width so successful output is nonempty."""
def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]: ...

"""One line per relation in input order: "table NAME" or "view NAME". Stored SQL is
not shown. Lines are joined with LF without a trailing LF; empty input is ""."""
def render_catalog_relations(relations: CottList[CatalogRelation]) -> str: ...

"""One line per column in input order: RELATION.NAME, then " " and declared_type
when it is nonempty, " NOT NULL" when not_null, " DEFAULT " and default_sql when
present, and " PRIMARY KEY " followed by primary_key_position when it is nonzero.
ordinal is not shown. Lines are joined with LF without a trailing LF; empty input
is ""."""
def render_catalog_columns(columns: CottList[CatalogColumn]) -> str: ...

"""One line per match in input order: "relation NAME" for a Relation match and
"column RELATION.NAME" for a Column match. Lines are joined with LF without a
trailing LF; empty input is ""."""
def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str: ...

"""Return exactly these built-in themes, in this order, as
name | foreground | background | accent:
harlequin | #DDDDDD | #0C0C0C | #FEFFAC
monokai | #F8F8F2 | #272822 | #F92672
dracula | #F8F8F2 | #282A36 | #BD93F9
nord | #D8DEE9 | #2E3440 | #88C0D0"""
def bundled_themes() -> CottList[Theme]: ...

"""Return exactly two built-in keymaps, in this order. "default" contains
ctrl+enter -> execute, ctrl+s -> save, ctrl+q -> quit.
"vim" contains ctrl+enter -> execute, :w -> save, :q -> quit.
Preserve the listed binding order and exact spelling. These are this Cott
client's static defaults, not a runtime scan of upstream packages or plugins."""
def bundled_keymaps() -> CottList[Keymap]: ...

"""Return Some containing the first Theme whose name exactly equals name,
case-sensitively; return Nothing when there is no match."""
def resolve_theme(themes: CottList[Theme], name: str) -> Option[Theme]: ...

"""Return Some containing the first Keymap whose name exactly equals name,
case-sensitively; return Nothing when there is no match."""
def resolve_keymap(keymaps: CottList[Keymap], name: str) -> Option[Keymap]: ...

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
def export_result(request: ExportRequest) -> Result[SavedFile, RenderError]: ...

__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme", "bundled_keymaps", "bundled_themes", "export_result", "render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_result", "render_table", "render_vertical", "resolve_keymap", "resolve_theme"]
