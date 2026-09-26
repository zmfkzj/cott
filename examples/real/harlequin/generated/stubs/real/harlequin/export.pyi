from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.export_types import ExportDialog as ExportDialog, ExportError as ExportError, ExportError_InvalidOption as ExportError_InvalidOption, ExportError_PathIsDirectory as ExportError_PathIsDirectory, ExportError_UnknownFormat as ExportError_UnknownFormat, ExportError_WriteFailed as ExportError_WriteFailed, ExportFocus as ExportFocus, ExportFocus_Cancel as ExportFocus_Cancel, ExportFocus_Export as ExportFocus_Export, ExportFocus_Format as ExportFocus_Format, ExportFocus_Option as ExportFocus_Option, ExportFocus_Path as ExportFocus_Path, ExportFormatSpec as ExportFormatSpec, ExportOptionKind as ExportOptionKind, ExportOptionKind_Choice as ExportOptionKind_Choice, ExportOptionKind_Flag as ExportOptionKind_Flag, ExportOptionKind_Text as ExportOptionKind_Text, ExportOptionSpec as ExportOptionSpec, ExportOptionValue as ExportOptionValue, ExportOutcome as ExportOutcome, ExportOutcome_Cancel as ExportOutcome_Cancel, ExportOutcome_Export as ExportOutcome_Export, ExportOutcome_Stay as ExportOutcome_Stay, ExportReceipt as ExportReceipt, ExportRequest as ExportRequest, ExportStep as ExportStep
from real.harlequin.results_types import ResultSet
from real.harlequin.style_types import StyledLine
"""The formats the Data Exporter offers on Linux and macOS, in this order,
with these options (name | label | kind | default | notes); descriptions
are Harlequin's option help texts.
csv | CSV | extensions .csv .tsv
  header | Header | flag | true
  sep | Separator | text | ","
  compression | Compression | choice Auto=auto, gzip=gzip, zstd=zstd, No compression=none | auto
  quoting | Force Quote | flag | false
  date_format | Date Format | text | "" | placeholder %Y-%m-%d
  timestamp_format | Timestamp Format | text | "" | placeholder %c
  quotechar | Quote Char | text | '"'
  escapechar | Escape Char | text | '"'
  na_rep | Null String | text | ""
  encoding | Encoding | text | UTF8
parquet | Parquet | extensions .parquet .pq
  compression | Compression | choice Snappy=snappy, gzip=gzip, zstd=zstd, Uncompressed=uncompressed | snappy
json | JSON | extensions .json .js .ndjson
  array | Array | flag | false
  compression | Compression | choice Auto=auto, gzip=gzip, zstd=zstd, Uncompressed=uncompressed | auto
  date_format | Date Format | text | "" | placeholder %Y-%m-%d
  timestamp_format | Timestamp Format | text | "" | placeholder %c
orc | ORC | extensions .orc
  file_version | File Version | choice 0.11=0.11, 0.12=0.12 | 0.12
  batch_size | Batch Size | text | 1024 | integer
  stripe_size | Stripe Size | text | 67108864 | integer
  compression | Compression | choice Uncompressed=UNCOMPRESSED, Snappy=SNAPPY, zlib=ZLIB, LZ4=LZ4, zstd=zstd | UNCOMPRESSED
  compression_block_size | Compression Block Size | text | 65536 | integer
  compression_strategy | Compression Strategy | choice Speed=SPEED, Compression=COMPRESSION | SPEED
  row_index_stride | Row Index Stride | text | 10000 | integer
  padding_tolerance | Padding Tolerance | text | 0.0 | number
  dictionary_key_size_threshold | Dict Key Size Threshold | text | 0.0 | number
  bloom_filter_columns | Bloom Filter Columns | text | "" | comma-separated names
  bloom_filter_fpp | Bloom Filter False-Positive | text | 0.05 | number
feather | Feather | extensions .feather
  compression | Compression | choice Uncompressed=uncompressed, LZ4=lz4, zstd=zstd | uncompressed
  compression_level | Compression Level | text | "" | integer, empty allowed
  chunksize | Chunk Size | text | "" | integer, empty allowed
  version | File Version | choice 2=2, 1=1 | 2
Choice values are the text after "=", labels the text before it."""
def export_formats() -> CottList[ExportFormatSpec]: ...

"""The export format whose extensions include the path's suffix (the text from
the last "." of the last path component, compared exactly), for example
"out.tsv" -> Some("csv") and "x.pq" -> Some("parquet"); Nothing otherwise."""
def format_for_path(path: str) -> Option[str]: ...

"""The dialog as it opens: path is default_path (a directory, meaning a path
that ends with "/" or names no suffix, gets a trailing "/" added when it has
none), or "" when Nothing; path_cursor at the end of path; format inferred
with format_for_path, else Nothing; values the defaults of that format's
options; focus Path; message ""."""
def new_export_dialog(default_path: Option[str]) -> ExportDialog: ...

