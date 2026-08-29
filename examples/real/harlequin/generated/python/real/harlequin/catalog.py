from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogMatchKind, CatalogMatchKind_Column, CatalogMatchKind_Relation, CatalogRelation, RelationKind, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import DatabaseTarget, SqlClientError

def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_relations.py", "141c83b17e3240d32e64de9379b1b603fbf8d03913c52dd938f3c036bba7a1ea", "catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_relations")
        _result = _implementation(database)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":757,"end_column":1,"end_line":40,"start_byte":530,"start_column":1,"start_line":33}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":757,"end_column":1,"end_line":40,"start_byte":530,"start_column":1,"start_line":33}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":757,"end_column":1,"end_line":40,"start_byte":530,"start_column":1,"start_line":33}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_relations", phase="error", span={"end_byte":757,"end_column":1,"end_line":40,"start_byte":530,"start_column":1,"start_line":33}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            relations = _cott_match_value.value
            return ((len(relations) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_relations", clause="ensures:0", phase="ensures", span={"end_byte":686,"end_column":60,"end_line":34,"start_byte":631,"start_column":5,"start_line":34}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    relation = _cott_validate_abi(relation, str, path="$.relation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_columns.py", "6c7a51ec9092a500360ac87074774144cbfc6a70a019bdf6c77ad20ffbd52703", "catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_columns")
        _result = _implementation(database, relation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":1001,"end_column":1,"end_line":50,"start_byte":757,"start_column":1,"start_line":40}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":1001,"end_column":1,"end_line":50,"start_byte":757,"start_column":1,"start_line":40}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":1001,"end_column":1,"end_line":50,"start_byte":757,"start_column":1,"start_line":40}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_columns", phase="error", span={"end_byte":1001,"end_column":1,"end_line":50,"start_byte":757,"start_column":1,"start_line":40}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            columns = _cott_match_value.value
            return ((len(columns) <= 65535))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_columns", clause="ensures:0", phase="ensures", span={"end_byte":930,"end_column":55,"end_line":44,"start_byte":880,"start_column":5,"start_line":44}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    term = _cott_validate_abi(term, str, path="$.term")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/search_catalog.py", "1b34afb1a121714a79d8891c9f4c78d5bf13d06849567dfff8a3e077f1671cb5", "search_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.search_catalog")
        _result = _implementation(database, term)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.search_catalog"
        if _error.span is None:
            _error.span = {"end_byte":1253,"end_column":1,"end_line":59,"start_byte":1001,"start_column":1,"start_line":50}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":1253,"end_column":1,"end_line":59,"start_byte":1001,"start_column":1,"start_line":50}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":1253,"end_column":1,"end_line":59,"start_byte":1001,"start_column":1,"start_line":50}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.search_catalog", phase="error", span={"end_byte":1253,"end_column":1,"end_line":59,"start_byte":1001,"start_column":1,"start_line":50}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog_matches = _cott_match_value.value
            return ((len(catalog_matches) <= 1000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.search_catalog", clause="ensures:0", phase="ensures", span={"end_byte":1183,"end_column":70,"end_line":54,"start_byte":1118,"start_column":5,"start_line":54}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CatalogColumn", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "search_catalog"]
