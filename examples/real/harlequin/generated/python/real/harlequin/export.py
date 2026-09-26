from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.export_types import ExportDialog, ExportError, ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_UnknownFormat, ExportError_WriteFailed, ExportFocus, ExportFocus_Cancel, ExportFocus_Export, ExportFocus_Format, ExportFocus_Option, ExportFocus_Path, ExportFormatSpec, ExportOptionKind, ExportOptionKind_Choice, ExportOptionKind_Flag, ExportOptionKind_Text, ExportOptionSpec, ExportOptionValue, ExportOutcome, ExportOutcome_Cancel, ExportOutcome_Export, ExportOutcome_Stay, ExportReceipt, ExportRequest, ExportStep
from real.harlequin.results_types import ResultSet
from real.harlequin.style_types import StyledLine

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def export_formats() -> CottList[ExportFormatSpec]:
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
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/export/export_formats.py", "f8124f8ebe987777eb8ecdceec9a5e03b7209909957c5d8eccc57655fca81f86", "export_formats", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.export.export_formats")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.export.export_formats"
        if _error.span is None:
            _error.span = {"end_byte":4770,"end_column":1,"end_line":136,"start_byte":2102,"start_column":1,"start_line":89}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.export.export_formats", phase="implementation-call", span={"end_byte":4770,"end_column":1,"end_line":136,"start_byte":2102,"start_column":1,"start_line":89}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.export.export_formats", phase="implementation-call", span={"end_byte":4770,"end_column":1,"end_line":136,"start_byte":2102,"start_column":1,"start_line":89}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ExportFormatSpec], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 5)), "real.harlequin.export.export_formats", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.export.export_formats", clause="ensures:1", phase="ensures", span={"end_byte":4752,"end_column":28,"end_line":132,"start_byte":4729,"start_column":5,"start_line":132}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[ExportFormatSpec], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def format_for_path(path: str) -> Option[str]:
    """The export format whose extensions include the path's suffix (the text from
the last "." of the last path component, compared exactly), for example
"out.tsv" -> Some("csv") and "x.pq" -> Some("parquet"); Nothing otherwise."""
    path = _cott_normalize_f32_abi(path, str, path="$.path")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/export/format_for_path.py", "27e4e6f0ec522ff96ebe53c57c4f4eb7ee4300edb0fd0ca9dde7df8e192d0e13", "format_for_path", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.export.format_for_path")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.export.format_for_path"
        if _error.span is None:
            _error.span = {"end_byte":5088,"end_column":1,"end_line":145,"start_byte":4770,"start_column":1,"start_line":136}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.export.format_for_path", phase="implementation-call", span={"end_byte":5088,"end_column":1,"end_line":145,"start_byte":4770,"start_column":1,"start_line":136}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.export.format_for_path", phase="implementation-call", span={"end_byte":5088,"end_column":1,"end_line":145,"start_byte":4770,"start_column":1,"start_line":136}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def new_export_dialog(default_path: Option[str]) -> ExportDialog:
    """The dialog as it opens: path is default_path (a directory, meaning a path
that ends with "/" or names no suffix, gets a trailing "/" added when it has
none), or "" when Nothing; path_cursor at the end of path; format inferred
with format_for_path, else Nothing; values the defaults of that format's
options; focus Path; message ""."""
    default_path = _cott_normalize_f32_abi(default_path, Option[str], path="$.default_path")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/export/new_export_dialog.py", "4cb0a8d9aaf75760cbc5ce317abf817511f07bbbe829d5d3a39bc06aacce546d", "new_export_dialog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.export.new_export_dialog")
        _result = _implementation(default_path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.export.new_export_dialog"
        if _error.span is None:
            _error.span = {"end_byte":5621,"end_column":1,"end_line":159,"start_byte":5088,"start_column":1,"start_line":145}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.export.new_export_dialog", phase="implementation-call", span={"end_byte":5621,"end_column":1,"end_line":159,"start_byte":5088,"start_column":1,"start_line":145}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.export.new_export_dialog", phase="implementation-call", span={"end_byte":5621,"end_column":1,"end_line":159,"start_byte":5088,"start_column":1,"start_line":145}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ExportDialog, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).focus == ExportFocus_Path())), "real.harlequin.export.new_export_dialog", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.export.new_export_dialog", clause="ensures:1", phase="ensures", span={"end_byte":5570,"end_column":45,"end_line":154,"start_byte":5530,"start_column":5,"start_line":154}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).message == "")), "real.harlequin.export.new_export_dialog", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.export.new_export_dialog", clause="ensures:2", phase="ensures", span={"end_byte":5603,"end_column":33,"end_line":155,"start_byte":5575,"start_column":5,"start_line":155}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ExportDialog, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def export_dialog_key(dialog: ExportDialog, key: str, text: str) -> ExportStep:
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
    dialog = _cott_normalize_f32_abi(dialog, ExportDialog, path="$.dialog")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/export/export_dialog_key.py", "dd4760454694ed147af733657742805e0f2f995ebfa9a9b01a4ea1eb56b8aa50", "export_dialog_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.export.export_dialog_key")
        _result = _implementation(dialog, key, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.export.export_dialog_key"
        if _error.span is None:
            _error.span = {"end_byte":7411,"end_column":1,"end_line":189,"start_byte":5621,"start_column":1,"start_line":159}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.export.export_dialog_key", phase="implementation-call", span={"end_byte":7411,"end_column":1,"end_line":189,"start_byte":5621,"start_column":1,"start_line":159}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.export.export_dialog_key", phase="implementation-call", span={"end_byte":7411,"end_column":1,"end_line":189,"start_byte":5621,"start_column":1,"start_line":159}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ExportStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, ExportStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_export_dialog(dialog: ExportDialog, width: U64) -> CottList[StyledLine]:
    """Draw the Data Exporter body: the title "Data Exporter" (class:hq.dialog.title),
"Export the results of your query to a file." (class:hq.text), the path line
showing the path or the placeholder "/path/to/file  (tab autocompletes, enter
exports, esc cancels)" (class:hq.muted when empty), the message line
(class:hq.error) when not "", "Format: " and the selected format label or
"Select a format", one line per option "{label}: {value}" (flags as "[x]" or
"[ ]", choices as their label), and the buttons line "[ Cancel ]  [ Export ]".
The focused element's value span carries class:hq.cursor (buttons use
class:hq.button.focused, unfocused class:hq.button). Lines are cut at width."""
    dialog = _cott_normalize_f32_abi(dialog, ExportDialog, path="$.dialog")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/export/render_export_dialog.py", "7946c211f2406c0d186b46251ef468f3dc5156c0bee94be884ebbd4419851396", "render_export_dialog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.export.render_export_dialog")
        _result = _implementation(dialog, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.export.render_export_dialog"
        if _error.span is None:
            _error.span = {"end_byte":8244,"end_column":1,"end_line":204,"start_byte":7411,"start_column":1,"start_line":189}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.export.render_export_dialog", phase="implementation-call", span={"end_byte":8244,"end_column":1,"end_line":204,"start_byte":7411,"start_column":1,"start_line":189}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.export.render_export_dialog", phase="implementation-call", span={"end_byte":8244,"end_column":1,"end_line":204,"start_byte":7411,"start_column":1,"start_line":189}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def write_result(result_set: ResultSet, request: ExportRequest) -> Result[ExportReceipt, ExportError]:
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
    result_set = _cott_normalize_f32_abi(result_set, ResultSet, path="$.result_set")
    request = _cott_normalize_f32_abi(request, ExportRequest, path="$.request")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/export/write_result.py", "1a4d0f44a52f7ae83f694fd09cb2181d0c6545f3bdd3e76fd950816c08386a99", "write_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.export.write_result")
        _result = _implementation(result_set, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.export.write_result"
        if _error.span is None:
            _error.span = {"end_byte":10340,"end_column":1,"end_line":239,"start_byte":8244,"start_column":1,"start_line":204}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.export.write_result", phase="implementation-call", span={"end_byte":10340,"end_column":1,"end_line":239,"start_byte":8244,"start_column":1,"start_line":204}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.export.write_result", phase="implementation-call", span={"end_byte":10340,"end_column":1,"end_line":239,"start_byte":8244,"start_column":1,"start_line":204}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[ExportReceipt, ExportError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.export.write_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ExportError_UnknownFormat, ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_WriteFailed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.export.write_result", phase="error", span={"end_byte":10340,"end_column":1,"end_line":239,"start_byte":8244,"start_column":1,"start_line":204}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.export.write_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.export.write_result", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ExportError_UnknownFormat:
            _cott_contract_condition(True, "real.harlequin.export.write_result", "error:2")
        if type(_result) is Err and type(_result.error) is ExportError_InvalidOption:
            _cott_contract_condition(True, "real.harlequin.export.write_result", "error:3")
        if type(_result) is Err and type(_result.error) is ExportError_PathIsDirectory:
            _cott_contract_condition(True, "real.harlequin.export.write_result", "error:4")
        if type(_result) is Err and type(_result.error) is ExportError_WriteFailed:
            _cott_contract_condition(True, "real.harlequin.export.write_result", "error:5")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                receipt = _cott_match_value.value
                return (_cott_contract_condition(((((receipt).path == (request).path) and ((receipt).rows == (result_set).fetched_row_count))), "real.harlequin.export.write_result", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.export.write_result", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.export.write_result", clause="ensures:1", phase="ensures", span={"end_byte":10156,"end_column":112,"end_line":230,"start_byte":10049,"start_column":5,"start_line":230}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExportReceipt, ExportError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["ExportDialog", "ExportError", "ExportError_InvalidOption", "ExportError_PathIsDirectory", "ExportError_UnknownFormat", "ExportError_WriteFailed", "ExportFocus", "ExportFocus_Cancel", "ExportFocus_Export", "ExportFocus_Format", "ExportFocus_Option", "ExportFocus_Path", "ExportFormatSpec", "ExportOptionKind", "ExportOptionKind_Choice", "ExportOptionKind_Flag", "ExportOptionKind_Text", "ExportOptionSpec", "ExportOptionValue", "ExportOutcome", "ExportOutcome_Cancel", "ExportOutcome_Export", "ExportOutcome_Stay", "ExportReceipt", "ExportRequest", "ExportStep", "export_dialog_key", "export_formats", "format_for_path", "new_export_dialog", "render_export_dialog", "write_result"]