"""Apply one key (normalized Textual key name, with the printable text it
produced) to the Data Exporter.
- "escape": Cancel. "tab"/"shift+tab": move focus through Path, Format, each
  option of the selected format, Cancel, Export (wrapping).
- On Path: printable text inserts at path_cursor, "backspace"/"delete" edit,
  "left"/"right"/"home"/"end" move the caret; after each edit, when
  format_for_path(path) names a format different from the selected one, that
  format becomes selected and values reset to its defaults. "enter" behaves
  like pressing Export.
- On Format: "left"/"right" (or "enter") select the previous/next format of
  export_formats (wrapping; from Nothing, "right"/"enter" selects the first),
  resetting values to its defaults.
- On an option: a flag toggles with "enter" or "space"; a choice cycles with
  "left"/"right"/"enter"; text edits at the end of its value with printable
  text and "backspace".
- "enter" on Cancel: Cancel. "enter" on Export: validate. An empty path sets
  message "A file path is required." A path ending with "/" sets message
  "Path is not a file". No selected format sets message "Must select format.
  Supported formats: CSV, Parquet, JSON, ORC, Feather". An integer option
  whose value is not an int (empty allowed only when allow_empty) sets
  message "{label} must be a whole number."; a number option that is not a
  float sets "{label} must be a number.". Otherwise the outcome is
  Export(ExportRequest(path, format, values)) with path "~" expanded.
Outcomes are Stay unless stated. message is cleared by any edit."""
def export_dialog_key(dialog: ExportDialog, key: str, text: str) -> ExportStep: ...

"""Draw the Data Exporter body: the title "Data Exporter" (class:hq.dialog.title),
"Export the results of your query to a file." (class:hq.text), the path line
showing the path or the placeholder "/path/to/file  (tab autocompletes, enter
exports, esc cancels)" (class:hq.muted when empty), the message line
(class:hq.error) when not "", "Format: " and the selected format label or
"Select a format", one line per option "{label}: {value}" (flags as "[x]" or
"[ ]", choices as their label), and the buttons line "[ Cancel ]  [ Export ]".
The focused element's value span carries class:hq.cursor (buttons use
class:hq.button.focused, unfocused class:hq.button). Lines are cut at width."""
def render_export_dialog(dialog: ExportDialog, width: U64) -> CottList[StyledLine]: ...

"""Write every fetched row of result_set (result_set.data, not capped by the viewer)
to request.path as Harlequin's exporter does, creating missing parent
directories. Column names that repeat are renamed (a, a0, a1, ...). Options
with an empty value are not passed; "true"/"false" become booleans.
csv: duckdb.from_arrow(data).write_csv(file_name, header=True unless header
is false, sep, compression, quotechar, escapechar, na_rep, encoding,
date_format, timestamp_format; quoting true means quoting="ALL").
tsv: csv with sep "\\t" unless given. json: duckdb COPY (select * from data)
TO path (FORMAT JSON[, ARRAY TRUE when array is true][, COMPRESSION ...]
[, DATEFORMAT ...][, TIMESTAMPFORMAT ...]) with bound values; jsonl and
ndjson are json with array false. parquet: write_parquet(file_name,
compression). orc: pyarrow.orc.write_table with the integer/float options
converted and bloom_filter_columns split on commas. feather and arrow:
pyarrow.feather.write_feather with compression ("uncompressed" is None for
version 1), compression_level, chunksize and version as integers.
A zero-row result set writes a header-only or empty file. An unknown format is
UnknownFormat(name); an existing directory at path is PathIsDirectory(path);
an unparsable option is InvalidOption(name, message); a writer failure is
WriteFailed(title, message) with Harlequin's title ("DuckDB raised an error
when writing your query to a CSV file.", "... to a JSON file.",
"... to a Parquet file.", "Arrow raised an error when writing your data to
an ORC file." or "... to a Feather file.") and the error text."""
def write_result(result_set: ResultSet, request: ExportRequest) -> Result[ExportReceipt, ExportError]: ...

__all__ = ["ExportDialog", "ExportError", "ExportError_InvalidOption", "ExportError_PathIsDirectory", "ExportError_UnknownFormat", "ExportError_WriteFailed", "ExportFocus", "ExportFocus_Cancel", "ExportFocus_Export", "ExportFocus_Format", "ExportFocus_Option", "ExportFocus_Path", "ExportFormatSpec", "ExportOptionKind", "ExportOptionKind_Choice", "ExportOptionKind_Flag", "ExportOptionKind_Text", "ExportOptionSpec", "ExportOptionValue", "ExportOutcome", "ExportOutcome_Cancel", "ExportOutcome_Export", "ExportOutcome_Stay", "ExportReceipt", "ExportRequest", "ExportStep", "export_dialog_key", "export_formats", "format_for_path", "new_export_dialog", "render_export_dialog", "write_result"]
