from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.render_types import ExportFormat as ExportFormat, ExportFormat_Csv as ExportFormat_Csv, ExportFormat_Json as ExportFormat_Json, ExportFormat_Markdown as ExportFormat_Markdown, ExportFormat_Sql as ExportFormat_Sql, ExportFormat_Tsv as ExportFormat_Tsv, ExportRequest as ExportRequest, KeyBinding as KeyBinding, Keymap as Keymap, RenderError as RenderError, RenderError_DestinationDenied as RenderError_DestinationDenied, RenderError_ExportFailed as RenderError_ExportFailed, RenderError_InvalidWidth as RenderError_InvalidWidth, RenderError_UnsupportedCell as RenderError_UnsupportedCell, RenderLayout as RenderLayout, RenderLayout_Table as RenderLayout_Table, RenderLayout_Vertical as RenderLayout_Vertical, RenderOptions as RenderOptions, Theme as Theme
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult
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
width. Reject a NUL in a column name or Text cell as UnsupportedCell.
Keep only the first maximum_rows rows, preserving columns and order.
Use the render_table cell mapping, truncating every column/cell string to
maximum_cell_width Unicode code points before formatting. Table uses " | "
headers/rows; Vertical uses "Row N" and "column: value" lines.
Clip each resulting line to terminal_width code points without ellipsis.
Join with LF and no trailing LF. If output would be empty or whitespace only,
use "(no rows)" clipped to terminal_width so successful output is nonempty.
Do not replace real row rendering with a debug repr of the whole QueryResult."""
def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]: ...

"""This diagnostic view joins the standard generated CatalogRelation string
representation for each value with LF, preserving order. No trailing LF;
empty input returns "". No database access or extra records are introduced."""
def render_catalog_relations(relations: CottList[CatalogRelation]) -> str: ...

"""This diagnostic view joins the standard generated CatalogColumn string
representation for each value with LF, retaining all fields and input order.
No trailing LF; empty input returns "". It is not an inferred SQL declaration."""
def render_catalog_columns(columns: CottList[CatalogColumn]) -> str: ...

"""This diagnostic view joins the standard generated CatalogMatch string
representation for each value with LF, preserving order and all fields.
No trailing LF; empty input returns ""."""
def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str: ...

def bundled_themes() -> CottList[Theme]: ...

"""Return exactly two built-in keymaps, in this order. "default" contains
ctrl+enter -> execute, ctrl+s -> save, ctrl+q -> quit.
"vim" contains ctrl+enter -> execute, :w -> save, :q -> quit.
Preserve the listed binding order and exact spelling. These are this Cott
client's static defaults, not a runtime scan of upstream packages or plugins."""
def bundled_keymaps() -> CottList[Keymap]: ...

"""Return Some containing the first Theme whose name exactly equals name,
case-sensitively; return Nothing when there is no match. Do not clone or edit it."""
def resolve_theme(themes: CottList[Theme], name: str) -> Option[Theme]: ...

"""Return Some containing the first Keymap whose name exactly equals name,
case-sensitively; return Nothing when there is no match. Do not clone or edit it."""
def resolve_keymap(keymaps: CottList[Keymap], name: str) -> Option[Keymap]: ...

"""Match destination.location as FileLocation_Local/S3; serialize row.values; use boto3 Any."""
def export_result(request: ExportRequest) -> Result[Unit, RenderError]: ...

__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme", "bundled_keymaps", "bundled_themes", "export_result", "render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_result", "render_table", "render_vertical", "resolve_keymap", "resolve_theme"]
