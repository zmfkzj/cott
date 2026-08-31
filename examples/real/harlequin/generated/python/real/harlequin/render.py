from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.harlequin.render_types import ExportFormat, ExportFormat_Csv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Sql, ExportFormat_Tsv, ExportRequest, KeyBinding, Keymap, RenderError, RenderError_DestinationDenied, RenderError_ExportFailed, RenderError_InvalidWidth, RenderError_UnsupportedCell, RenderLayout, RenderLayout_Table, RenderLayout_Vertical, RenderOptions, Theme
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult

def render_table(result: QueryResult) -> str:
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_table.py", "42bdf8cca6c3722d9ca69cc776cf83b885ced88791d40c3846e83523b29b8a81", "render_table", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_table")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_table"
        if _error.span is None:
            _error.span = {"end_byte":940,"end_column":1,"end_line":51,"start_byte":879,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":940,"end_column":1,"end_line":51,"start_byte":879,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":940,"end_column":1,"end_line":51,"start_byte":879,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_vertical(result: QueryResult) -> str:
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_vertical.py", "0e4762abb501e6330a1e77a31fe4d5d37bb92f574c555cd986a97d47b0c833ab", "render_vertical", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_vertical")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_vertical"
        if _error.span is None:
            _error.span = {"end_byte":1004,"end_column":1,"end_line":54,"start_byte":940,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_vertical", phase="implementation-call", span={"end_byte":1004,"end_column":1,"end_line":54,"start_byte":940,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_vertical", phase="implementation-call", span={"end_byte":1004,"end_column":1,"end_line":54,"start_byte":940,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]:
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    options = _cott_validate_abi(options, RenderOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_result.py", "845e713f4ffee69c4f638ea6b43c829b143c7100afb1c8ef6e3d7923dd59d9b5", "render_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_result")
        _result = _implementation(result, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_result"
        if _error.span is None:
            _error.span = {"end_byte":1238,"end_column":1,"end_line":62,"start_byte":1004,"start_column":1,"start_line":54}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_result", phase="implementation-call", span={"end_byte":1238,"end_column":1,"end_line":62,"start_byte":1004,"start_column":1,"start_line":54}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_result", phase="implementation-call", span={"end_byte":1238,"end_column":1,"end_line":62,"start_byte":1004,"start_column":1,"start_line":54}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, RenderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.render.render_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RenderError_InvalidWidth, RenderError_UnsupportedCell,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.render.render_result", phase="error", span={"end_byte":1238,"end_column":1,"end_line":62,"start_byte":1004,"start_column":1,"start_line":54}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.render.render_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return ((len(rendered) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.render_result", clause="ensures:0", phase="ensures", span={"end_byte":1146,"end_column":52,"end_line":55,"start_byte":1099,"start_column":5,"start_line":55}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, RenderError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    relations = _cott_validate_abi(relations, CottList[CatalogRelation], path="$.relations")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_relations.py", "c37194fbbe81e640c3c12dc09948416d1d26fb99dfad504559e69c44a9a0cc39", "render_catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_relations")
        _result = _implementation(relations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":1324,"end_column":1,"end_line":65,"start_byte":1238,"start_column":1,"start_line":62}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":1324,"end_column":1,"end_line":65,"start_byte":1238,"start_column":1,"start_line":62}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":1324,"end_column":1,"end_line":65,"start_byte":1238,"start_column":1,"start_line":62}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    columns = _cott_validate_abi(columns, CottList[CatalogColumn], path="$.columns")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_columns.py", "2887e8cdae1c47ae996b671bf95de8f1b36426b891476eb34641b375315037e6", "render_catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_columns")
        _result = _implementation(columns)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":1404,"end_column":1,"end_line":68,"start_byte":1324,"start_column":1,"start_line":65}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":1404,"end_column":1,"end_line":68,"start_byte":1324,"start_column":1,"start_line":65}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":1404,"end_column":1,"end_line":68,"start_byte":1324,"start_column":1,"start_line":65}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    catalog_matches = _cott_validate_abi(catalog_matches, CottList[CatalogMatch], path="$.catalog_matches")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_matches.py", "0562c59400798c8e8d6881dc68b7ef40f7f41e28d315ee1e6cfdb2672a6ecdb0", "render_catalog_matches", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_matches")
        _result = _implementation(catalog_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_matches"
        if _error.span is None:
            _error.span = {"end_byte":1491,"end_column":1,"end_line":71,"start_byte":1404,"start_column":1,"start_line":68}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":1491,"end_column":1,"end_line":71,"start_byte":1404,"start_column":1,"start_line":68}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":1491,"end_column":1,"end_line":71,"start_byte":1404,"start_column":1,"start_line":68}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def bundled_themes() -> CottList[Theme]:
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/bundled_themes.py", "2ae892c96edbf7eb71da8d5e8cd1fddd9971b64ff5f52300171735e4cad403eb", "bundled_themes", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.bundled_themes")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.bundled_themes"
        if _error.span is None:
            _error.span = {"end_byte":1543,"end_column":1,"end_line":74,"start_byte":1491,"start_column":1,"start_line":71}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.bundled_themes", phase="implementation-call", span={"end_byte":1543,"end_column":1,"end_line":74,"start_byte":1491,"start_column":1,"start_line":71}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.bundled_themes", phase="implementation-call", span={"end_byte":1543,"end_column":1,"end_line":74,"start_byte":1491,"start_column":1,"start_line":71}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Theme], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[Theme], path="$.return", validator=_cott_validate_abi)
    return _result

