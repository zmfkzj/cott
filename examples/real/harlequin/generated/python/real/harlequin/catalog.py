from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.harlequin.catalog_types import CatalogColumn, CatalogError, CatalogError_ConnectionMissing, CatalogError_Failed, CatalogError_LimitExceeded, CatalogError_NamespaceMissing, CatalogMatch, CatalogMatchKind, CatalogMatchKind_Column, CatalogMatchKind_Relation, CatalogRelation, CatalogScope, CatalogSnapshot, CompletionRequest, CompletionResult, RelationKind, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError

def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_relations.py", "da0c3e834ba61c6597e9a85709909ad9afeadcb02dad4fb675f487136e2263b3", "catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_relations")
        _result = _implementation(database)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_relations", phase="error", span={"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            relations = _cott_match_value.value
            return ((len(relations) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_relations", clause="ensures:0", phase="ensures", span={"end_byte":1239,"end_column":60,"end_line":60,"start_byte":1184,"start_column":5,"start_line":60}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    relation = _cott_validate_abi(relation, str, path="$.relation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_columns.py", "4481d0ba5224067fd94637337adae29519f7bb0aeadd125881636888e7330c4f", "catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_columns")
        _result = _implementation(database, relation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_columns", phase="error", span={"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            columns = _cott_match_value.value
            return ((len(columns) <= 65535))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_columns", clause="ensures:0", phase="ensures", span={"end_byte":1483,"end_column":55,"end_line":70,"start_byte":1433,"start_column":5,"start_line":70}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    term = _cott_validate_abi(term, str, path="$.term")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/search_catalog.py", "479fee03d82490b6611d10dc39a5f5384fefd43ea8a1a5985fac2c972cf1c0ee", "search_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.search_catalog")
        _result = _implementation(database, term)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.search_catalog"
        if _error.span is None:
            _error.span = {"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.search_catalog", phase="error", span={"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog_matches = _cott_match_value.value
            return ((len(catalog_matches) <= 1000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.search_catalog", clause="ensures:0", phase="ensures", span={"end_byte":1736,"end_column":70,"end_line":80,"start_byte":1671,"start_column":5,"start_line":80}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def refresh_catalog(connection: Connection, scope: CatalogScope) -> Result[CatalogSnapshot, CatalogError]:
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    scope = _cott_validate_abi(scope, CatalogScope, path="$.scope")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/refresh_catalog.py", "ea8e8d7872741d0fd3b6e97e9987217cb4208b5f10036e37862712846095dc01", "refresh_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.refresh_catalog")
        _result = _implementation(connection, scope)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.refresh_catalog"
        if _error.span is None:
            _error.span = {"end_byte":2180,"end_column":1,"end_line":99,"start_byte":1807,"start_column":1,"start_line":86}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.refresh_catalog", phase="implementation-call", span={"end_byte":2180,"end_column":1,"end_line":99,"start_byte":1807,"start_column":1,"start_line":86}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.refresh_catalog", phase="implementation-call", span={"end_byte":2180,"end_column":1,"end_line":99,"start_byte":1807,"start_column":1,"start_line":86}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CatalogSnapshot, CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CatalogError_ConnectionMissing, CatalogError_NamespaceMissing, CatalogError_Failed, CatalogError_LimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.refresh_catalog", phase="error", span={"end_byte":2180,"end_column":1,"end_line":99,"start_byte":1807,"start_column":1,"start_line":86}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return ((len((snapshot).relations) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:0", phase="ensures", span={"end_byte":1991,"end_column":68,"end_line":90,"start_byte":1928,"start_column":5,"start_line":90}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CatalogSnapshot, CatalogError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    snapshot = _cott_validate_abi(snapshot, CatalogSnapshot, path="$.snapshot")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/complete_sql.py", "dd6a6fc02c15103c80da1be48f4a797d7352bb6f54219dd3d8f925284610ba48", "complete_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.complete_sql")
        _result = _implementation(request, snapshot)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":2353,"end_column":1,"end_line":104,"start_byte":2180,"start_column":1,"start_line":99}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.complete_sql", phase="implementation-call", span={"end_byte":2353,"end_column":1,"end_line":104,"start_byte":2180,"start_column":1,"start_line":99}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.complete_sql", phase="implementation-call", span={"end_byte":2353,"end_column":1,"end_line":104,"start_byte":2180,"start_column":1,"start_line":99}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not ((len((_result).candidates) <= (request).maximum_candidates)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.complete_sql", clause="ensures:0", phase="ensures", span={"end_byte":2335,"end_column":64,"end_line":100,"start_byte":2276,"start_column":5,"start_line":100}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def find_catalog(snapshot: CatalogSnapshot, term: str, maximum_matches: U64) -> Result[CottList[CatalogMatch], CatalogError]:
    snapshot = _cott_validate_abi(snapshot, CatalogSnapshot, path="$.snapshot")
    term = _cott_validate_abi(term, str, path="$.term")
    maximum_matches = _cott_validate_abi(maximum_matches, U64, path="$.maximum_matches")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/find_catalog.py", "8a8ca88d8289d131180a2dedcca21a343608634693fddcb5d6f6c4440cc7fd9b", "find_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.find_catalog")
        _result = _implementation(snapshot, term, maximum_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.find_catalog"
        if _error.span is None:
            _error.span = {"end_byte":2604,"end_column":1,"end_line":114,"start_byte":2353,"start_column":1,"start_line":104}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.find_catalog", phase="implementation-call", span={"end_byte":2604,"end_column":1,"end_line":114,"start_byte":2353,"start_column":1,"start_line":104}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.find_catalog", phase="implementation-call", span={"end_byte":2604,"end_column":1,"end_line":114,"start_byte":2353,"start_column":1,"start_line":104}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.find_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CatalogError_LimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.find_catalog", phase="error", span={"end_byte":2604,"end_column":1,"end_line":114,"start_byte":2353,"start_column":1,"start_line":104}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.find_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            found = _cott_match_value.value
            return ((len(found) <= maximum_matches))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.find_catalog", clause="ensures:0", phase="ensures", span={"end_byte":2549,"end_column":61,"end_line":109,"start_byte":2493,"start_column":5,"start_line":109}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogMatch], CatalogError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "complete_sql", "find_catalog", "refresh_catalog", "search_catalog"]
