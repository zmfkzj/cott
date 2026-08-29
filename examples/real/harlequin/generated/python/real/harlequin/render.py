from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import QueryResult

def render_table(result: QueryResult) -> str:
    """Render a query result deterministically in horizontal or vertical table form."""
    result = _cott_validate_abi(result, QueryResult, path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_table.py", "0cb3f0017afc0eb2ab01dba0a7ee635e23ea79f5d25946608c640816e0a4f832", "render_table", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_table")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_table"
        if _error.span is None:
            _error.span = {"end_byte":307,"end_column":1,"end_line":13,"start_byte":143,"start_column":1,"start_line":6}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":307,"end_column":1,"end_line":13,"start_byte":143,"start_column":1,"start_line":6}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_table", phase="implementation-call", span={"end_byte":307,"end_column":1,"end_line":13,"start_byte":143,"start_column":1,"start_line":6}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    """Render catalog relations in deterministic table order."""
    relations = _cott_validate_abi(relations, CottList[CatalogRelation], path="$.relations")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_relations.py", "c99a5635da90619fa0243e820063c539da42ec1472e2656f07db674ef9f6724f", "render_catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_relations")
        _result = _implementation(relations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":473,"end_column":1,"end_line":20,"start_byte":307,"start_column":1,"start_line":13}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":473,"end_column":1,"end_line":20,"start_byte":307,"start_column":1,"start_line":13}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_relations", phase="implementation-call", span={"end_byte":473,"end_column":1,"end_line":20,"start_byte":307,"start_column":1,"start_line":13}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    """Render catalog columns in deterministic table order."""
    columns = _cott_validate_abi(columns, CottList[CatalogColumn], path="$.columns")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_columns.py", "88f223d93d64c3ee058b9d8a88077ea9af5c8492bc0e31d3967f959cc3e5f1b6", "render_catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_columns")
        _result = _implementation(columns)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":631,"end_column":1,"end_line":27,"start_byte":473,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":631,"end_column":1,"end_line":27,"start_byte":473,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_columns", phase="implementation-call", span={"end_byte":631,"end_column":1,"end_line":27,"start_byte":473,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    """Render catalog matches in deterministic table order."""
    catalog_matches = _cott_validate_abi(catalog_matches, CottList[CatalogMatch], path="$.catalog_matches")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/render/render_catalog_matches.py", "d16fab3240bcf984a987df712bcee0fa09e86886bdedf9d7c728d40704e41769", "render_catalog_matches", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.render.render_catalog_matches")
        _result = _implementation(catalog_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.render.render_catalog_matches"
        if _error.span is None:
            _error.span = {"end_byte":795,"end_column":1,"end_line":33,"start_byte":631,"start_column":1,"start_line":27}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":795,"end_column":1,"end_line":33,"start_byte":631,"start_column":1,"start_line":27}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.render.render_catalog_matches", phase="implementation-call", span={"end_byte":795,"end_column":1,"end_line":33,"start_byte":631,"start_column":1,"start_line":27}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_table"]
