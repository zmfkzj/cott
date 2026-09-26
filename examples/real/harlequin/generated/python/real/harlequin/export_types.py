from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.results_types import ResultSet
from real.harlequin.style_types import StyledLine

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOptionKind_Flag:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOptionKind_Text:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOptionKind_Choice:
    __hash__ = None
    values: CottList[str]
    labels: CottList[str]

ExportOptionKind: TypeAlias = Union[ExportOptionKind_Flag, ExportOptionKind_Text, ExportOptionKind_Choice]

"""One option the Data Exporter shows for a format. default is the initial value
as text ("true"/"false" for flags, "" for none). integer and number mark text
options validated as an integer or a floating-point number (empty allowed when
allow_empty)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOptionSpec:
    __hash__ = None
    name: str
    label: str
    description: str
    kind: ExportOptionKind
    default: str
    placeholder: str
    integer: bool
    number: bool
    allow_empty: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, str, path="$.label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "description", _cott_validate_abi(self.description, str, path="$.description"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, ExportOptionKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default", _cott_validate_abi(self.default, str, path="$.default"))
        if not _cott_validated_construction():
            object.__setattr__(self, "placeholder", _cott_validate_abi(self.placeholder, str, path="$.placeholder"))
        if not _cott_validated_construction():
            object.__setattr__(self, "integer", _cott_validate_abi(self.integer, bool, path="$.integer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "number", _cott_validate_abi(self.number, bool, path="$.number"))
        if not _cott_validated_construction():
            object.__setattr__(self, "allow_empty", _cott_validate_abi(self.allow_empty, bool, path="$.allow_empty"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormatSpec:
    __hash__ = None
    name: str
    label: str
    extensions: CottList[str]
    options: CottList[ExportOptionSpec]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, str, path="$.label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "extensions", _cott_validate_abi(self.extensions, CottList[str], path="$.extensions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, CottList[ExportOptionSpec], path="$.options"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOptionValue:
    __hash__ = None
    name: str
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

"""A complete export request: destination path (after ~ expansion), a format
name accepted by write_result ("csv", "tsv", "json", "jsonl", "ndjson",
"parquet", "orc", "feather", "arrow") and option values keyed by option name."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRequest:
    __hash__ = None
    path: Path
    format: str
    options: CottList[ExportOptionValue]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, str, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, CottList[ExportOptionValue], path="$.options"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportReceipt:
    __hash__ = None
    path: Path
    rows: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, U64, path="$.rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportError_UnknownFormat:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportError_InvalidOption:
    __hash__ = None
    name: str
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportError_PathIsDirectory:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportError_WriteFailed:
    __hash__ = None
    title: str
    message: str

ExportError: TypeAlias = Union[ExportError_UnknownFormat, ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_WriteFailed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFocus_Path:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFocus_Format:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFocus_Option:
    __hash__ = None
    index: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFocus_Cancel:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFocus_Export:
    pass

ExportFocus: TypeAlias = Union[ExportFocus_Path, ExportFocus_Format, ExportFocus_Option, ExportFocus_Cancel, ExportFocus_Export]

"""The Data Exporter dialog (Ctrl+E). format is the selected entry of
export_formats (Nothing until chosen or inferred from the path extension);
values holds the current value of every option of the selected format;
path_cursor is the caret in path; message is the validation text shown under
the path ("" for none)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportDialog:
    __hash__ = None
    path: str
    path_cursor: U64
    format: Option[str]
    values: CottList[ExportOptionValue]
    focus: ExportFocus
    message: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path_cursor", _cott_validate_abi(self.path_cursor, U64, path="$.path_cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, Option[str], path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "values", _cott_validate_abi(self.values, CottList[ExportOptionValue], path="$.values"))
        if not _cott_validated_construction():
            object.__setattr__(self, "focus", _cott_validate_abi(self.focus, ExportFocus, path="$.focus"))
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOutcome_Stay:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOutcome_Cancel:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportOutcome_Export:
    __hash__ = None
    request: ExportRequest

ExportOutcome: TypeAlias = Union[ExportOutcome_Stay, ExportOutcome_Cancel, ExportOutcome_Export]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportStep:
    __hash__ = None
    dialog: ExportDialog
    outcome: ExportOutcome

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "dialog", _cott_validate_abi(self.dialog, ExportDialog, path="$.dialog"))
        if not _cott_validated_construction():
            object.__setattr__(self, "outcome", _cott_validate_abi(self.outcome, ExportOutcome, path="$.outcome"))

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
"""The export format whose extensions include the path's suffix (the text from
the last "." of the last path component, compared exactly), for example
"out.tsv" -> Some("csv") and "x.pq" -> Some("parquet"); Nothing otherwise."""
"""The dialog as it opens: path is default_path (a directory, meaning a path
that ends with "/" or names no suffix, gets a trailing "/" added when it has
none), or "" when Nothing; path_cursor at the end of path; format inferred
with format_for_path, else Nothing; values the defaults of that format's
options; focus Path; message ""."""
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
"""Draw the Data Exporter body: the title "Data Exporter" (class:hq.dialog.title),
"Export the results of your query to a file." (class:hq.text), the path line
showing the path or the placeholder "/path/to/file  (tab autocompletes, enter
exports, esc cancels)" (class:hq.muted when empty), the message line
(class:hq.error) when not "", "Format: " and the selected format label or
"Select a format", one line per option "{label}: {value}" (flags as "[x]" or
"[ ]", choices as their label), and the buttons line "[ Cancel ]  [ Export ]".
The focused element's value span carries class:hq.cursor (buttons use
class:hq.button.focused, unfocused class:hq.button). Lines are cut at width."""
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
__all__ = ["ExportDialog", "ExportError", "ExportError_InvalidOption", "ExportError_PathIsDirectory", "ExportError_UnknownFormat", "ExportError_WriteFailed", "ExportFocus", "ExportFocus_Cancel", "ExportFocus_Export", "ExportFocus_Format", "ExportFocus_Option", "ExportFocus_Path", "ExportFormatSpec", "ExportOptionKind", "ExportOptionKind_Choice", "ExportOptionKind_Flag", "ExportOptionKind_Text", "ExportOptionSpec", "ExportOptionValue", "ExportOutcome", "ExportOutcome_Cancel", "ExportOutcome_Export", "ExportOutcome_Stay", "ExportReceipt", "ExportRequest", "ExportStep"]
