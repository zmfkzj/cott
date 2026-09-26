from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.results_types import ArrowTable, CellValue, CellValue_Blob, CellValue_Boolean, CellValue_Integer, CellValue_Null, CellValue_Real, CellValue_Text, CellView, ColumnInfo, GridFrame, GridMotion, GridMotion_ColumnEnd, GridMotion_ColumnStart, GridMotion_Down, GridMotion_Left, GridMotion_NextCell, GridMotion_PageDown, GridMotion_PageUp, GridMotion_PreviousCell, GridMotion_Right, GridMotion_RowEnd, GridMotion_RowStart, GridMotion_SelectAll, GridMotion_TableEnd, GridMotion_TableStart, GridMotion_Up, GridPosition, NumberFormat, ResultSet, ResultsGrid
from real.harlequin.style_types import StyledLine

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def result_set_from_rows(statement: str, columns: CottList[ColumnInfo], rows: CottList[CottList[CellValue]], viewer_max_rows: Option[U64], elapsed_ms: U64) -> ResultSet:
    """Build a ResultSet from literal rows. Each row supplies one CellValue per
column, in column order (a row with fewer values is padded with Null, extra
values are ignored). Column Arrow types come from the first non-Null value of
each column (CellValue mapping above); an all-Null column is Arrow null type.
A value of another variant than the column's type is converted to its text
and the column becomes string. Column names are deduplicated like ArrowTable
documents, and the returned columns carry the deduplicated names with the
given type labels. fetched_row_count is rows.len, row_count is that capped by
viewer_max_rows when Some, truncated is false."""
    statement = _cott_normalize_f32_abi(statement, str, path="$.statement")
    columns = _cott_normalize_f32_abi(columns, CottList[ColumnInfo], path="$.columns")
    rows = _cott_normalize_f32_abi(rows, CottList[CottList[CellValue]], path="$.rows")
    viewer_max_rows = _cott_normalize_f32_abi(viewer_max_rows, Option[U64], path="$.viewer_max_rows")
    elapsed_ms = _cott_normalize_f32_abi(elapsed_ms, U64, path="$.elapsed_ms")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/result_set_from_rows.py", "2931303c47935ca752e60814dee53bf4a0c97e2ce0ef0b5690889cb5af665369", "result_set_from_rows", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.result_set_from_rows")
        _result = _implementation(statement, columns, rows, viewer_max_rows, elapsed_ms)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.result_set_from_rows"
        if _error.span is None:
            _error.span = {"end_byte":4670,"end_column":1,"end_line":149,"start_byte":3546,"start_column":1,"start_line":122}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.result_set_from_rows", phase="implementation-call", span={"end_byte":4670,"end_column":1,"end_line":149,"start_byte":3546,"start_column":1,"start_line":122}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.result_set_from_rows", phase="implementation-call", span={"end_byte":4670,"end_column":1,"end_line":149,"start_byte":3546,"start_column":1,"start_line":122}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ResultSet, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).statement == statement)), "real.harlequin.results.result_set_from_rows", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.result_set_from_rows", clause="ensures:1", phase="ensures", span={"end_byte":4480,"end_column":42,"end_line":141,"start_byte":4443,"start_column":5,"start_line":141}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((_result).columns) == len(columns))), "real.harlequin.results.result_set_from_rows", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.result_set_from_rows", clause="ensures:2", phase="ensures", span={"end_byte":4526,"end_column":46,"end_line":142,"start_byte":4485,"start_column":5,"start_line":142}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).fetched_row_count == len(rows))), "real.harlequin.results.result_set_from_rows", "ensures:3")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.result_set_from_rows", clause="ensures:3", phase="ensures", span={"end_byte":4575,"end_column":49,"end_line":143,"start_byte":4531,"start_column":5,"start_line":143}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).elapsed_ms == elapsed_ms)), "real.harlequin.results.result_set_from_rows", "ensures:4")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.result_set_from_rows", clause="ensures:4", phase="ensures", span={"end_byte":4619,"end_column":44,"end_line":144,"start_byte":4580,"start_column":5,"start_line":144}, expected="true", actual="false")
        if not (_cott_contract_condition(((not (_result).truncated)), "real.harlequin.results.result_set_from_rows", "ensures:5")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.result_set_from_rows", clause="ensures:5", phase="ensures", span={"end_byte":4652,"end_column":33,"end_line":145,"start_byte":4624,"start_column":5,"start_line":145}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ResultSet, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def default_number_format() -> NumberFormat:
    """The C locale's number format: thousands_separator "", decimal_point ".",
grouping empty."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/default_number_format.py", "9bcdfe8c458643a723dfbf838381ae758f71bf6288fa27de4ae68a6924700021", "default_number_format", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.default_number_format")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.default_number_format"
        if _error.span is None:
            _error.span = {"end_byte":4926,"end_column":1,"end_line":160,"start_byte":4670,"start_column":1,"start_line":149}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.default_number_format", phase="implementation-call", span={"end_byte":4926,"end_column":1,"end_line":160,"start_byte":4670,"start_column":1,"start_line":149}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.default_number_format", phase="implementation-call", span={"end_byte":4926,"end_column":1,"end_line":160,"start_byte":4670,"start_column":1,"start_line":149}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, NumberFormat, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).decimal_point == ".")), "real.harlequin.results.default_number_format", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.default_number_format", clause="ensures:1", phase="ensures", span={"end_byte":4871,"end_column":40,"end_line":155,"start_byte":4836,"start_column":5,"start_line":155}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((_result).grouping) == 0)), "real.harlequin.results.default_number_format", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.default_number_format", clause="ensures:2", phase="ensures", span={"end_byte":4908,"end_column":37,"end_line":156,"start_byte":4876,"start_column":5,"start_line":156}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, NumberFormat, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def format_number_text(digits: str, number_format: NumberFormat) -> str:
    """Localize a plain decimal number text such as "-1234567.25" or "1e+06":
group the digits of the integer part (after an optional leading "-") by
number_format.grouping from the right, joining groups with
thousands_separator (a grouping entry of 0 repeats the previous size; a size
of 127 or more stops further grouping), and replace the "." decimal point
with decimal_point. Exponent suffixes and fraction digits are unchanged."""
    digits = _cott_normalize_f32_abi(digits, str, path="$.digits")
    number_format = _cott_normalize_f32_abi(number_format, NumberFormat, path="$.number_format")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/format_number_text.py", "9b64cd5d54fbee3e43775fa8ac63e31b9d5a83f1eda88f059963c414b8a6a095", "format_number_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.format_number_text")
        _result = _implementation(digits, number_format)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.format_number_text"
        if _error.span is None:
            _error.span = {"end_byte":5485,"end_column":1,"end_line":172,"start_byte":4926,"start_column":1,"start_line":160}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.format_number_text", phase="implementation-call", span={"end_byte":5485,"end_column":1,"end_line":172,"start_byte":4926,"start_column":1,"start_line":160}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.format_number_text", phase="implementation-call", span={"end_byte":5485,"end_column":1,"end_line":172,"start_byte":4926,"start_column":1,"start_line":160}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def display_value_text(value: CellValue, number_format: NumberFormat, id_column: bool) -> str:
    """The one-line cell text for a literal CellValue, following Harlequin's
results table formatting:
Null -> "∅ null"; Boolean true -> "✓ True", false -> "X False";
Integer -> the decimal digits, localized with format_number_text unless
id_column; Real -> Python format(value, "g") localized with
format_number_text ("nan", "inf" and "-inf" stay as written); Text -> its
first line (up to the first CR or LF) followed by "…⏎" when more lines
follow; Blob -> repr() of its first 32 bytes, followed by " (+N bytes)" when
it has N more bytes."""
    value = _cott_normalize_f32_abi(value, CellValue, path="$.value")
    number_format = _cott_normalize_f32_abi(number_format, NumberFormat, path="$.number_format")
    id_column = _cott_normalize_f32_abi(id_column, bool, path="$.id_column")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/display_value_text.py", "892fb347ccd755f4e729585f36f860c31e5eb45aa64bae8597767efcd31a5c11", "display_value_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.display_value_text")
        _result = _implementation(value, number_format, id_column)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.display_value_text"
        if _error.span is None:
            _error.span = {"end_byte":6195,"end_column":1,"end_line":187,"start_byte":5485,"start_column":1,"start_line":172}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.display_value_text", phase="implementation-call", span={"end_byte":6195,"end_column":1,"end_line":187,"start_byte":5485,"start_column":1,"start_line":172}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.display_value_text", phase="implementation-call", span={"end_byte":6195,"end_column":1,"end_line":187,"start_byte":5485,"start_column":1,"start_line":172}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def is_id_column(name: str) -> bool:
    """Whether a column holds identifiers, whose integers are printed without
digit grouping: the name matches the regular expression (\\b|_)id\\b
case-insensitively, or [a-z]I[dD]\\b case-sensitively."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/is_id_column.py", "9586a5a216903326daab54e11c52fe8fef132e25b5eac482b4a64728651c2f04", "is_id_column", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.is_id_column")
        _result = _implementation(name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.is_id_column"
        if _error.span is None:
            _error.span = {"end_byte":6472,"end_column":1,"end_line":196,"start_byte":6195,"start_column":1,"start_line":187}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.is_id_column", phase="implementation-call", span={"end_byte":6472,"end_column":1,"end_line":196,"start_byte":6195,"start_column":1,"start_line":187}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.is_id_column", phase="implementation-call", span={"end_byte":6472,"end_column":1,"end_line":196,"start_byte":6195,"start_column":1,"start_line":187}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def new_grid(result: ResultSet) -> ResultsGrid:
    """A results tab showing result with the cursor and anchor at row 0 column 0
and no scroll."""
    result = _cott_normalize_f32_abi(result, ResultSet, path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/new_grid.py", "5cccfeb56a90dae231666aea5a36acac99eee0250ee1cbcf913d4f24cc54911e", "new_grid", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.new_grid")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.new_grid"
        if _error.span is None:
            _error.span = {"end_byte":6847,"end_column":1,"end_line":208,"start_byte":6472,"start_column":1,"start_line":196}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.new_grid", phase="implementation-call", span={"end_byte":6847,"end_column":1,"end_line":208,"start_byte":6472,"start_column":1,"start_line":196}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.new_grid", phase="implementation-call", span={"end_byte":6847,"end_column":1,"end_line":208,"start_byte":6472,"start_column":1,"start_line":196}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ResultsGrid, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((((_result).cursor).row == 0) and (((_result).cursor).column == 0))), "real.harlequin.results.new_grid", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.new_grid", clause="ensures:1", phase="ensures", span={"end_byte":6701,"end_column":65,"end_line":202,"start_byte":6641,"start_column":5,"start_line":202}, expected="true", actual="false")
        if not (_cott_contract_condition((((((_result).anchor).row == 0) and (((_result).anchor).column == 0))), "real.harlequin.results.new_grid", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.new_grid", clause="ensures:2", phase="ensures", span={"end_byte":6766,"end_column":65,"end_line":203,"start_byte":6706,"start_column":5,"start_line":203}, expected="true", actual="false")
        if not (_cott_contract_condition(((((_result).first_row == 0) and ((_result).first_column == 0))), "real.harlequin.results.new_grid", "ensures:3")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.new_grid", clause="ensures:3", phase="ensures", span={"end_byte":6829,"end_column":63,"end_line":204,"start_byte":6771,"start_column":5,"start_line":204}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ResultsGrid, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def move_grid(grid: ResultsGrid, motion: GridMotion, extend: bool, page_rows: U64) -> ResultsGrid:
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
    grid = _cott_normalize_f32_abi(grid, ResultsGrid, path="$.grid")
    motion = _cott_normalize_f32_abi(motion, GridMotion, path="$.motion")
    extend = _cott_normalize_f32_abi(extend, bool, path="$.extend")
    page_rows = _cott_normalize_f32_abi(page_rows, U64, path="$.page_rows")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/move_grid.py", "db9048438a48bd1e9565093857a8e6a255c4520f160381e923d5b815711af835", "move_grid", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.move_grid")
        _result = _implementation(grid, motion, extend, page_rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.move_grid"
        if _error.span is None:
            _error.span = {"end_byte":8150,"end_column":1,"end_line":231,"start_byte":6847,"start_column":1,"start_line":208}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.move_grid", phase="implementation-call", span={"end_byte":8150,"end_column":1,"end_line":231,"start_byte":6847,"start_column":1,"start_line":208}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.move_grid", phase="implementation-call", span={"end_byte":8150,"end_column":1,"end_line":231,"start_byte":6847,"start_column":1,"start_line":208}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ResultsGrid, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).result == (grid).result)), "real.harlequin.results.move_grid", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.move_grid", clause="ensures:1", phase="ensures", span={"end_byte":8040,"end_column":41,"end_line":226,"start_byte":8004,"start_column":5,"start_line":226}, expected="true", actual="false")
        if not (_cott_contract_condition(((((_result).first_row == (grid).first_row) and ((_result).first_column == (grid).first_column))), "real.harlequin.results.move_grid", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.move_grid", clause="ensures:2", phase="ensures", span={"end_byte":8132,"end_column":92,"end_line":227,"start_byte":8045,"start_column":5,"start_line":227}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ResultsGrid, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_grid(grid: ResultsGrid, width: U64, height: U64, focused: bool, number_format: NumberFormat) -> GridFrame:
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
    grid = _cott_normalize_f32_abi(grid, ResultsGrid, path="$.grid")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    height = _cott_normalize_f32_abi(height, U64, path="$.height")
    focused = _cott_normalize_f32_abi(focused, bool, path="$.focused")
    number_format = _cott_normalize_f32_abi(number_format, NumberFormat, path="$.number_format")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/render_grid.py", "85e85b9c45d3d6df235a7c254452e502efe6f68fc9e837c3132800aacd0bd2b8", "render_grid", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.render_grid")
        _result = _implementation(grid, width, height, focused, number_format)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.render_grid"
        if _error.span is None:
            _error.span = {"end_byte":11228,"end_column":1,"end_line":278,"start_byte":8150,"start_column":1,"start_line":231}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.render_grid", phase="implementation-call", span={"end_byte":11228,"end_column":1,"end_line":278,"start_byte":8150,"start_column":1,"start_line":231}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.render_grid", phase="implementation-call", span={"end_byte":11228,"end_column":1,"end_line":278,"start_byte":8150,"start_column":1,"start_line":231}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, GridFrame, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).lines) <= height)), "real.harlequin.results.render_grid", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.results.render_grid", clause="ensures:1", phase="ensures", span={"end_byte":11210,"end_column":39,"end_line":274,"start_byte":11176,"start_column":5,"start_line":274}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, GridFrame, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def selection_text(grid: ResultsGrid) -> str:
    """The Copy Selection text: the values in the rectangle spanned by anchor and
cursor, rows top to bottom, each row's values left to right joined by TAB,
rows joined by LF. A value is Python str() of the value pyarrow returns
(so SQL NULL is "None"). An empty result copies ""."""
    grid = _cott_normalize_f32_abi(grid, ResultsGrid, path="$.grid")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/selection_text.py", "dbd6cfe47863a14c149658745350ebe626106705c440b8174566c45a320a8f51", "selection_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.selection_text")
        _result = _implementation(grid)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.selection_text"
        if _error.span is None:
            _error.span = {"end_byte":11600,"end_column":1,"end_line":288,"start_byte":11228,"start_column":1,"start_line":278}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.selection_text", phase="implementation-call", span={"end_byte":11600,"end_column":1,"end_line":288,"start_byte":11228,"start_column":1,"start_line":278}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.selection_text", phase="implementation-call", span={"end_byte":11600,"end_column":1,"end_line":288,"start_byte":11228,"start_column":1,"start_line":278}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def cursor_cell(grid: ResultsGrid) -> Option[CellView]:
    """The View Cell dialog content for the cursor: the column's name and the full
value text (every line; None -> "∅ null"; bytes -> repr of all bytes; other
values as render_grid formats them but without first-line truncation and
without localization). Nothing when the result has no rows or no columns."""
    grid = _cott_normalize_f32_abi(grid, ResultsGrid, path="$.grid")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/cursor_cell.py", "9186906aaca8b29874c6ef874d0d792750000909d5b7a94da91c640e41ac99e9", "cursor_cell", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.cursor_cell")
        _result = _implementation(grid)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.cursor_cell"
        if _error.span is None:
            _error.span = {"end_byte":12009,"end_column":1,"end_line":298,"start_byte":11600,"start_column":1,"start_line":288}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.cursor_cell", phase="implementation-call", span={"end_byte":12009,"end_column":1,"end_line":298,"start_byte":11600,"start_column":1,"start_line":288}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.cursor_cell", phase="implementation-call", span={"end_byte":12009,"end_column":1,"end_line":298,"start_byte":11600,"start_column":1,"start_line":288}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[CellView], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[CellView], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def results_title(result: ResultSet, number_format: NumberFormat) -> str:
    """The results viewer's border title after a query, as Harlequin shows it,
with counts localized by format_number_text:
- row_count == 0 and fetched_row_count == 0: "Query Returned No Records";
- truncated: "Query Results (Showing {row_count} of >{fetched_row_count} Records)";
- row_count < fetched_row_count: "Query Results (Showing {row_count} of {fetched_row_count} Records)";
- otherwise "Query Results ({fetched_row_count} Records)"."""
    result = _cott_normalize_f32_abi(result, ResultSet, path="$.result")
    number_format = _cott_normalize_f32_abi(number_format, NumberFormat, path="$.number_format")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/results/results_title.py", "8ab493d1c8492ca419b5d9c6864718d38b5f22f652202a27acfa2fdd570d1bf9", "results_title", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.results.results_title")
        _result = _implementation(result, number_format)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.results.results_title"
        if _error.span is None:
            _error.span = {"end_byte":12580,"end_column":1,"end_line":310,"start_byte":12009,"start_column":1,"start_line":298}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.results.results_title", phase="implementation-call", span={"end_byte":12580,"end_column":1,"end_line":310,"start_byte":12009,"start_column":1,"start_line":298}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.results.results_title", phase="implementation-call", span={"end_byte":12580,"end_column":1,"end_line":310,"start_byte":12009,"start_column":1,"start_line":298}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["ArrowTable", "CellValue", "CellValue_Blob", "CellValue_Boolean", "CellValue_Integer", "CellValue_Null", "CellValue_Real", "CellValue_Text", "CellView", "ColumnInfo", "GridFrame", "GridMotion", "GridMotion_ColumnEnd", "GridMotion_ColumnStart", "GridMotion_Down", "GridMotion_Left", "GridMotion_NextCell", "GridMotion_PageDown", "GridMotion_PageUp", "GridMotion_PreviousCell", "GridMotion_Right", "GridMotion_RowEnd", "GridMotion_RowStart", "GridMotion_SelectAll", "GridMotion_TableEnd", "GridMotion_TableStart", "GridMotion_Up", "GridPosition", "NumberFormat", "ResultSet", "ResultsGrid", "cursor_cell", "default_number_format", "display_value_text", "format_number_text", "is_id_column", "move_grid", "new_grid", "render_grid", "result_set_from_rows", "results_title", "selection_text"]
