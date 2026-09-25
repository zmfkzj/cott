from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_unique_by

from real.harlequin.render_types import ExportFormat, ExportFormat_Csv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Sql, ExportFormat_Tsv, ExportRequest, KeyBinding, Keymap, RenderError, RenderError_DestinationDenied, RenderError_ExportFailed, RenderError_InvalidWidth, RenderError_UnsupportedCell, RenderLayout, RenderLayout_Table, RenderLayout_Vertical, RenderOptions, Theme
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult, SavedFile

def render_table(result: QueryResult) -> str:
    """Format Cell.Null as NULL, Integer/Real as str(value), Text as its stored text,
and Blob as lowercase hexadecimal. Emit a header joined by " | " when columns
is nonempty, then one similarly joined line for each row in input order.
Join lines with LF without a trailing LF. No columns and no rows returns "".
This function applies no row or width limit."""
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_table.py", "25c80435f43729afc74f4e4d7b8e1627f05aa41e3d92cb00ed649cffbd16f39b", "render_table", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_table")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_table"
        if _error.span is None:
            _error.span = {"end_byte":1508,"end_column":1,"end_line":75,"start_byte":1054,"start_column":1,"start_line":64}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":1508,"end_column":1,"end_line":75,"start_byte":1054,"start_column":1,"start_line":64}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":1508,"end_column":1,"end_line":75,"start_byte":1054,"start_column":1,"start_line":64}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_vertical(result: QueryResult) -> str:
    """For each row, starting at one, emit "Row N" followed by "column: value" lines
for paired columns and values. Use the same cell text mapping as render_table.
Preserve order, join with LF without a trailing LF; no rows returns "".
Pair only the common length if columns and values differ."""
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_vertical.py", "d9b9fa41d382df9e1d2765950d0a8c219973793bf99a3cbd494bff812f523919", "render_vertical", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_vertical")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_vertical"
        if _error.span is None:
            _error.span = {"end_byte":1896,"end_column":1,"end_line":85,"start_byte":1508,"start_column":1,"start_line":75}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_vertical", phase="implementation-call", span={"end_byte":1896,"end_column":1,"end_line":85,"start_byte":1508,"start_column":1,"start_line":75}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_vertical", phase="implementation-call", span={"end_byte":1896,"end_column":1,"end_line":85,"start_byte":1508,"start_column":1,"start_line":75}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]:
    """terminal_width or maximum_cell_width zero returns InvalidWidth with that zero
width. Keep only the first maximum_rows rows, preserving columns and order.
A NUL in a column name or in a Text cell of a kept row is UnsupportedCell.
Use the render_table cell mapping, truncating every column/cell string to
maximum_cell_width Unicode code points before formatting. Table uses " | "
headers/rows; Vertical uses "Row N" and "column: value" lines.
Clip each resulting line to terminal_width code points without ellipsis.
Join with LF and no trailing LF. If output would be empty or whitespace only,
use "(no rows)" clipped to terminal_width so successful output is nonempty."""
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    options = _cott_validate_abi(options, RenderOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((options).terminal_width == 0) or ((options).maximum_cell_width == 0))), "real.harlequin.render.render_result", "error:3:condition")):
        _expected_error = RenderError_InvalidWidth
        _expected_error_span = {"end_byte":2939,"end_column":105,"end_line":101,"start_byte":2839,"start_column":5,"start_line":101}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_result.py", "6a1043dfc2b57df3645b7ed0540b95e1cf753a3b3aa052050d49cd8e180e5e5a", "render_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_result")
        _result = _implementation(result, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_result"
        if _error.span is None:
            _error.span = {"end_byte":2995,"end_column":1,"end_line":106,"start_byte":1896,"start_column":1,"start_line":85}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_result", phase="implementation-call", span={"end_byte":2995,"end_column":1,"end_line":106,"start_byte":1896,"start_column":1,"start_line":85}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_result", phase="implementation-call", span={"end_byte":2995,"end_column":1,"end_line":106,"start_byte":1896,"start_column":1,"start_line":85}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, RenderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.render.render_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RenderError_UnsupportedCell,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.render.render_result", phase="error", span={"end_byte":2995,"end_column":1,"end_line":106,"start_byte":1896,"start_column":1,"start_line":85}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.render.render_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.render.render_result", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is RenderError_UnsupportedCell:
        _cott_contract_condition(True, "real.harlequin.render.render_result", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return (_cott_contract_condition(((len(rendered) > 0)), "real.harlequin.render.render_result", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.render.render_result", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.render_result", clause="ensures:1", phase="ensures", span={"end_byte":2763,"end_column":52,"end_line":98,"start_byte":2716,"start_column":5,"start_line":98}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is RenderError_InvalidWidth and True:
            width = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((width == 0)), "real.harlequin.render.render_result", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.render.render_result", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.render_result", clause="ensures:2", phase="ensures", span={"end_byte":2833,"end_column":70,"end_line":99,"start_byte":2768,"start_column":5,"start_line":99}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, RenderError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    """One line per relation in input order: "table NAME" or "view NAME". Stored SQL is
not shown. Lines are joined with LF without a trailing LF; empty input is ""."""
    relations = _cott_validate_abi(relations, CottList[CatalogRelation], path="$.relations")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_relations.py", "024f2933ee4f21e0610996b7ef65a752693a6d74f442f169f5bce912fa688539", "render_catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_relations")
        _result = _implementation(relations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":3269,"end_column":1,"end_line":114,"start_byte":2995,"start_column":1,"start_line":106}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":3269,"end_column":1,"end_line":114,"start_byte":2995,"start_column":1,"start_line":106}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":3269,"end_column":1,"end_line":114,"start_byte":2995,"start_column":1,"start_line":106}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    """One line per column in input order: RELATION.NAME, then " " and declared_type
when it is nonempty, " NOT NULL" when not_null, " DEFAULT " and default_sql when
present, and " PRIMARY KEY " followed by primary_key_position when it is nonzero.
ordinal is not shown. Lines are joined with LF without a trailing LF; empty input
is ""."""
    columns = _cott_validate_abi(columns, CottList[CatalogColumn], path="$.columns")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_columns.py", "937394e25a32f3321826c08f2161249e83d97804fa6a3663d71f04f96cafbad3", "render_catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_columns")
        _result = _implementation(columns)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":3720,"end_column":1,"end_line":125,"start_byte":3269,"start_column":1,"start_line":114}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":3720,"end_column":1,"end_line":125,"start_byte":3269,"start_column":1,"start_line":114}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":3720,"end_column":1,"end_line":125,"start_byte":3269,"start_column":1,"start_line":114}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    """One line per match in input order: "relation NAME" for a Relation match and
"column RELATION.NAME" for a Column match. Lines are joined with LF without a
trailing LF; empty input is ""."""
    catalog_matches = _cott_validate_abi(catalog_matches, CottList[CatalogMatch], path="$.catalog_matches")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_matches.py", "d2d86308c27551ac2df8f1cd3ef1728b3158e5e4e92dbda0ac61de56af27a121", "render_catalog_matches", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_matches")
        _result = _implementation(catalog_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_matches"
        if _error.span is None:
            _error.span = {"end_byte":4026,"end_column":1,"end_line":134,"start_byte":3720,"start_column":1,"start_line":125}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":4026,"end_column":1,"end_line":134,"start_byte":3720,"start_column":1,"start_line":125}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":4026,"end_column":1,"end_line":134,"start_byte":3720,"start_column":1,"start_line":125}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def bundled_themes() -> CottList[Theme]:
    """Return exactly these built-in themes, in this order, as
name | foreground | background | accent:
harlequin | #DDDDDD | #0C0C0C | #FEFFAC
monokai | #F8F8F2 | #272822 | #F92672
dracula | #F8F8F2 | #282A36 | #BD93F9
nord | #D8DEE9 | #2E3440 | #88C0D0"""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/bundled_themes.py", "d8cb7cc762dbf8e757f0e02c4c9a431c4b68c03f48e1557d663ce8e3733c0e45", "bundled_themes", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.bundled_themes")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.bundled_themes"
        if _error.span is None:
            _error.span = {"end_byte":4416,"end_column":1,"end_line":148,"start_byte":4026,"start_column":1,"start_line":134}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.bundled_themes", phase="implementation-call", span={"end_byte":4416,"end_column":1,"end_line":148,"start_byte":4026,"start_column":1,"start_line":134}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.bundled_themes", phase="implementation-call", span={"end_byte":4416,"end_column":1,"end_line":148,"start_byte":4026,"start_column":1,"start_line":134}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Theme], path="$.return")
    if not (_cott_contract_condition((_cott_unique_by(_result, "name")), "real.harlequin.render.bundled_themes", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.bundled_themes", clause="ensures:1", phase="ensures", span={"end_byte":4398,"end_column":44,"end_line":144,"start_byte":4359,"start_column":5,"start_line":144}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Theme], path="$.return", validator=_cott_validate_abi)
    return _result

def bundled_keymaps() -> CottList[Keymap]:
    """Return exactly two built-in keymaps, in this order. "default" contains
ctrl+enter -> execute, ctrl+s -> save, ctrl+q -> quit.
"vim" contains ctrl+enter -> execute, :w -> save, :q -> quit.
Preserve the listed binding order and exact spelling. These are this Cott
client's static defaults, not a runtime scan of upstream packages or plugins."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/bundled_keymaps.py", "0da31ff828b2899fbf630beca11c5a7e7f00cad9be932627beecd02e97a78710", "bundled_keymaps", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.bundled_keymaps")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.bundled_keymaps"
        if _error.span is None:
            _error.span = {"end_byte":4897,"end_column":1,"end_line":161,"start_byte":4416,"start_column":1,"start_line":148}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.bundled_keymaps", phase="implementation-call", span={"end_byte":4897,"end_column":1,"end_line":161,"start_byte":4416,"start_column":1,"start_line":148}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.bundled_keymaps", phase="implementation-call", span={"end_byte":4897,"end_column":1,"end_line":161,"start_byte":4416,"start_column":1,"start_line":148}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Keymap], path="$.return")
    if not (_cott_contract_condition((_cott_unique_by(_result, "name")), "real.harlequin.render.bundled_keymaps", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.bundled_keymaps", clause="ensures:1", phase="ensures", span={"end_byte":4879,"end_column":45,"end_line":157,"start_byte":4839,"start_column":5,"start_line":157}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Keymap], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_theme(themes: CottList[Theme], name: str) -> Option[Theme]:
    """Return Some containing the first Theme whose name exactly equals name,
case-sensitively; return Nothing when there is no match."""
    themes = _cott_validate_abi(themes, CottList[Theme], path="$.themes")
    name = _cott_validate_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/resolve_theme.py", "fcd50747e64f42fd5a07f13b45175830e5aec36427262bb4b38bab35a0fc539b", "resolve_theme", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.resolve_theme")
        _result = _implementation(themes, name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.resolve_theme"
        if _error.span is None:
            _error.span = {"end_byte":5191,"end_column":1,"end_line":171,"start_byte":4897,"start_column":1,"start_line":161}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.resolve_theme", phase="implementation-call", span={"end_byte":5191,"end_column":1,"end_line":171,"start_byte":4897,"start_column":1,"start_line":161}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.resolve_theme", phase="implementation-call", span={"end_byte":5191,"end_column":1,"end_line":171,"start_byte":4897,"start_column":1,"start_line":161}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Theme], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            theme = _cott_match_value.value
            return (_cott_contract_condition((((theme).name == name)), "real.harlequin.render.resolve_theme", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.render.resolve_theme", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.resolve_theme", clause="ensures:1", phase="ensures", span={"end_byte":5173,"end_column":53,"end_line":167,"start_byte":5125,"start_column":5,"start_line":167}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[Theme], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_keymap(keymaps: CottList[Keymap], name: str) -> Option[Keymap]:
    """Return Some containing the first Keymap whose name exactly equals name,
case-sensitively; return Nothing when there is no match."""
    keymaps = _cott_validate_abi(keymaps, CottList[Keymap], path="$.keymaps")
    name = _cott_validate_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/resolve_keymap.py", "6463be1057d1a91e33e745224aea73b3dbad70be1bd03a195c3a956d9e7d01b8", "resolve_keymap", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.resolve_keymap")
        _result = _implementation(keymaps, name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.resolve_keymap"
        if _error.span is None:
            _error.span = {"end_byte":5492,"end_column":1,"end_line":181,"start_byte":5191,"start_column":1,"start_line":171}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.resolve_keymap", phase="implementation-call", span={"end_byte":5492,"end_column":1,"end_line":181,"start_byte":5191,"start_column":1,"start_line":171}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.resolve_keymap", phase="implementation-call", span={"end_byte":5492,"end_column":1,"end_line":181,"start_byte":5191,"start_column":1,"start_line":171}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Keymap], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            keymap = _cott_match_value.value
            return (_cott_contract_condition((((keymap).name == name)), "real.harlequin.render.resolve_keymap", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.render.resolve_keymap", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.resolve_keymap", clause="ensures:1", phase="ensures", span={"end_byte":5474,"end_column":55,"end_line":177,"start_byte":5424,"start_column":5,"start_line":177}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[Keymap], path="$.return", validator=_cott_validate_abi)
    return _result

def export_result(request: ExportRequest) -> Result[SavedFile, RenderError]:
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
    request = _cott_validate_abi(request, ExportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((not ((request).destination).writable)), "real.harlequin.render.export_result", "error:4:condition")):
        _expected_error = RenderError_DestinationDenied
        _expected_error_span = {"end_byte":8240,"end_column":78,"end_line":220,"start_byte":8167,"start_column":5,"start_line":220}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/export_result.py", "bd17f4524924af719646f126b7a7ffd6001c5c4a20fdf64050ad007e7b0b36f9", "export_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.export_result")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.export_result"
        if _error.span is None:
            _error.span = {"end_byte":8390,"end_column":1,"end_line":227,"start_byte":5492,"start_column":1,"start_line":181}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.export_result", phase="implementation-call", span={"end_byte":8390,"end_column":1,"end_line":227,"start_byte":5492,"start_column":1,"start_line":181}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.export_result", phase="implementation-call", span={"end_byte":8390,"end_column":1,"end_line":227,"start_byte":5492,"start_column":1,"start_line":181}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[SavedFile, RenderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.render.export_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RenderError_DestinationDenied, RenderError_UnsupportedCell, RenderError_ExportFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.render.export_result", phase="error", span={"end_byte":8390,"end_column":1,"end_line":227,"start_byte":5492,"start_column":1,"start_line":181}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.render.export_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.render.export_result", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is RenderError_DestinationDenied:
        _cott_contract_condition(True, "real.harlequin.render.export_result", "error:5")
    if type(_result) is Err and type(_result.error) is RenderError_UnsupportedCell:
        _cott_contract_condition(True, "real.harlequin.render.export_result", "error:6")
    if type(_result) is Err and type(_result.error) is RenderError_ExportFailed:
        _cott_contract_condition(True, "real.harlequin.render.export_result", "error:7")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition((((saved).reference == (request).destination)), "real.harlequin.render.export_result", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.render.export_result", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.export_result", clause="ensures:1", phase="ensures", span={"end_byte":7973,"end_column":71,"end_line":216,"start_byte":7907,"start_column":5,"start_line":216}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is RenderError_DestinationDenied and True:
            denied = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((denied == (request).destination)), "real.harlequin.render.export_result", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.render.export_result", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.export_result", clause="ensures:2", phase="ensures", span={"end_byte":8068,"end_column":95,"end_line":217,"start_byte":7978,"start_column":5,"start_line":217}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is RenderError_ExportFailed and True and True:
            failed = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((failed == (request).destination)), "real.harlequin.render.export_result", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.render.export_result", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.export_result", clause="ensures:3", phase="ensures", span={"end_byte":8161,"end_column":93,"end_line":218,"start_byte":8073,"start_column":5,"start_line":218}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[SavedFile, RenderError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme", "bundled_keymaps", "bundled_themes", "export_result", "render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_result", "render_table", "render_vertical", "resolve_keymap", "resolve_theme"]
