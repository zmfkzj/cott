from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.pgcli_types import BackslashCommand, BackslashCommand_Describe, BackslashCommand_Help, BackslashCommand_Quit, BackslashCommand_Tables, BackslashCommand_Unknown, Catalog, CatalogRefreshRequest, ClientError, ClientError_CatalogFailed, ClientError_EditorFailed, ClientError_ExportFailed, ClientError_FavoriteFailed, ClientError_HistoryFailed, ClientError_ImportFailed, ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_NotificationFailed, ClientError_PagerFailed, ClientError_QueryFailed, ClientError_TerminalFailed, ClientError_TransactionFailed, ClientError_UnsupportedFormat, ColumnCatalog, CommandInvocation, CommandResult, CompletionPolicy, CompletionRequest, CompletionResult, ConnectionError, ConnectionError_ConnectionFailed, ConnectionError_CredentialUnavailable, ConnectionError_InvalidDsn, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionError_ProfileMissing, ConnectionError_PromptDisabled, ConnectionError_SshInvalid, ConnectionError_TlsInvalid, ConnectionInputs, ConnectionPlan, ConnectionProfile, ConnectionRequest, ConnectionSettings, CredentialRequest, CredentialResolution, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, EditorRequest, EnvironmentInputs, ExecutedQuery, ExportRequest, Favorite, FavoriteStore, FormatRequest, FormattedQuery, HighlightRequest, HighlightedSql, HistoryEntry, HistoryPolicy, ImportRequest, InputBuffer, InteractiveRequest, MetaCommand, MetaCommand_ClearOutput, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery, MetaCommand_Describe, MetaCommand_Echo, MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_Expanded, MetaCommand_Favorite, MetaCommand_Help, MetaCommand_History, MetaCommand_ListDataTypes, MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains, MetaCommand_ListExtensions, MetaCommand_ListFavorites, MetaCommand_ListForeignTables, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListNotifications, MetaCommand_ListPrivileges, MetaCommand_ListRoles, MetaCommand_ListSchemas, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews, MetaCommand_NamedQuery, MetaCommand_Password, MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho, MetaCommand_Quit, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery, MetaCommand_SetFormat, MetaCommand_SetLogFile, MetaCommand_SetOptions, MetaCommand_SetOutput, MetaCommand_SetPager, MetaCommand_Shell, MetaCommand_ShowFunction, MetaCommand_SqlHelp, MetaCommand_Timing, MetaCommand_Unknown, MetaCommand_VerboseErrors, MetaCommand_Watch, MetaCommand_WriteBuffer, Notification, NotificationRequest, PagerRequest, PasswordSource, PasswordSource_Environment, PasswordSource_Keyring, PasswordSource_None, PasswordSource_Prompt, PasswordSource_Supplied, PromptAction, PromptAction_PromptPassword, PromptAction_UsePassword, QueryPlan, QueryRequest, QueryResult, RelationCatalog, RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery, RoutineCatalog, SessionOptions, SshSettings, TableCatalog, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical, TlsSettings, TransactionMode, TransactionMode_AutoCommit, TransactionMode_Manual, TransactionMode_ReadOnly, TransactionState, TransferResult, WatchRequest, WatchResult

