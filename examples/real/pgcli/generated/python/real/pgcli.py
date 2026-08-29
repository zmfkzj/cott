from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.pgcli_types import BackslashCommand, BackslashCommand_Describe, BackslashCommand_Help, BackslashCommand_Quit, BackslashCommand_Tables, BackslashCommand_Unknown, ColumnCatalog, CompletionRequest, CompletionResult, ConnectionError, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionError_PromptDisabled, ConnectionInputs, ConnectionSettings, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, EnvironmentInputs, PromptAction, PromptAction_PromptPassword, PromptAction_UsePassword, QueryResult, RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery, TableCatalog

def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    inputs = _cott_validate_abi(inputs, ConnectionInputs, path="$.inputs")
    environment = _cott_validate_abi(environment, EnvironmentInputs, path="$.environment")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((((inputs).database == "") and ((environment).database == ""))):
        _expected_error = ConnectionError_MissingDatabase
        _expected_error_span = {"end_byte":2283,"end_column":100,"end_line":90,"start_byte":2188,"start_column":5,"start_line":90}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection.py", "6c24ecb3bae0b4e26e120d3c5859ecd72fde3cb4d6c5c070dae6c427ad98bc99", "resolve_connection", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection")
        _result = _implementation(inputs, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection"
        if _error.span is None:
            _error.span = {"end_byte":2339,"end_column":1,"end_line":95,"start_byte":1241,"start_column":1,"start_line":80}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":2339,"end_column":1,"end_line":95,"start_byte":1241,"start_column":1,"start_line":80}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":2339,"end_column":1,"end_line":95,"start_byte":1241,"start_column":1,"start_line":80}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionSettings, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_InvalidPort,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection", phase="error", span={"end_byte":2339,"end_column":1,"end_line":95,"start_byte":1241,"start_column":1,"start_line":80}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).host != "") and ((settings).host == (inputs).host)) or (((inputs).host == "") and ((settings).host == (environment).host))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:0", phase="ensures", span={"end_byte":1530,"end_column":151,"end_line":84,"start_byte":1384,"start_column":5,"start_line":84}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).port != "") and ((settings).port == (inputs).port)) or (((inputs).port == "") and ((settings).port == (environment).port))))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:1", phase="ensures", span={"end_byte":1681,"end_column":151,"end_line":85,"start_byte":1535,"start_column":5,"start_line":85}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).user != "") and ((settings).user == (inputs).user)) or (((inputs).user == "") and ((settings).user == (environment).user))))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:2", phase="ensures", span={"end_byte":1832,"end_column":151,"end_line":86,"start_byte":1686,"start_column":5,"start_line":86}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).password != "") and ((settings).password == (inputs).password)) or (((inputs).password == "") and ((settings).password == (environment).password))))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:3", phase="ensures", span={"end_byte":2007,"end_column":175,"end_line":87,"start_byte":1837,"start_column":5,"start_line":87}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).database != "") and ((settings).database == (inputs).database)) or (((inputs).database == "") and ((settings).database == (environment).database))))
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:4", phase="ensures", span={"end_byte":2182,"end_column":175,"end_line":88,"start_byte":2012,"start_column":5,"start_line":88}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionSettings, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]:
    no_prompt = _cott_validate_abi(no_prompt, bool, path="$.no_prompt")
    password = _cott_validate_abi(password, str, path="$.password")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((no_prompt and (password == ""))):
        _expected_error = ConnectionError_PromptDisabled
        _expected_error_span = {"end_byte":2658,"end_column":75,"end_line":98,"start_byte":2588,"start_column":5,"start_line":98}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/prompt_policy.py", "a43b76c00b63c68e78d7dec858586b55e8cd85ea53e1d774600e6d845934c94c", "prompt_policy", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.prompt_policy")
        _result = _implementation(no_prompt, password)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.prompt_policy"
        if _error.span is None:
            _error.span = {"end_byte":2676,"end_column":1,"end_line":102,"start_byte":2339,"start_column":1,"start_line":95}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":2676,"end_column":1,"end_line":102,"start_byte":2339,"start_column":1,"start_line":95}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":2676,"end_column":1,"end_line":102,"start_byte":2339,"start_column":1,"start_line":95}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PromptAction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.prompt_policy", phase="error", span={"end_byte":2676,"end_column":1,"end_line":102,"start_byte":2339,"start_column":1,"start_line":95}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            action = _cott_match_value.value
            return ((((password != "") and (action == PromptAction_UsePassword())) or ((password == "") and (action == PromptAction_PromptPassword()))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.prompt_policy", clause="ensures:0", phase="ensures", span={"end_byte":2582,"end_column":153,"end_line":96,"start_byte":2434,"start_column":5,"start_line":96}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PromptAction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_sql.py", "db0443c12775e5f486eb4ef278f9d8c8e52d8ab5394d4db987825301dcf987e8", "complete_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":2757,"end_column":1,"end_line":105,"start_byte":2676,"start_column":1,"start_line":102}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":2757,"end_column":1,"end_line":105,"start_byte":2676,"start_column":1,"start_line":102}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":2757,"end_column":1,"end_line":105,"start_byte":2676,"start_column":1,"start_line":102}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def render_query(request: RenderRequest) -> RenderedQuery:
    request = _cott_validate_abi(request, RenderRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/render_query.py", "3223e727252a9bca4e1ef174546c9a6321c7306e9566c8d392d7d53dfdc43bec", "render_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.render_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.render_query"
        if _error.span is None:
            _error.span = {"end_byte":2831,"end_column":1,"end_line":108,"start_byte":2757,"start_column":1,"start_line":105}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":2831,"end_column":1,"end_line":108,"start_byte":2757,"start_column":1,"start_line":105}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":2831,"end_column":1,"end_line":108,"start_byte":2757,"start_column":1,"start_line":105}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, RenderedQuery, path="$.return")
    _result = _cott_wrap_async_protocol(_result, RenderedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def recognize_backslash(source: str) -> BackslashCommand:
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/recognize_backslash.py", "5e619c21888e4556221b8925f8793dcc28a13cb074e4713981095eaa81bbb75d", "recognize_backslash", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.recognize_backslash")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.recognize_backslash"
        if _error.span is None:
            _error.span = {"end_byte":2904,"end_column":1,"end_line":111,"start_byte":2831,"start_column":1,"start_line":108}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":2904,"end_column":1,"end_line":111,"start_byte":2831,"start_column":1,"start_line":108}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":2904,"end_column":1,"end_line":111,"start_byte":2831,"start_column":1,"start_line":108}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, BackslashCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, BackslashCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    connection = _cott_validate_abi(connection, ConnectionSettings, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_query.py", "49286a4bb3af3d28634aba557a542a47039fbb0b2db1f40d5658d8d9c6d51e13", "execute_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_query")
        _result = _implementation(connection, sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_query"
        if _error.span is None:
            _error.span = {"end_byte":3223,"end_column":1,"end_line":118,"start_byte":2904,"start_column":1,"start_line":111}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":3223,"end_column":1,"end_line":118,"start_byte":2904,"start_column":1,"start_line":111}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":3223,"end_column":1,"end_line":118,"start_byte":2904,"start_column":1,"start_line":111}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryResult, DatabaseError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (DatabaseError_ConnectionFailed, DatabaseError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_query", phase="error", span={"end_byte":3223,"end_column":1,"end_line":118,"start_byte":2904,"start_column":1,"start_line":111}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            query_result = _cott_match_value.value
            return (((len((query_result).rows) == 0) or (len((query_result).columns) > 0)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_query", clause="ensures:0", phase="ensures", span={"end_byte":3099,"end_column":98,"end_line":112,"start_byte":3006,"start_column":5,"start_line":112}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryResult, DatabaseError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "ColumnCatalog", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_PromptDisabled", "ConnectionInputs", "ConnectionSettings", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EnvironmentInputs", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryResult", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "TableCatalog", "complete_sql", "execute_query", "prompt_policy", "recognize_backslash", "render_query", "resolve_connection"]