def bundled_keymaps() -> CottList[Keymap]:
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/bundled_keymaps.py", "975f15964b8c663b96d879eee556f881f3a7ddfbef1c301ca1ec4a0c9115ed3e", "bundled_keymaps", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.bundled_keymaps")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.bundled_keymaps"
        if _error.span is None:
            _error.span = {"end_byte":1597,"end_column":1,"end_line":77,"start_byte":1543,"start_column":1,"start_line":74}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.bundled_keymaps", phase="implementation-call", span={"end_byte":1597,"end_column":1,"end_line":77,"start_byte":1543,"start_column":1,"start_line":74}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.bundled_keymaps", phase="implementation-call", span={"end_byte":1597,"end_column":1,"end_line":77,"start_byte":1543,"start_column":1,"start_line":74}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Keymap], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[Keymap], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_theme(themes: CottList[Theme], name: str) -> Option[Theme]:
    themes = _cott_validate_abi(themes, CottList[Theme], path="$.themes")
    name = _cott_validate_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/resolve_theme.py", "fcd50747e64f42fd5a07f13b45175830e5aec36427262bb4b38bab35a0fc539b", "resolve_theme", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.resolve_theme")
        _result = _implementation(themes, name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.resolve_theme"
        if _error.span is None:
            _error.span = {"end_byte":1680,"end_column":1,"end_line":80,"start_byte":1597,"start_column":1,"start_line":77}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.resolve_theme", phase="implementation-call", span={"end_byte":1680,"end_column":1,"end_line":80,"start_byte":1597,"start_column":1,"start_line":77}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.resolve_theme", phase="implementation-call", span={"end_byte":1680,"end_column":1,"end_line":80,"start_byte":1597,"start_column":1,"start_line":77}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Theme], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[Theme], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_keymap(keymaps: CottList[Keymap], name: str) -> Option[Keymap]:
    keymaps = _cott_validate_abi(keymaps, CottList[Keymap], path="$.keymaps")
    name = _cott_validate_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/resolve_keymap.py", "6463be1057d1a91e33e745224aea73b3dbad70be1bd03a195c3a956d9e7d01b8", "resolve_keymap", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.resolve_keymap")
        _result = _implementation(keymaps, name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.resolve_keymap"
        if _error.span is None:
            _error.span = {"end_byte":1767,"end_column":1,"end_line":83,"start_byte":1680,"start_column":1,"start_line":80}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.resolve_keymap", phase="implementation-call", span={"end_byte":1767,"end_column":1,"end_line":83,"start_byte":1680,"start_column":1,"start_line":80}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.resolve_keymap", phase="implementation-call", span={"end_byte":1767,"end_column":1,"end_line":83,"start_byte":1680,"start_column":1,"start_line":80}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
        _implementation = _cott_load("_cott_impl/real/harlequin/render/export_result.py", "fc722df1632a58ff24655660209f33992ddae2837a0022571088ce3954b5d04b", "export_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.export_result")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.export_result"
        if _error.span is None:
            _error.span = {"end_byte":2127,"end_column":1,"end_line":94,"start_byte":1767,"start_column":1,"start_line":83}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.export_result", phase="implementation-call", span={"end_byte":2127,"end_column":1,"end_line":94,"start_byte":1767,"start_column":1,"start_line":83}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.export_result", phase="implementation-call", span={"end_byte":2127,"end_column":1,"end_line":94,"start_byte":1767,"start_column":1,"start_line":83}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, RenderError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.render.export_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RenderError_DestinationDenied, RenderError_ExportFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.render.export_result", phase="error", span={"end_byte":2127,"end_column":1,"end_line":94,"start_byte":1767,"start_column":1,"start_line":83}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.render.export_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            written = _cott_match_value.value
            return (((request).destination).writable)
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.render.export_result", clause="ensures:1", phase="ensures", span={"end_byte":2015,"end_column":63,"end_line":88,"start_byte":1957,"start_column":5,"start_line":88}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, RenderError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme", "bundled_keymaps", "bundled_themes", "export_result", "render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_result", "render_table", "render_vertical", "resolve_keymap", "resolve_theme"]