def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]:
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_dsn.py", "2651625fe1f1e8f651223c13fb879319beb38339f7c460fe57d3d9564e9fcf27", "parse_dsn", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_dsn")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_dsn"
        if _error.span is None:
            _error.span = {"end_byte":9009,"end_column":1,"end_line":434,"start_byte":8828,"start_column":1,"start_line":427}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_dsn", phase="implementation-call", span={"end_byte":9009,"end_column":1,"end_line":434,"start_byte":8828,"start_column":1,"start_line":427}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_dsn", phase="implementation-call", span={"end_byte":9009,"end_column":1,"end_line":434,"start_byte":8828,"start_column":1,"start_line":427}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionInputs, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.parse_dsn", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_InvalidDsn,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.parse_dsn", phase="error", span={"end_byte":9009,"end_column":1,"end_line":434,"start_byte":8828,"start_column":1,"start_line":427}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.parse_dsn", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.parse_dsn", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidDsn:
        _cott_contract_condition(True, "real.pgcli.parse_dsn", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (_cott_contract_condition((((inputs).database != "")), "real.pgcli.parse_dsn", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.parse_dsn", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.parse_dsn", clause="ensures:0", phase="ensures", span={"end_byte":8953,"end_column":55,"end_line":428,"start_byte":8903,"start_column":5,"start_line":428}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionInputs, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_profile(name: str, profiles: CottList[ConnectionProfile]) -> Result[ConnectionProfile, ConnectionError]:
    name = _cott_validate_abi(name, str, path="$.name")
    profiles = _cott_validate_abi(profiles, CottList[ConnectionProfile], path="$.profiles")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_profile.py", "f8e9c7db3b2404f9ec26c6c6e3681785f3390c05baef2d26385f2f8f66c52067", "resolve_profile", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_profile")
        _result = _implementation(name, profiles)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_profile"
        if _error.span is None:
            _error.span = {"end_byte":9246,"end_column":1,"end_line":444,"start_byte":9009,"start_column":1,"start_line":434}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_profile", phase="implementation-call", span={"end_byte":9246,"end_column":1,"end_line":444,"start_byte":9009,"start_column":1,"start_line":434}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_profile", phase="implementation-call", span={"end_byte":9246,"end_column":1,"end_line":444,"start_byte":9009,"start_column":1,"start_line":434}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionProfile, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_ProfileMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_profile", phase="error", span={"end_byte":9246,"end_column":1,"end_line":444,"start_byte":9009,"start_column":1,"start_line":434}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_profile", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_ProfileMissing:
        _cott_contract_condition(True, "real.pgcli.resolve_profile", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            profile = _cott_match_value.value
            return (_cott_contract_condition((((profile).name == name)), "real.pgcli.resolve_profile", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.resolve_profile", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_profile", clause="ensures:0", phase="ensures", span={"end_byte":9186,"end_column":55,"end_line":438,"start_byte":9136,"start_column":5,"start_line":438}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionProfile, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    inputs = _cott_validate_abi(inputs, ConnectionInputs, path="$.inputs")
    environment = _cott_validate_abi(environment, EnvironmentInputs, path="$.environment")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection.py", "0253e82519bdba5d71040deca1d8c26c1174c026c346c00d8a16569071fba85f", "resolve_connection", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection")
        _result = _implementation(inputs, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection"
        if _error.span is None:
            _error.span = {"end_byte":10286,"end_column":1,"end_line":459,"start_byte":9246,"start_column":1,"start_line":444}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":10286,"end_column":1,"end_line":459,"start_byte":9246,"start_column":1,"start_line":444}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":10286,"end_column":1,"end_line":459,"start_byte":9246,"start_column":1,"start_line":444}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionSettings, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_MissingDatabase, ConnectionError_InvalidPort,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection", phase="error", span={"end_byte":10286,"end_column":1,"end_line":459,"start_byte":9246,"start_column":1,"start_line":444}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_connection", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_MissingDatabase:
        _cott_contract_condition(True, "real.pgcli.resolve_connection", "error:5")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidPort:
        _cott_contract_condition(True, "real.pgcli.resolve_connection", "error:6")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).host != "") and ((settings).host == (inputs).host)) or (((inputs).host == "") and ((settings).host == (environment).host)))), "real.pgcli.resolve_connection", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:0", phase="ensures", span={"end_byte":9535,"end_column":151,"end_line":448,"start_byte":9389,"start_column":5,"start_line":448}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).port != "") and ((settings).port == (inputs).port)) or (((inputs).port == "") and ((settings).port == (environment).port)))), "real.pgcli.resolve_connection", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:1", phase="ensures", span={"end_byte":9686,"end_column":151,"end_line":449,"start_byte":9540,"start_column":5,"start_line":449}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).user != "") and ((settings).user == (inputs).user)) or (((inputs).user == "") and ((settings).user == (environment).user)))), "real.pgcli.resolve_connection", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:2", phase="ensures", span={"end_byte":9837,"end_column":151,"end_line":450,"start_byte":9691,"start_column":5,"start_line":450}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).password != "") and ((settings).password == (inputs).password)) or (((inputs).password == "") and ((settings).password == (environment).password)))), "real.pgcli.resolve_connection", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:3", phase="ensures", span={"end_byte":10012,"end_column":175,"end_line":451,"start_byte":9842,"start_column":5,"start_line":451}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).database != "") and ((settings).database == (inputs).database)) or (((inputs).database == "") and ((settings).database == (environment).database)))), "real.pgcli.resolve_connection", "ensures:4"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:4", phase="ensures", span={"end_byte":10187,"end_column":175,"end_line":452,"start_byte":10017,"start_column":5,"start_line":452}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionSettings, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]:
    request = _cott_validate_abi(request, ConnectionRequest, path="$.request")
    profile = _cott_validate_abi(profile, Option[ConnectionProfile], path="$.profile")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection_plan.py", "f3ecfede310d5ea1cf167d534055ad773fc8bb206f8ff15de480c1a716a6cfca", "resolve_connection_plan", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection_plan")
        _result = _implementation(request, profile)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection_plan"
        if _error.span is None:
            _error.span = {"end_byte":10701,"end_column":1,"end_line":473,"start_byte":10286,"start_column":1,"start_line":459}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection_plan", phase="implementation-call", span={"end_byte":10701,"end_column":1,"end_line":473,"start_byte":10286,"start_column":1,"start_line":459}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection_plan", phase="implementation-call", span={"end_byte":10701,"end_column":1,"end_line":473,"start_byte":10286,"start_column":1,"start_line":459}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionPlan, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection_plan", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_MissingDatabase, ConnectionError_InvalidPort, ConnectionError_InvalidDsn, ConnectionError_TlsInvalid, ConnectionError_SshInvalid,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection_plan", phase="error", span={"end_byte":10701,"end_column":1,"end_line":473,"start_byte":10286,"start_column":1,"start_line":459}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection_plan", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_MissingDatabase:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:1")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidPort:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:2")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidDsn:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:3")
    if type(_result) is Err and type(_result.error) is ConnectionError_TlsInvalid:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:4")
    if type(_result) is Err and type(_result.error) is ConnectionError_SshInvalid:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:5")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition(((((plan).settings).database != "")), "real.pgcli.resolve_connection_plan", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:0", phase="ensures", span={"end_byte":10491,"end_column":60,"end_line":463,"start_byte":10436,"start_column":5,"start_line":463}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionPlan, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]:
    no_prompt = _cott_validate_abi(no_prompt, bool, path="$.no_prompt")
    password = _cott_validate_abi(password, str, path="$.password")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((no_prompt and (password == ""))), "real.pgcli.prompt_policy", "error:1:condition")):
        _expected_error = ConnectionError_PromptDisabled
        _expected_error_span = {"end_byte":11020,"end_column":75,"end_line":476,"start_byte":10950,"start_column":5,"start_line":476}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/prompt_policy.py", "a43b76c00b63c68e78d7dec858586b55e8cd85ea53e1d774600e6d845934c94c", "prompt_policy", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.prompt_policy")
        _result = _implementation(no_prompt, password)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.prompt_policy"
        if _error.span is None:
            _error.span = {"end_byte":11038,"end_column":1,"end_line":480,"start_byte":10701,"start_column":1,"start_line":473}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":11038,"end_column":1,"end_line":480,"start_byte":10701,"start_column":1,"start_line":473}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":11038,"end_column":1,"end_line":480,"start_byte":10701,"start_column":1,"start_line":473}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PromptAction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.prompt_policy", phase="error", span={"end_byte":11038,"end_column":1,"end_line":480,"start_byte":10701,"start_column":1,"start_line":473}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.prompt_policy", _expected_error_clause)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            action = _cott_match_value.value
            return (_cott_contract_condition(((((password != "") and (action == PromptAction_UsePassword())) or ((password == "") and (action == PromptAction_PromptPassword())))), "real.pgcli.prompt_policy", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.prompt_policy", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.prompt_policy", clause="ensures:0", phase="ensures", span={"end_byte":10944,"end_column":153,"end_line":474,"start_byte":10796,"start_column":5,"start_line":474}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PromptAction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]:
    """Resolve a password with short-circuit priority: nonempty supplied_password
returns Supplied; otherwise nonempty environment_password returns Environment.
Those fields are already resolved input, so do not read process environment.
Otherwise, if use_keyring is true, require nonempty service and user and call
the lock-selected keyring.get_password(service, user). A nonempty result
returns Keyring. A None or empty result means no stored credential and proceeds
to the prompt policy. A backend/lookup failure returns CredentialUnavailable
with a fixed nonsecret message; never write/delete a keyring entry.
If still unresolved and no_prompt is true, return PromptDisabled without
reading stdin or opening the terminal. Otherwise prompt exactly once using
getpass.getpass with a fixed "Password: " prompt. Do not permit its echoed-input
fallback: treat getpass.GetPassWarning as an error. A nonempty response returns
Prompt; an explicitly submitted empty response returns password="" with
PasswordSource.None (passwordless authentication). EOF, cancellation, terminal
or hidden-input failure returns CredentialUnavailable without echoing secrets.
Never log or include any password, service credential or raw exception in errors."""
    request = _cott_validate_abi(request, CredentialRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_credential.py", "d4ae5d17ab91c175d440acc8c4af5964e1d507f5883fed327ccd5f72d06ce639", "resolve_credential", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_credential")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_credential"
        if _error.span is None:
            _error.span = {"end_byte":12697,"end_column":1,"end_line":507,"start_byte":11038,"start_column":1,"start_line":480}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_credential", phase="implementation-call", span={"end_byte":12697,"end_column":1,"end_line":507,"start_byte":11038,"start_column":1,"start_line":480}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_credential", phase="implementation-call", span={"end_byte":12697,"end_column":1,"end_line":507,"start_byte":11038,"start_column":1,"start_line":480}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CredentialResolution, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_credential", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_CredentialUnavailable, ConnectionError_PromptDisabled,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_credential", phase="error", span={"end_byte":12697,"end_column":1,"end_line":507,"start_byte":11038,"start_column":1,"start_line":480}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_credential", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_credential", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_CredentialUnavailable:
        _cott_contract_condition(True, "real.pgcli.resolve_credential", "error:2")
    if type(_result) is Err and type(_result.error) is ConnectionError_PromptDisabled:
        _cott_contract_condition(True, "real.pgcli.resolve_credential", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolution = _cott_match_value.value
            return (_cott_contract_condition(((((resolution).password != "") or ((resolution).source == PasswordSource_None()))), "real.pgcli.resolve_credential", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.resolve_credential", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_credential", clause="ensures:1", phase="ensures", span={"end_byte":12559,"end_column":109,"end_line":500,"start_byte":12455,"start_column":5,"start_line":500}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CredentialResolution, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def connect(plan: ConnectionPlan) -> Result[Unit, ConnectionError]:
    """Probe an authenticated PostgreSQL session using the lock-selected psycopg
driver, execute SELECT 1, and close it before returning Unit. This function
does not install a global session or retain a transaction or SSH daemon.
A real successful query, not an open TCP socket, establishes success.

Parse plan.dsn with psycopg.conninfo.conninfo_to_dict (empty means no DSN).
Nonempty settings.host, port, user, password and database override the DSN's
corresponding host, port, user, password and dbname; empty settings leave
the DSN value in place. Require a nonempty resolved dbname. Validate a supplied
port as decimal 1..65535; the default port is 5432. Pass connection parameters
as psycopg keyword arguments, never SQL or shell text.
plan.tls.mode overrides sslmode: empty means prefer; otherwise accept exactly
disable, allow, prefer, require, verify-ca, verify-full. The Path value "."
means an omitted certificate path. Other root_certificate, certificate and
private_key paths override sslrootcert, sslcert and sslkey respectively.
The certificate and private key are supplied together or both omitted.
Invalid DSN/port/TLS data maps to ConnectionFailed, the only declared error.
Set connect_timeout=10 regardless of DSN and issue no application writes.

Without SSH connect directly. With Some(ssh), use the installed OpenSSH ssh
executable with an argument vector, never a shell. Validate nonempty jump
host/user, positive port, and a single remote database host (no comma-separated
host list, Unix socket or control characters). Preserve the resolved database
hostname for TLS verification, but connect to the loopback tunnel using
hostaddr=127.0.0.1 and the allocated local port. Missing remote host defaults
to localhost from the jump host's perspective.
Launch a foreground control master with -M -N, a private mode-0700 temporary
directory and control socket, BatchMode=yes, StrictHostKeyChecking=yes,
ExitOnForwardFailure=yes, ConnectTimeout=10, ControlPersist=no and
GatewayPorts=no. Existing known_hosts is authority: never accept an unknown
key automatically. Use -p and -l for jump port/user; private_key "." means
no explicit identity file, otherwise use -i. Reject jump host beginning "-".
Wait at most ten monotonic seconds for ssh -S socket -O check to succeed.
Allocate a loopback-only port through a short-lived bound socket, then ask
the authenticated master with -O forward -L 127.0.0.1:port:dbhost:dbport.
Quote IPv6 hosts with forwarding-syntax brackets. A bind race is a declared
failure, never permission to connect through an unconfirmed forwarding.
Confirm the control request succeeded before contacting PostgreSQL.
All ssh commands are bounded; stdin is DEVNULL, no password prompt or shell,
no password in argv, and subprocess output is not copied into diagnostics.

On every path close the psycopg connection, request control-master exit,
terminate then kill and wait for a still-running owned foreground process,
and remove the temporary control directory. Never kill an unrelated PID.
All validation, driver, authentication, TLS, SSH, query, timeout or cleanup
failures return ConnectionFailed with a fixed nonsecret category message;
never include a DSN, password, private-key contents or raw exception text."""
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connect.py", "44f725b213a1c700ca3226aa7837e6aeb07ff0e0265fad5e070e0ce30bdcdc85", "connect", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connect")
        _result = _implementation(plan)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connect"
        if _error.span is None:
            _error.span = {"end_byte":16401,"end_column":1,"end_line":564,"start_byte":12697,"start_column":1,"start_line":507}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connect", phase="implementation-call", span={"end_byte":16401,"end_column":1,"end_line":564,"start_byte":12697,"start_column":1,"start_line":507}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connect", phase="implementation-call", span={"end_byte":16401,"end_column":1,"end_line":564,"start_byte":12697,"start_column":1,"start_line":507}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_ConnectionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connect", phase="error", span={"end_byte":16401,"end_column":1,"end_line":564,"start_byte":12697,"start_column":1,"start_line":507}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connect", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.connect", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connected = _cott_match_value.value
            return (_cott_contract_condition(((connected == UNIT)), "real.pgcli.connect", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connect", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connect", clause="ensures:1", phase="ensures", span={"end_byte":16271,"end_column":52,"end_line":558,"start_byte":16224,"start_column":5,"start_line":558}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]:
    request = _cott_validate_abi(request, CatalogRefreshRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/refresh_catalog.py", "2294b349c8ba4b4872f62b24053abb743955f50982769b65d71cfec0bab9aa4c", "refresh_catalog", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.refresh_catalog")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.refresh_catalog"
        if _error.span is None:
            _error.span = {"end_byte":16697,"end_column":1,"end_line":572,"start_byte":16401,"start_column":1,"start_line":564}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.refresh_catalog", phase="implementation-call", span={"end_byte":16697,"end_column":1,"end_line":572,"start_byte":16401,"start_column":1,"start_line":564}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.refresh_catalog", phase="implementation-call", span={"end_byte":16697,"end_column":1,"end_line":572,"start_byte":16401,"start_column":1,"start_line":564}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Catalog, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_CatalogFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.refresh_catalog", phase="error", span={"end_byte":16697,"end_column":1,"end_line":572,"start_byte":16401,"start_column":1,"start_line":564}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.refresh_catalog", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_CatalogFailed:
        _cott_contract_condition(True, "real.pgcli.refresh_catalog", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (_cott_contract_condition((((catalog).limit == (request).limit)), "real.pgcli.refresh_catalog", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:0", phase="ensures", span={"end_byte":16549,"end_column":65,"end_line":565,"start_byte":16489,"start_column":5,"start_line":565}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (_cott_contract_condition(((len((catalog).relations) <= (request).limit)), "real.pgcli.refresh_catalog", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:1", phase="ensures", span={"end_byte":16622,"end_column":73,"end_line":566,"start_byte":16554,"start_column":5,"start_line":566}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Catalog, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_sql.py", "d3190705ccf619e22e552f54b7b82f084c88dfceeb61a4053a6551b56e1dd2ae", "complete_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":16778,"end_column":1,"end_line":575,"start_byte":16697,"start_column":1,"start_line":572}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":16778,"end_column":1,"end_line":575,"start_byte":16697,"start_column":1,"start_line":572}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":16778,"end_column":1,"end_line":575,"start_byte":16697,"start_column":1,"start_line":572}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    policy = _cott_validate_abi(policy, CompletionPolicy, path="$.policy")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_catalog_sql.py", "5835859d732f473b2d1732e5dac1f9cd638007bf8bdfe808a1ce367fcb3afbfc", "complete_catalog_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_catalog_sql")
        _result = _implementation(request, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_catalog_sql"
        if _error.span is None:
            _error.span = {"end_byte":16953,"end_column":1,"end_line":580,"start_byte":16778,"start_column":1,"start_line":575}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_catalog_sql", phase="implementation-call", span={"end_byte":16953,"end_column":1,"end_line":580,"start_byte":16778,"start_column":1,"start_line":575}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_catalog_sql", phase="implementation-call", span={"end_byte":16953,"end_column":1,"end_line":580,"start_byte":16778,"start_column":1,"start_line":575}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not (_cott_contract_condition(((len((_result).candidates) <= (policy).max_candidates)), "real.pgcli.complete_catalog_sql", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.complete_catalog_sql", clause="ensures:0", phase="ensures", span={"end_byte":16935,"end_column":59,"end_line":576,"start_byte":16881,"start_column":5,"start_line":576}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def highlight_sql(request: HighlightRequest) -> HighlightedSql:
    request = _cott_validate_abi(request, HighlightRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/highlight_sql.py", "6086c9e3d6a91cc86d084d10f763a5d0462e6631aa728f2b8a78431b9d2c8462", "highlight_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.highlight_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.highlight_sql"
        if _error.span is None:
            _error.span = {"end_byte":17032,"end_column":1,"end_line":583,"start_byte":16953,"start_column":1,"start_line":580}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.highlight_sql", phase="implementation-call", span={"end_byte":17032,"end_column":1,"end_line":583,"start_byte":16953,"start_column":1,"start_line":580}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.highlight_sql", phase="implementation-call", span={"end_byte":17032,"end_column":1,"end_line":583,"start_byte":16953,"start_column":1,"start_line":580}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HighlightedSql, path="$.return")
    _result = _cott_wrap_async_protocol(_result, HighlightedSql, path="$.return", validator=_cott_validate_abi)
    return _result

def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]:
    buffer = _cott_validate_abi(buffer, InputBuffer, path="$.buffer")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/plan_query.py", "f5a2f9dade43cedeff511c0a4dfcebed2d3181b0534c8d31f53578b8ddf720f3", "plan_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.plan_query")
        _result = _implementation(buffer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.plan_query"
        if _error.span is None:
            _error.span = {"end_byte":17208,"end_column":1,"end_line":590,"start_byte":17032,"start_column":1,"start_line":583}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.plan_query", phase="implementation-call", span={"end_byte":17208,"end_column":1,"end_line":590,"start_byte":17032,"start_column":1,"start_line":583}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.plan_query", phase="implementation-call", span={"end_byte":17208,"end_column":1,"end_line":590,"start_byte":17032,"start_column":1,"start_line":583}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryPlan, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.plan_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.plan_query", phase="error", span={"end_byte":17208,"end_column":1,"end_line":590,"start_byte":17032,"start_column":1,"start_line":583}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.plan_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.plan_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidSql:
        _cott_contract_condition(True, "real.pgcli.plan_query", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((plan).sql == (buffer).text)), "real.pgcli.plan_query", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.plan_query", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.plan_query", clause="ensures:0", phase="ensures", span={"end_byte":17156,"end_column":55,"end_line":584,"start_byte":17106,"start_column":5,"start_line":584}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryPlan, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer:
    buffer = _cott_validate_abi(buffer, InputBuffer, path="$.buffer")
    input = _cott_validate_abi(input, str, path="$.input")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/edit_multiline.py", "90035b5246b79b112cad6c5b41bb568f5887ddc22b09dbdef49124e01acc3e2d", "edit_multiline", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.edit_multiline")
        _result = _implementation(buffer, input)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.edit_multiline"
        if _error.span is None:
            _error.span = {"end_byte":17337,"end_column":1,"end_line":595,"start_byte":17208,"start_column":1,"start_line":590}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.edit_multiline", phase="implementation-call", span={"end_byte":17337,"end_column":1,"end_line":595,"start_byte":17208,"start_column":1,"start_line":590}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.edit_multiline", phase="implementation-call", span={"end_byte":17337,"end_column":1,"end_line":595,"start_byte":17208,"start_column":1,"start_line":590}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, InputBuffer, path="$.return")
    if not (_cott_contract_condition((((_result).cursor <= len((_result).text))), "real.pgcli.edit_multiline", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_multiline", clause="ensures:0", phase="ensures", span={"end_byte":17319,"end_column":45,"end_line":591,"start_byte":17279,"start_column":5,"start_line":591}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, InputBuffer, path="$.return", validator=_cott_validate_abi)
    return _result

def recognize_backslash(source: str) -> BackslashCommand:
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/recognize_backslash.py", "ac267cbf3cd57685ee6c5cbef8568e5835ad16573282bb57f617e82905b2e7a9", "recognize_backslash", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.recognize_backslash")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.recognize_backslash"
        if _error.span is None:
            _error.span = {"end_byte":17410,"end_column":1,"end_line":598,"start_byte":17337,"start_column":1,"start_line":595}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":17410,"end_column":1,"end_line":598,"start_byte":17337,"start_column":1,"start_line":595}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":17410,"end_column":1,"end_line":598,"start_byte":17337,"start_column":1,"start_line":595}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, BackslashCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, BackslashCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def parse_meta_command(source: str) -> MetaCommand:
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_meta_command.py", "297fa528e1b85630274002b06ccb68fa525e2f26360b41150aecc4c7f3f76dc0", "parse_meta_command", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_meta_command")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_meta_command"
        if _error.span is None:
            _error.span = {"end_byte":17477,"end_column":1,"end_line":601,"start_byte":17410,"start_column":1,"start_line":598}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_meta_command", phase="implementation-call", span={"end_byte":17477,"end_column":1,"end_line":601,"start_byte":17410,"start_column":1,"start_line":598}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_meta_command", phase="implementation-call", span={"end_byte":17477,"end_column":1,"end_line":601,"start_byte":17410,"start_column":1,"start_line":598}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, MetaCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, MetaCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def render_query(request: RenderRequest) -> RenderedQuery:
    request = _cott_validate_abi(request, RenderRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/render_query.py", "ca592a3dafa745cf08da62964142f4b1c83f9b0cc5d5fa352770deed2d7974e2", "render_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.render_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.render_query"
        if _error.span is None:
            _error.span = {"end_byte":17551,"end_column":1,"end_line":604,"start_byte":17477,"start_column":1,"start_line":601}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":17551,"end_column":1,"end_line":604,"start_byte":17477,"start_column":1,"start_line":601}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":17551,"end_column":1,"end_line":604,"start_byte":17477,"start_column":1,"start_line":601}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, RenderedQuery, path="$.return")
    _result = _cott_wrap_async_protocol(_result, RenderedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def format_query(request: FormatRequest) -> FormattedQuery:
    request = _cott_validate_abi(request, FormatRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/format_query.py", "73b8dba8aeff729966296924aef2012def06eea33166ef871b483b50430df6d0", "format_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.format_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.format_query"
        if _error.span is None:
            _error.span = {"end_byte":17681,"end_column":1,"end_line":609,"start_byte":17551,"start_column":1,"start_line":604}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.format_query", phase="implementation-call", span={"end_byte":17681,"end_column":1,"end_line":609,"start_byte":17551,"start_column":1,"start_line":604}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.format_query", phase="implementation-call", span={"end_byte":17681,"end_column":1,"end_line":609,"start_byte":17551,"start_column":1,"start_line":604}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, FormattedQuery, path="$.return")
    if not (_cott_contract_condition((((_result).truncated_rows <= (request).max_rows)), "real.pgcli.format_query", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.format_query", clause="ensures:0", phase="ensures", span={"end_byte":17663,"end_column":54,"end_line":605,"start_byte":17614,"start_column":5,"start_line":605}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FormattedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    connection = _cott_validate_abi(connection, ConnectionSettings, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_query.py", "7b2df1bdd153910a1cc81efa4c6ac35958e9e2457b86894ff7a30c0413f7d537", "execute_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_query")
        _result = _implementation(connection, sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_query"
        if _error.span is None:
            _error.span = {"end_byte":18001,"end_column":1,"end_line":617,"start_byte":17681,"start_column":1,"start_line":609}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":18001,"end_column":1,"end_line":617,"start_byte":17681,"start_column":1,"start_line":609}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":18001,"end_column":1,"end_line":617,"start_byte":17681,"start_column":1,"start_line":609}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryResult, DatabaseError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (DatabaseError_ConnectionFailed, DatabaseError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_query", phase="error", span={"end_byte":18001,"end_column":1,"end_line":617,"start_byte":17681,"start_column":1,"start_line":609}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.execute_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is DatabaseError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.execute_query", "error:1")
    if type(_result) is Err and type(_result.error) is DatabaseError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.execute_query", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            query_result = _cott_match_value.value
            return (_cott_contract_condition((((len((query_result).rows) == 0) or (len((query_result).columns) > 0))), "real.pgcli.execute_query", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.execute_query", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_query", clause="ensures:0", phase="ensures", span={"end_byte":17876,"end_column":98,"end_line":610,"start_byte":17783,"start_column":5,"start_line":610}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryResult, DatabaseError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]:
    request = _cott_validate_abi(request, QueryRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_planned_query.py", "e09b43fa876a3e2b49c6d6aa3a2b485939930a161a89f5704e00bacbb4d7f76a", "execute_planned_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_planned_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_planned_query"
        if _error.span is None:
            _error.span = {"end_byte":18296,"end_column":1,"end_line":625,"start_byte":18001,"start_column":1,"start_line":617}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_planned_query", phase="implementation-call", span={"end_byte":18296,"end_column":1,"end_line":625,"start_byte":18001,"start_column":1,"start_line":617}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_planned_query", phase="implementation-call", span={"end_byte":18296,"end_column":1,"end_line":625,"start_byte":18001,"start_column":1,"start_line":617}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExecutedQuery, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_planned_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_QueryFailed, ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_planned_query", phase="error", span={"end_byte":18296,"end_column":1,"end_line":625,"start_byte":18001,"start_column":1,"start_line":617}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_planned_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", "error:1")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            executed = _cott_match_value.value
            return (_cott_contract_condition(((len(((executed).result).rows) <= (request).max_rows)), "real.pgcli.execute_planned_query", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.execute_planned_query", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_planned_query", clause="ensures:0", phase="ensures", span={"end_byte":18167,"end_column":80,"end_line":618,"start_byte":18092,"start_column":5,"start_line":618}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExecutedQuery, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def begin_transaction(mode: TransactionMode) -> TransactionState:
    mode = _cott_validate_abi(mode, TransactionMode, path="$.mode")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/begin_transaction.py", "ec92118bdd509a043f4905764e3ad9e19ba87f71709a094f659ad769b5f5aa37", "begin_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.begin_transaction")
        _result = _implementation(mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.begin_transaction"
        if _error.span is None:
            _error.span = {"end_byte":18424,"end_column":1,"end_line":630,"start_byte":18296,"start_column":1,"start_line":625}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.begin_transaction", phase="implementation-call", span={"end_byte":18424,"end_column":1,"end_line":630,"start_byte":18296,"start_column":1,"start_line":625}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.begin_transaction", phase="implementation-call", span={"end_byte":18424,"end_column":1,"end_line":630,"start_byte":18296,"start_column":1,"start_line":625}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TransactionState, path="$.return")
    if not (_cott_contract_condition((((_result).mode == mode)), "real.pgcli.begin_transaction", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.begin_transaction", clause="ensures:0", phase="ensures", span={"end_byte":18392,"end_column":32,"end_line":626,"start_byte":18365,"start_column":5,"start_line":626}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TransactionState, path="$.return", validator=_cott_validate_abi)
    return _result

def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    transaction = _cott_validate_abi(transaction, TransactionState, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/commit_transaction.py", "4439b0712b434fd5569eb7f86b1420a7c6fbe7ded4e2558e81c8c9528592ed72", "commit_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.commit_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":18648,"end_column":1,"end_line":637,"start_byte":18424,"start_column":1,"start_line":630}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.commit_transaction", phase="implementation-call", span={"end_byte":18648,"end_column":1,"end_line":637,"start_byte":18424,"start_column":1,"start_line":630}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.commit_transaction", phase="implementation-call", span={"end_byte":18648,"end_column":1,"end_line":637,"start_byte":18424,"start_column":1,"start_line":630}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransactionState, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.commit_transaction", phase="error", span={"end_byte":18648,"end_column":1,"end_line":637,"start_byte":18424,"start_column":1,"start_line":630}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.commit_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.commit_transaction", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            committed = _cott_match_value.value
            return (_cott_contract_condition(((not (committed).active)), "real.pgcli.commit_transaction", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.commit_transaction", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.commit_transaction", clause="ensures:0", phase="ensures", span={"end_byte":18575,"end_column":57,"end_line":631,"start_byte":18523,"start_column":5,"start_line":631}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransactionState, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    transaction = _cott_validate_abi(transaction, TransactionState, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/rollback_transaction.py", "d1e13cd87069eab2d90c57eb50985c533854181187bdd30ec673c392cffdaca5", "rollback_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.rollback_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":18878,"end_column":1,"end_line":644,"start_byte":18648,"start_column":1,"start_line":637}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.rollback_transaction", phase="implementation-call", span={"end_byte":18878,"end_column":1,"end_line":644,"start_byte":18648,"start_column":1,"start_line":637}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.rollback_transaction", phase="implementation-call", span={"end_byte":18878,"end_column":1,"end_line":644,"start_byte":18648,"start_column":1,"start_line":637}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransactionState, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.rollback_transaction", phase="error", span={"end_byte":18878,"end_column":1,"end_line":644,"start_byte":18648,"start_column":1,"start_line":637}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.rollback_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.rollback_transaction", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rolled_back = _cott_match_value.value
            return (_cott_contract_condition(((not (rolled_back).active)), "real.pgcli.rollback_transaction", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.rollback_transaction", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.rollback_transaction", clause="ensures:0", phase="ensures", span={"end_byte":18805,"end_column":61,"end_line":638,"start_byte":18749,"start_column":5,"start_line":638}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransactionState, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]:
    """Read policy.path as the HistoryEntry JSON format and apply HistoryPolicy
normalization only after validating every row, including rows later trimmed.
A missing file is an empty success. Invalid UTF-8/JSON/field types, a non-array
root, a non-regular or symlink leaf, and other I/O failures return
HistoryFailed(path=policy.path, message=a fixed nonsecret category).
Reject files larger than 16 MiB using a bounded read; do not execute file content."""
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/load_history.py", "9b164aa2a24f1d74acd154275ed34c392df2868f703de29ca68f577f0024733c", "load_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.load_history")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.load_history"
        if _error.span is None:
            _error.span = {"end_byte":19586,"end_column":1,"end_line":660,"start_byte":18878,"start_column":1,"start_line":644}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.load_history", phase="implementation-call", span={"end_byte":19586,"end_column":1,"end_line":660,"start_byte":18878,"start_column":1,"start_line":644}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.load_history", phase="implementation-call", span={"end_byte":19586,"end_column":1,"end_line":660,"start_byte":18878,"start_column":1,"start_line":644}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[HistoryEntry], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_HistoryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.load_history", phase="error", span={"end_byte":19586,"end_column":1,"end_line":660,"start_byte":18878,"start_column":1,"start_line":644}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.load_history", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_HistoryFailed:
        _cott_contract_condition(True, "real.pgcli.load_history", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return (_cott_contract_condition(((len(entries) <= (policy).max_entries)), "real.pgcli.load_history", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.load_history", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_history", clause="ensures:1", phase="ensures", span={"end_byte":19522,"end_column":68,"end_line":654,"start_byte":19459,"start_column":5,"start_line":654}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[HistoryEntry], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]:
    """Apply HistoryPolicy normalization, then write the HistoryEntry JSON format
with ensure_ascii=False, compact separators and one final newline. Preserve
field values exactly and reject serialized data larger than 16 MiB.
Replace policy.path atomically using an exclusive same-directory temporary
file, mode 0600, flush/fsync then os.replace, followed by parent directory fsync.
Parent directories are not created. Reject a symlink/non-regular existing leaf.
On precommit failure preserve the original and remove the temporary file.
Return HistoryFailed(path=policy.path, message=a fixed nonsecret category) for
serialization or I/O failure; never leave a partially truncated history file."""
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    entries = _cott_validate_abi(entries, CottList[HistoryEntry], path="$.entries")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/save_history.py", "f2cfc33272889fbabf2b045e9ee718837d5a223b30e9545431298d3bdc3e5936", "save_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.save_history")
        _result = _implementation(policy, entries)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.save_history"
        if _error.span is None:
            _error.span = {"end_byte":20536,"end_column":1,"end_line":679,"start_byte":19586,"start_column":1,"start_line":660}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.save_history", phase="implementation-call", span={"end_byte":20536,"end_column":1,"end_line":679,"start_byte":19586,"start_column":1,"start_line":660}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.save_history", phase="implementation-call", span={"end_byte":20536,"end_column":1,"end_line":679,"start_byte":19586,"start_column":1,"start_line":660}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_HistoryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.save_history", phase="error", span={"end_byte":20536,"end_column":1,"end_line":679,"start_byte":19586,"start_column":1,"start_line":660}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.save_history", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_HistoryFailed:
        _cott_contract_condition(True, "real.pgcli.save_history", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition(((saved == UNIT)), "real.pgcli.save_history", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.save_history", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.save_history", clause="ensures:1", phase="ensures", span={"end_byte":20471,"end_column":44,"end_line":673,"start_byte":20432,"start_column":5,"start_line":673}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]:
    """Append entry to entries, then apply the exact HistoryPolicy normalization.
This is pure list transformation with no clock or filesystem access."""
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    entries = _cott_validate_abi(entries, CottList[HistoryEntry], path="$.entries")
    entry = _cott_validate_abi(entry, HistoryEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/remember_history.py", "1493972c82b104753924232716b7a7408b1c06b9e4d6948ce37878b2d67cceea", "remember_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.remember_history")
        _result = _implementation(policy, entries, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.remember_history"
        if _error.span is None:
            _error.span = {"end_byte":20902,"end_column":1,"end_line":693,"start_byte":20536,"start_column":1,"start_line":679}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.remember_history", phase="implementation-call", span={"end_byte":20902,"end_column":1,"end_line":693,"start_byte":20536,"start_column":1,"start_line":679}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.remember_history", phase="implementation-call", span={"end_byte":20902,"end_column":1,"end_line":693,"start_byte":20536,"start_column":1,"start_line":679}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[HistoryEntry], path="$.return")
    if not (_cott_contract_condition(((len(_result) <= (policy).max_entries)), "real.pgcli.remember_history", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.remember_history", clause="ensures:1", phase="ensures", span={"end_byte":20884,"end_column":45,"end_line":689,"start_byte":20844,"start_column":5,"start_line":689}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[HistoryEntry], path="$.return", validator=_cott_validate_abi)
    return _result

def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]:
    """Read store.path as the Favorite JSON format; a missing file is an empty success.
Preserve all valid entries in file order; more than store.max_entries is an
error, not truncation. Validate every row, including tags and duplicate names.
Reject invalid UTF-8/JSON, files over 16 MiB, non-regular/symlink leaves and
genuine I/O failures. Return FavoriteFailed(name=str(store.path)) for all file,
shape, duplicate-name or capacity failures. Do not silently skip invalid rows."""
    store = _cott_validate_abi(store, FavoriteStore, path="$.store")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/load_favorites.py", "fe16575d3529392af0724826a3874808345eef264b3dd9d74ce94c9ac97bc706", "load_favorites", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.load_favorites")
        _result = _implementation(store)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.load_favorites"
        if _error.span is None:
            _error.span = {"end_byte":21634,"end_column":1,"end_line":709,"start_byte":20902,"start_column":1,"start_line":693}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.load_favorites", phase="implementation-call", span={"end_byte":21634,"end_column":1,"end_line":709,"start_byte":20902,"start_column":1,"start_line":693}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.load_favorites", phase="implementation-call", span={"end_byte":21634,"end_column":1,"end_line":709,"start_byte":20902,"start_column":1,"start_line":693}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[Favorite], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.load_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_FavoriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.load_favorites", phase="error", span={"end_byte":21634,"end_column":1,"end_line":709,"start_byte":20902,"start_column":1,"start_line":693}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.load_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.load_favorites", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.load_favorites", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            favorites = _cott_match_value.value
            return (_cott_contract_condition(((len(favorites) <= (store).max_entries)), "real.pgcli.load_favorites", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.load_favorites", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_favorites", clause="ensures:1", phase="ensures", span={"end_byte":21569,"end_column":71,"end_line":703,"start_byte":21503,"start_column":5,"start_line":703}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[Favorite], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]:
    """Validate Favorite names and capacity exactly as the persistence format requires,
retaining input order. Write UTF-8 JSON with ensure_ascii=False, compact
separators and one newline; reject serialized data over 16 MiB.
Use an exclusive same-directory temporary file, mode 0600, flush/fsync,
os.replace and parent fsync. Do not create parents or follow symlink leaves;
preserve the old file and remove the temporary file on precommit failure.
Every validation/serialization/I/O failure is FavoriteFailed(name=str(store.path))."""
    store = _cott_validate_abi(store, FavoriteStore, path="$.store")
    favorites = _cott_validate_abi(favorites, CottList[Favorite], path="$.favorites")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/save_favorites.py", "c024d48c7b414f7473caa4fde683f221452b4c5c8347fd97f38620b94e95a148", "save_favorites", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.save_favorites")
        _result = _implementation(store, favorites)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.save_favorites"
        if _error.span is None:
            _error.span = {"end_byte":22414,"end_column":1,"end_line":726,"start_byte":21634,"start_column":1,"start_line":709}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.save_favorites", phase="implementation-call", span={"end_byte":22414,"end_column":1,"end_line":726,"start_byte":21634,"start_column":1,"start_line":709}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.save_favorites", phase="implementation-call", span={"end_byte":22414,"end_column":1,"end_line":726,"start_byte":21634,"start_column":1,"start_line":709}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.save_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_FavoriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.save_favorites", phase="error", span={"end_byte":22414,"end_column":1,"end_line":726,"start_byte":21634,"start_column":1,"start_line":709}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.save_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.save_favorites", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.save_favorites", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition(((saved == UNIT)), "real.pgcli.save_favorites", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.save_favorites", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.save_favorites", clause="ensures:1", phase="ensures", span={"end_byte":22348,"end_column":44,"end_line":720,"start_byte":22309,"start_column":5,"start_line":720}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]:
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    request = _cott_validate_abi(request, ImportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/import_delimited.py", "a2a1b0fe167730f6c5f79111d81b8c945844bf928c70569eb5d191ec51eb597c", "import_delimited", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.import_delimited")
        _result = _implementation(plan, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.import_delimited"
        if _error.span is None:
            _error.span = {"end_byte":22712,"end_column":1,"end_line":737,"start_byte":22414,"start_column":1,"start_line":726}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.import_delimited", phase="implementation-call", span={"end_byte":22712,"end_column":1,"end_line":737,"start_byte":22414,"start_column":1,"start_line":726}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.import_delimited", phase="implementation-call", span={"end_byte":22712,"end_column":1,"end_line":737,"start_byte":22414,"start_column":1,"start_line":726}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.import_delimited", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ImportFailed, ClientError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.import_delimited", phase="error", span={"end_byte":22712,"end_column":1,"end_line":737,"start_byte":22414,"start_column":1,"start_line":726}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.import_delimited", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.import_delimited", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_ImportFailed:
        _cott_contract_condition(True, "real.pgcli.import_delimited", "error:1")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.import_delimited", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            imported = _cott_match_value.value
            return (_cott_contract_condition((((imported).rows <= (request).max_rows)), "real.pgcli.import_delimited", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.import_delimited", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.import_delimited", clause="ensures:0", phase="ensures", span={"end_byte":22599,"end_column":69,"end_line":730,"start_byte":22535,"start_column":5,"start_line":730}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]:
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    request = _cott_validate_abi(request, ExportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/export_query.py", "0e230f1c5ba9f41980ddf05e701e7de24ba4a643a2673e18447866f97d58bd6e", "export_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.export_query")
        _result = _implementation(plan, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.export_query"
        if _error.span is None:
            _error.span = {"end_byte":23006,"end_column":1,"end_line":748,"start_byte":22712,"start_column":1,"start_line":737}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.export_query", phase="implementation-call", span={"end_byte":23006,"end_column":1,"end_line":748,"start_byte":22712,"start_column":1,"start_line":737}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.export_query", phase="implementation-call", span={"end_byte":23006,"end_column":1,"end_line":748,"start_byte":22712,"start_column":1,"start_line":737}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.export_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ExportFailed, ClientError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.export_query", phase="error", span={"end_byte":23006,"end_column":1,"end_line":748,"start_byte":22712,"start_column":1,"start_line":737}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.export_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.export_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_ExportFailed:
        _cott_contract_condition(True, "real.pgcli.export_query", "error:1")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.export_query", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            exported = _cott_match_value.value
            return (_cott_contract_condition((((exported).rows <= (request).max_rows)), "real.pgcli.export_query", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.export_query", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.export_query", clause="ensures:0", phase="ensures", span={"end_byte":22893,"end_column":69,"end_line":741,"start_byte":22829,"start_column":5,"start_line":741}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    request = _cott_validate_abi(request, EditorRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/edit_in_editor.py", "2117fd9d5077d994d94210011f50a76f9f7a195cf496caccb727e681e5361e24", "edit_in_editor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.edit_in_editor")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.edit_in_editor"
        if _error.span is None:
            _error.span = {"end_byte":23225,"end_column":1,"end_line":755,"start_byte":23006,"start_column":1,"start_line":748}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.edit_in_editor", phase="implementation-call", span={"end_byte":23225,"end_column":1,"end_line":755,"start_byte":23006,"start_column":1,"start_line":748}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.edit_in_editor", phase="implementation-call", span={"end_byte":23225,"end_column":1,"end_line":755,"start_byte":23006,"start_column":1,"start_line":748}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[InputBuffer, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.edit_in_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_EditorFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.edit_in_editor", phase="error", span={"end_byte":23225,"end_column":1,"end_line":755,"start_byte":23006,"start_column":1,"start_line":748}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.edit_in_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.edit_in_editor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_EditorFailed:
        _cott_contract_condition(True, "real.pgcli.edit_in_editor", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            buffer = _cott_match_value.value
            return (_cott_contract_condition((((buffer).cursor <= len((buffer).text))), "real.pgcli.edit_in_editor", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.edit_in_editor", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_in_editor", clause="ensures:0", phase="ensures", span={"end_byte":23150,"end_column":66,"end_line":749,"start_byte":23089,"start_column":5,"start_line":749}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[InputBuffer, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def page_output(request: PagerRequest) -> Result[Unit, ClientError]:
    request = _cott_validate_abi(request, PagerRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/page_output.py", "8ac906709204086e606e66dd53dddb604681c68264c3f655f66c8020361ff404", "page_output", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.page_output")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.page_output"
        if _error.span is None:
            _error.span = {"end_byte":23410,"end_column":1,"end_line":762,"start_byte":23225,"start_column":1,"start_line":755}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.page_output", phase="implementation-call", span={"end_byte":23410,"end_column":1,"end_line":762,"start_byte":23225,"start_column":1,"start_line":755}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.page_output", phase="implementation-call", span={"end_byte":23410,"end_column":1,"end_line":762,"start_byte":23225,"start_column":1,"start_line":755}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.page_output", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_PagerFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.page_output", phase="error", span={"end_byte":23410,"end_column":1,"end_line":762,"start_byte":23225,"start_column":1,"start_line":755}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.page_output", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.page_output", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_PagerFailed:
        _cott_contract_condition(True, "real.pgcli.page_output", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            paged = _cott_match_value.value
            return (_cott_contract_condition(((paged == UNIT)), "real.pgcli.page_output", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.page_output", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.page_output", clause="ensures:0", phase="ensures", span={"end_byte":23336,"end_column":44,"end_line":756,"start_byte":23297,"start_column":5,"start_line":756}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]:
    request = _cott_validate_abi(request, NotificationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/receive_notifications.py", "b6f5004e26b1e7e8329fe0799927fb667954b28fa8179df6711eeca1e59f6e3b", "receive_notifications", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.receive_notifications")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.receive_notifications"
        if _error.span is None:
            _error.span = {"end_byte":23675,"end_column":1,"end_line":769,"start_byte":23410,"start_column":1,"start_line":762}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.receive_notifications", phase="implementation-call", span={"end_byte":23675,"end_column":1,"end_line":769,"start_byte":23410,"start_column":1,"start_line":762}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.receive_notifications", phase="implementation-call", span={"end_byte":23675,"end_column":1,"end_line":769,"start_byte":23410,"start_column":1,"start_line":762}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[Notification], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.receive_notifications", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_NotificationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.receive_notifications", phase="error", span={"end_byte":23675,"end_column":1,"end_line":769,"start_byte":23410,"start_column":1,"start_line":762}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.receive_notifications", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.receive_notifications", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_NotificationFailed:
        _cott_contract_condition(True, "real.pgcli.receive_notifications", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            notifications = _cott_match_value.value
            return (_cott_contract_condition(((len(notifications) <= (request).max_notifications)), "real.pgcli.receive_notifications", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.receive_notifications", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.receive_notifications", clause="ensures:0", phase="ensures", span={"end_byte":23595,"end_column":87,"end_line":763,"start_byte":23513,"start_column":5,"start_line":763}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[Notification], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]:
    request = _cott_validate_abi(request, WatchRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/watch_query.py", "1e8de31ca575f4254f67e78da0bb2bd215a87d269d5ca6b7beb29a8b75bbafde", "watch_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.watch_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.watch_query"
        if _error.span is None:
            _error.span = {"end_byte":23957,"end_column":1,"end_line":777,"start_byte":23675,"start_column":1,"start_line":769}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.watch_query", phase="implementation-call", span={"end_byte":23957,"end_column":1,"end_line":777,"start_byte":23675,"start_column":1,"start_line":769}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.watch_query", phase="implementation-call", span={"end_byte":23957,"end_column":1,"end_line":777,"start_byte":23675,"start_column":1,"start_line":769}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WatchResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.watch_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_QueryFailed, ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.watch_query", phase="error", span={"end_byte":23957,"end_column":1,"end_line":777,"start_byte":23675,"start_column":1,"start_line":769}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.watch_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.watch_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.watch_query", "error:1")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.watch_query", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            watched = _cott_match_value.value
            return (_cott_contract_condition((((watched).executions <= (request).max_iterations)), "real.pgcli.watch_query", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.watch_query", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.watch_query", clause="ensures:0", phase="ensures", span={"end_byte":23828,"end_column":79,"end_line":770,"start_byte":23754,"start_column":5,"start_line":770}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[WatchResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]:
    invocation = _cott_validate_abi(invocation, CommandInvocation, path="$.invocation")
    options = _cott_validate_abi(options, SessionOptions, path="$.options")
    catalog = _cott_validate_abi(catalog, Catalog, path="$.catalog")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run_meta_command.py", "087fccfd271395e6bb6a455698a940409196dc702bb51b093b850b9e4bb6a839", "run_meta_command", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run_meta_command")
        _result = _implementation(invocation, options, catalog)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run_meta_command"
        if _error.span is None:
            _error.span = {"end_byte":24669,"end_column":1,"end_line":798,"start_byte":23957,"start_column":1,"start_line":777}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.run_meta_command", phase="implementation-call", span={"end_byte":24669,"end_column":1,"end_line":798,"start_byte":23957,"start_column":1,"start_line":777}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run_meta_command", phase="implementation-call", span={"end_byte":24669,"end_column":1,"end_line":798,"start_byte":23957,"start_column":1,"start_line":777}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CommandResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.run_meta_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidCommand, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_ImportFailed, ClientError_ExportFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_NotificationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.run_meta_command", phase="error", span={"end_byte":24669,"end_column":1,"end_line":798,"start_byte":23957,"start_column":1,"start_line":777}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.run_meta_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidCommand:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:1")
    if type(_result) is Err and type(_result.error) is ClientError_CatalogFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:2")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:3")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:4")
    if type(_result) is Err and type(_result.error) is ClientError_ImportFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:5")
    if type(_result) is Err and type(_result.error) is ClientError_ExportFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:6")
    if type(_result) is Err and type(_result.error) is ClientError_HistoryFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:7")
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:8")
    if type(_result) is Err and type(_result.error) is ClientError_EditorFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:9")
    if type(_result) is Err and type(_result.error) is ClientError_PagerFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:10")
    if type(_result) is Err and type(_result.error) is ClientError_NotificationFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:11")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            step = _cott_match_value.value
            return (_cott_contract_condition((((step).quit or (((step).buffer).cursor <= len(((step).buffer).text)))), "real.pgcli.run_meta_command", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.run_meta_command", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_meta_command", clause="ensures:0", phase="ensures", span={"end_byte":24191,"end_column":87,"end_line":782,"start_byte":24109,"start_column":5,"start_line":782}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CommandResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_interactive(request: InteractiveRequest) -> Result[Unit, ClientError]:
    request = _cott_validate_abi(request, InteractiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run_interactive.py", "104dd3b79d04c96f44ba13d73363ffd1ae822003a7b84df42b0dc7515d2763f1", "run_interactive", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run_interactive")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run_interactive"
        if _error.span is None:
            _error.span = {"end_byte":25283,"end_column":1,"end_line":815,"start_byte":24669,"start_column":1,"start_line":798}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.run_interactive", phase="implementation-call", span={"end_byte":25283,"end_column":1,"end_line":815,"start_byte":24669,"start_column":1,"start_line":798}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run_interactive", phase="implementation-call", span={"end_byte":25283,"end_column":1,"end_line":815,"start_byte":24669,"start_column":1,"start_line":798}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.run_interactive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_NotificationFailed, ClientError_TerminalFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.run_interactive", phase="error", span={"end_byte":25283,"end_column":1,"end_line":815,"start_byte":24669,"start_column":1,"start_line":798}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.run_interactive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.run_interactive", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidCommand:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:1")
    if type(_result) is Err and type(_result.error) is ClientError_InvalidSql:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:2")
    if type(_result) is Err and type(_result.error) is ClientError_CatalogFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:3")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:4")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:5")
    if type(_result) is Err and type(_result.error) is ClientError_HistoryFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:6")
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:7")
    if type(_result) is Err and type(_result.error) is ClientError_EditorFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:8")
    if type(_result) is Err and type(_result.error) is ClientError_PagerFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:9")
    if type(_result) is Err and type(_result.error) is ClientError_NotificationFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:10")
    if type(_result) is Err and type(_result.error) is ClientError_TerminalFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:11")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            finished = _cott_match_value.value
            return (_cott_contract_condition(((finished == UNIT)), "real.pgcli.run_interactive", "ensures:0"))
        _cott_contract_condition((False), "real.pgcli.run_interactive", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_interactive", clause="ensures:0", phase="ensures", span={"end_byte":24796,"end_column":50,"end_line":799,"start_byte":24751,"start_column":5,"start_line":799}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """Run a real psycopg line-oriented PostgreSQL REPL. arguments excludes argv[0].
Use argparse with program name pgcli-cott, optional positional DSN, -h/--host,
-p/--port, -U/--username, -d/--dbname, -c/--command and --help. Reserve -h for
host, not help. Unknown or malformed arguments print usage to stderr and exit 2;
--help prints usage and exits 0 without connecting. Nonempty supplied flags
override the DSN; unspecified connection fields retain libpq defaults and
PGHOST/PGPORT/PGUSER/PGDATABASE/PGPASSWORD environment behavior. Never accept a
password argument, echo credentials or disable the DSN's TLS verification.
Connect once using psycopg.connect with autocommit=True and connect_timeout=10.
With -c, execute that complete SQL string once. Otherwise read one complete
SQL command per stdin line (no multiline parser); skip empty lines and leave
on a line equal to \\q or quit after stripping. EOF is normal termination.
Print "pgcli> " only when stdin is a terminal. Execute SQL through a real
cursor; for row results print tab-separated column names followed by rows in
driver order, rendering SQL NULL as NULL and other cells with str. For
commands without rows print cursor.statusmessage when nonempty.
On a query error print only a fixed "query failed" message to stderr; in -c
mode exit 1, otherwise continue accepting lines but remember failure. Normal
EOF/quit exits 0 if every query succeeded, otherwise 1. Connection or I/O
failure exits 1 with a fixed category message. KeyboardInterrupt exits 130.
Close every cursor and the connection before sys.exit; never log raw exception
text or leave a background connection. This entrypoint does not create a hidden
global session or infer a richer argument grammar from the upstream project."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run.py", "96533d09929ffd53eccdca33e5fc2ccad95d40d86478c4888b7a7a032859c97e", "run", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run"
        if _error.span is None:
            _error.span = {"end_byte":27365,"end_column":1,"end_line":852,"start_byte":25283,"start_column":1,"start_line":815}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run", phase="implementation-call", span={"end_byte":27365,"end_column":1,"end_line":852,"start_byte":25283,"start_column":1,"start_line":815}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.pgcli.run", phase="return", span={"end_byte":27365,"end_column":1,"end_line":852,"start_byte":25283,"start_column":1,"start_line":815}, expected="Never", actual=repr(_result))

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "ClientError", "ClientError_CatalogFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionError_TlsInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_ClearOutput", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListNotifications", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_Password", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetLogFile", "MetaCommand_SetOptions", "MetaCommand_SetOutput", "MetaCommand_SetPager", "MetaCommand_Shell", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_VerboseErrors", "MetaCommand_Watch", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SessionOptions", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransferResult", "WatchRequest", "WatchResult", "begin_transaction", "commit_transaction", "complete_catalog_sql", "complete_sql", "connect", "edit_in_editor", "edit_multiline", "execute_planned_query", "execute_query", "export_query", "format_query", "highlight_sql", "import_delimited", "load_favorites", "load_history", "page_output", "parse_dsn", "parse_meta_command", "plan_query", "prompt_policy", "receive_notifications", "recognize_backslash", "refresh_catalog", "remember_history", "render_query", "resolve_connection", "resolve_connection_plan", "resolve_credential", "resolve_profile", "rollback_transaction", "run", "run_interactive", "run_meta_command", "save_favorites", "save_history", "watch_query"]
