from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.render_types import ExportFormat, ExportFormat_Csv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Sql, ExportFormat_Tsv, ExportRequest, KeyBinding, Keymap, RenderError, RenderError_DestinationDenied, RenderError_ExportFailed, RenderError_InvalidWidth, RenderError_UnsupportedCell, RenderLayout, RenderLayout_Table, RenderLayout_Vertical, RenderOptions, Theme
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult

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
            _error.span = {"end_byte":1333,"end_column":1,"end_line":59,"start_byte":879,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":1333,"end_column":1,"end_line":59,"start_byte":879,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":1333,"end_column":1,"end_line":59,"start_byte":879,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
            _error.span = {"end_byte":1721,"end_column":1,"end_line":69,"start_byte":1333,"start_column":1,"start_line":59}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_vertical", phase="implementation-call", span={"end_byte":1721,"end_column":1,"end_line":69,"start_byte":1333,"start_column":1,"start_line":59}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_vertical", phase="implementation-call", span={"end_byte":1721,"end_column":1,"end_line":69,"start_byte":1333,"start_column":1,"start_line":59}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]:
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
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    options = _cott_validate_abi(options, RenderOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_result.py", "6a1043dfc2b57df3645b7ed0540b95e1cf753a3b3aa052050d49cd8e180e5e5a", "render_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_result")
        _result = _implementation(result, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_result"
        if _error.span is None:
            _error.span = {"end_byte":2750,"end_column":1,"end_line":90,"start_byte":1721,"start_column":1,"start_line":69}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_result", phase="implementation-call", span={"end_byte":2750,"end_column":1,"end_line":90,"start_byte":1721,"start_column":1,"start_line":69}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_result", phase="implementation-call", span={"end_byte":2750,"end_column":1,"end_line":90,"start_byte":1721,"start_column":1,"start_line":69}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, RenderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.render.render_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RenderError_InvalidWidth, RenderError_UnsupportedCell,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.render.render_result", phase="error", span={"end_byte":2750,"end_column":1,"end_line":90,"start_byte":1721,"start_column":1,"start_line":69}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.render.render_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.render.render_result", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is RenderError_InvalidWidth:
        _cott_contract_condition(True, "real.harlequin.render.render_result", "error:2")
    if type(_result) is Err and type(_result.error) is RenderError_UnsupportedCell:
        _cott_contract_condition(True, "real.harlequin.render.render_result", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return (_cott_contract_condition(((len(rendered) > 0)), "real.harlequin.render.render_result", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.render.render_result", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.render_result", clause="ensures:1", phase="ensures", span={"end_byte":2658,"end_column":52,"end_line":83,"start_byte":2611,"start_column":5,"start_line":83}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, RenderError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    """This diagnostic view joins the standard generated CatalogRelation string
representation for each value with LF, preserving order. No trailing LF;
empty input returns "". No database access or extra records are introduced."""
    relations = _cott_validate_abi(relations, CottList[CatalogRelation], path="$.relations")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_relations.py", "6ba7e591c09de6f69cd4ec8bde4b72820e4eaa2960c4ba2c258100131383a9a2", "render_catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_relations")
        _result = _implementation(relations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":3091,"end_column":1,"end_line":99,"start_byte":2750,"start_column":1,"start_line":90}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":3091,"end_column":1,"end_line":99,"start_byte":2750,"start_column":1,"start_line":90}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":3091,"end_column":1,"end_line":99,"start_byte":2750,"start_column":1,"start_line":90}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    """This diagnostic view joins the standard generated CatalogColumn string
representation for each value with LF, retaining all fields and input order.
No trailing LF; empty input returns "". It is not an inferred SQL declaration."""
    columns = _cott_validate_abi(columns, CottList[CatalogColumn], path="$.columns")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_columns.py", "2887e8cdae1c47ae996b671bf95de8f1b36426b891476eb34641b375315037e6", "render_catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_columns")
        _result = _implementation(columns)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":3431,"end_column":1,"end_line":108,"start_byte":3091,"start_column":1,"start_line":99}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":3431,"end_column":1,"end_line":108,"start_byte":3091,"start_column":1,"start_line":99}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":3431,"end_column":1,"end_line":108,"start_byte":3091,"start_column":1,"start_line":99}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    """This diagnostic view joins the standard generated CatalogMatch string
representation for each value with LF, preserving order and all fields.
No trailing LF; empty input returns ""."""
    catalog_matches = _cott_validate_abi(catalog_matches, CottList[CatalogMatch], path="$.catalog_matches")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_matches.py", "cb096a1de153fa7b6713a10ebf15f704a3700c912c41ec26c85bd909fb65722f", "render_catalog_matches", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_matches")
        _result = _implementation(catalog_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_matches"
        if _error.span is None:
            _error.span = {"end_byte":3733,"end_column":1,"end_line":117,"start_byte":3431,"start_column":1,"start_line":108}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":3733,"end_column":1,"end_line":117,"start_byte":3431,"start_column":1,"start_line":108}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":3733,"end_column":1,"end_line":117,"start_byte":3431,"start_column":1,"start_line":108}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def bundled_themes() -> CottList[Theme]:
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/bundled_themes.py", "696662dc389ded2dc5cf72a0f7826f882dd99a4d154bf6e48c2d3f4db10fd051", "bundled_themes", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.bundled_themes")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.bundled_themes"
        if _error.span is None:
            _error.span = {"end_byte":3785,"end_column":1,"end_line":120,"start_byte":3733,"start_column":1,"start_line":117}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.bundled_themes", phase="implementation-call", span={"end_byte":3785,"end_column":1,"end_line":120,"start_byte":3733,"start_column":1,"start_line":117}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.bundled_themes", phase="implementation-call", span={"end_byte":3785,"end_column":1,"end_line":120,"start_byte":3733,"start_column":1,"start_line":117}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Theme], path="$.return")
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
            _error.span = {"end_byte":4220,"end_column":1,"end_line":131,"start_byte":3785,"start_column":1,"start_line":120}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.bundled_keymaps", phase="implementation-call", span={"end_byte":4220,"end_column":1,"end_line":131,"start_byte":3785,"start_column":1,"start_line":120}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.bundled_keymaps", phase="implementation-call", span={"end_byte":4220,"end_column":1,"end_line":131,"start_byte":3785,"start_column":1,"start_line":120}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Keymap], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[Keymap], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_theme(themes: CottList[Theme], name: str) -> Option[Theme]:
    """Return Some containing the first Theme whose name exactly equals name,
case-sensitively; return Nothing when there is no match. Do not clone or edit it."""
    themes = _cott_validate_abi(themes, CottList[Theme], path="$.themes")
    name = _cott_validate_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/resolve_theme.py", "fcd50747e64f42fd5a07f13b45175830e5aec36427262bb4b38bab35a0fc539b", "resolve_theme", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.resolve_theme")
        _result = _implementation(themes, name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.resolve_theme"
        if _error.span is None:
            _error.span = {"end_byte":4485,"end_column":1,"end_line":139,"start_byte":4220,"start_column":1,"start_line":131}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.resolve_theme", phase="implementation-call", span={"end_byte":4485,"end_column":1,"end_line":139,"start_byte":4220,"start_column":1,"start_line":131}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.resolve_theme", phase="implementation-call", span={"end_byte":4485,"end_column":1,"end_line":139,"start_byte":4220,"start_column":1,"start_line":131}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Theme], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[Theme], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_keymap(keymaps: CottList[Keymap], name: str) -> Option[Keymap]:
    """Return Some containing the first Keymap whose name exactly equals name,
case-sensitively; return Nothing when there is no match. Do not clone or edit it."""
    keymaps = _cott_validate_abi(keymaps, CottList[Keymap], path="$.keymaps")
    name = _cott_validate_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/resolve_keymap.py", "6463be1057d1a91e33e745224aea73b3dbad70be1bd03a195c3a956d9e7d01b8", "resolve_keymap", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.resolve_keymap")
        _result = _implementation(keymaps, name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.resolve_keymap"
        if _error.span is None:
            _error.span = {"end_byte":4755,"end_column":1,"end_line":147,"start_byte":4485,"start_column":1,"start_line":139}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.resolve_keymap", phase="implementation-call", span={"end_byte":4755,"end_column":1,"end_line":147,"start_byte":4485,"start_column":1,"start_line":139}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.resolve_keymap", phase="implementation-call", span={"end_byte":4755,"end_column":1,"end_line":147,"start_byte":4485,"start_column":1,"start_line":139}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Keymap], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[Keymap], path="$.return", validator=_cott_validate_abi)
    return _result

def export_result(request: ExportRequest) -> Result[Unit, RenderError]:
    """Match destination.location as FileLocation_Local/S3; serialize row.values; use boto3 Any."""
    request = _cott_validate_abi(request, ExportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/export_result.py", "79c8a787985809860d4cb84e972db6fe13085af8417db440fe821b7f2cbe5ab5", "export_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.export_result")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.export_result"
        if _error.span is None:
            _error.span = {"end_byte":5115,"end_column":1,"end_line":158,"start_byte":4755,"start_column":1,"start_line":147}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.export_result", phase="implementation-call", span={"end_byte":5115,"end_column":1,"end_line":158,"start_byte":4755,"start_column":1,"start_line":147}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.export_result", phase="implementation-call", span={"end_byte":5115,"end_column":1,"end_line":158,"start_byte":4755,"start_column":1,"start_line":147}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, RenderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.render.export_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RenderError_DestinationDenied, RenderError_ExportFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.render.export_result", phase="error", span={"end_byte":5115,"end_column":1,"end_line":158,"start_byte":4755,"start_column":1,"start_line":147}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.render.export_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.render.export_result", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is RenderError_DestinationDenied:
        _cott_contract_condition(True, "real.harlequin.render.export_result", "error:2")
    if type(_result) is Err and type(_result.error) is RenderError_ExportFailed:
        _cott_contract_condition(True, "real.harlequin.render.export_result", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            written = _cott_match_value.value
            return (_cott_contract_condition((((request).destination).writable), "real.harlequin.render.export_result", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.render.export_result", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.export_result", clause="ensures:1", phase="ensures", span={"end_byte":5003,"end_column":63,"end_line":152,"start_byte":4945,"start_column":5,"start_line":152}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, RenderError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme", "bundled_keymaps", "bundled_themes", "export_result", "render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_result", "render_table", "render_vertical", "resolve_keymap", "resolve_theme"]
