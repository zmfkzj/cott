from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, QueryResult, SqlClientError, SqlClientError_EmptySql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql, TypedRow

def split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/split_statements.py", "a66decfce8ded5968c037339e0a3713f12cd0a5ec57b79b9179f49a89ac0a448", "split_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.split_statements")
        _result = _implementation(sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.split_statements"
        if _error.span is None:
            _error.span = {"end_byte":720,"end_column":1,"end_line":37,"start_byte":503,"start_column":1,"start_line":29}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":720,"end_column":1,"end_line":37,"start_byte":503,"start_column":1,"start_line":29}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":720,"end_column":1,"end_line":37,"start_byte":503,"start_column":1,"start_line":29}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.split_statements", phase="error", span={"end_byte":720,"end_column":1,"end_line":37,"start_byte":503,"start_column":1,"start_line":29}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            statements = _cott_match_value.value
            return ((len(statements) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.split_statements", clause="ensures:0", phase="ensures", span={"end_byte":626,"end_column":56,"end_line":30,"start_byte":575,"start_column":5,"start_line":30}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    read_only = _cott_validate_abi(read_only, bool, path="$.read_only")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_sql.py", "7b2d048f3676fa1b67a260c9819d586a09ad96fbeb3befb2fc8c32beae187567", "execute_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_sql")
        _result = _implementation(database, sql, read_only)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_sql"
        if _error.span is None:
            _error.span = {"end_byte":1144,"end_column":1,"end_line":51,"start_byte":720,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":1144,"end_column":1,"end_line":51,"start_byte":720,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":1144,"end_column":1,"end_line":51,"start_byte":720,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[QueryResult], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_sql", phase="error", span={"end_byte":1144,"end_column":1,"end_line":51,"start_byte":720,"start_column":1,"start_line":37}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            results = _cott_match_value.value
            return ((len(results) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_sql", clause="ensures:0", phase="ensures", span={"end_byte":898,"end_column":50,"end_line":42,"start_byte":853,"start_column":5,"start_line":42}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[QueryResult], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "QueryResult", "SqlClientError", "SqlClientError_EmptySql", "SqlClientError_ReadOnlyViolation", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "TypedRow", "execute_sql", "split_statements"]
