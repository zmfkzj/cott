from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.pgcli_types import BackslashCommand, BackslashCommand_Describe, BackslashCommand_Help, BackslashCommand_Quit, BackslashCommand_Tables, BackslashCommand_Unknown, Catalog, CatalogRefreshRequest, ClientError, ClientError_CatalogFailed, ClientError_EditorFailed, ClientError_ExportFailed, ClientError_FavoriteFailed, ClientError_HistoryFailed, ClientError_ImportFailed, ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_NotificationFailed, ClientError_PagerFailed, ClientError_QueryFailed, ClientError_TerminalFailed, ClientError_TransactionFailed, ClientError_UnsupportedFormat, ColumnCatalog, CommandInvocation, CommandResult, CompletionPolicy, CompletionRequest, CompletionResult, ConnectionError, ConnectionError_ConnectionFailed, ConnectionError_CredentialUnavailable, ConnectionError_InvalidDsn, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionError_ProfileMissing, ConnectionError_PromptDisabled, ConnectionError_SshInvalid, ConnectionError_TlsInvalid, ConnectionInputs, ConnectionPlan, ConnectionProfile, ConnectionRequest, ConnectionSettings, CredentialRequest, CredentialResolution, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, EditorRequest, EnvironmentInputs, ExecutedQuery, ExportRequest, Favorite, FavoriteStore, FormatRequest, FormattedQuery, HighlightRequest, HighlightedSql, HistoryEntry, HistoryPolicy, ImportRequest, InputBuffer, InteractiveRequest, MetaCommand, MetaCommand_ClearOutput, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery, MetaCommand_Describe, MetaCommand_Echo, MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_Expanded, MetaCommand_Favorite, MetaCommand_Help, MetaCommand_History, MetaCommand_ListDataTypes, MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains, MetaCommand_ListExtensions, MetaCommand_ListFavorites, MetaCommand_ListForeignTables, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListNotifications, MetaCommand_ListPrivileges, MetaCommand_ListRoles, MetaCommand_ListSchemas, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews, MetaCommand_NamedQuery, MetaCommand_Password, MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho, MetaCommand_Quit, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery, MetaCommand_SetFormat, MetaCommand_SetLogFile, MetaCommand_SetOptions, MetaCommand_SetOutput, MetaCommand_SetPager, MetaCommand_Shell, MetaCommand_ShowFunction, MetaCommand_SqlHelp, MetaCommand_Timing, MetaCommand_Unknown, MetaCommand_VerboseErrors, MetaCommand_Watch, MetaCommand_WriteBuffer, Notification, NotificationRequest, PagerRequest, PasswordSource, PasswordSource_Environment, PasswordSource_Keyring, PasswordSource_None, PasswordSource_Prompt, PasswordSource_Supplied, PromptAction, PromptAction_PromptPassword, PromptAction_UsePassword, QueryPlan, QueryRequest, QueryResult, RelationCatalog, RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery, RoutineCatalog, SessionOptions, SshSettings, TableCatalog, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical, TlsSettings, TransactionMode, TransactionMode_AutoCommit, TransactionMode_Manual, TransactionMode_ReadOnly, TransactionState, TransferResult, WatchRequest, WatchResult

def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]:
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_dsn.py", "84a69acff381f004d67d25789a36b6b80b51bf1112e5ce261c462736c7aced0d", "parse_dsn", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_dsn")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_dsn"
        if _error.span is None:
            _error.span = {"end_byte":7977,"end_column":1,"end_line":415,"start_byte":7796,"start_column":1,"start_line":408}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_dsn", phase="implementation-call", span={"end_byte":7977,"end_column":1,"end_line":415,"start_byte":7796,"start_column":1,"start_line":408}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_dsn", phase="implementation-call", span={"end_byte":7977,"end_column":1,"end_line":415,"start_byte":7796,"start_column":1,"start_line":408}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionInputs, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.parse_dsn", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_InvalidDsn,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.parse_dsn", phase="error", span={"end_byte":7977,"end_column":1,"end_line":415,"start_byte":7796,"start_column":1,"start_line":408}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.parse_dsn", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (((inputs).database != ""))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.parse_dsn", clause="ensures:0", phase="ensures", span={"end_byte":7921,"end_column":55,"end_line":409,"start_byte":7871,"start_column":5,"start_line":409}, expected="true", actual="false")
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
            _error.span = {"end_byte":8214,"end_column":1,"end_line":425,"start_byte":7977,"start_column":1,"start_line":415}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_profile", phase="implementation-call", span={"end_byte":8214,"end_column":1,"end_line":425,"start_byte":7977,"start_column":1,"start_line":415}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_profile", phase="implementation-call", span={"end_byte":8214,"end_column":1,"end_line":425,"start_byte":7977,"start_column":1,"start_line":415}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionProfile, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_ProfileMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_profile", phase="error", span={"end_byte":8214,"end_column":1,"end_line":425,"start_byte":7977,"start_column":1,"start_line":415}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            profile = _cott_match_value.value
            return (((profile).name == name))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_profile", clause="ensures:0", phase="ensures", span={"end_byte":8154,"end_column":55,"end_line":419,"start_byte":8104,"start_column":5,"start_line":419}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionProfile, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    inputs = _cott_validate_abi(inputs, ConnectionInputs, path="$.inputs")
    environment = _cott_validate_abi(environment, EnvironmentInputs, path="$.environment")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection.py", "fffa7d04b57138877963b17c3bb577067843286f326b5dad7f5421790b5ea649", "resolve_connection", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection")
        _result = _implementation(inputs, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection"
        if _error.span is None:
            _error.span = {"end_byte":9254,"end_column":1,"end_line":440,"start_byte":8214,"start_column":1,"start_line":425}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":9254,"end_column":1,"end_line":440,"start_byte":8214,"start_column":1,"start_line":425}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":9254,"end_column":1,"end_line":440,"start_byte":8214,"start_column":1,"start_line":425}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionSettings, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_MissingDatabase, ConnectionError_InvalidPort,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection", phase="error", span={"end_byte":9254,"end_column":1,"end_line":440,"start_byte":8214,"start_column":1,"start_line":425}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).host != "") and ((settings).host == (inputs).host)) or (((inputs).host == "") and ((settings).host == (environment).host))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:0", phase="ensures", span={"end_byte":8503,"end_column":151,"end_line":429,"start_byte":8357,"start_column":5,"start_line":429}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).port != "") and ((settings).port == (inputs).port)) or (((inputs).port == "") and ((settings).port == (environment).port))))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:1", phase="ensures", span={"end_byte":8654,"end_column":151,"end_line":430,"start_byte":8508,"start_column":5,"start_line":430}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).user != "") and ((settings).user == (inputs).user)) or (((inputs).user == "") and ((settings).user == (environment).user))))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:2", phase="ensures", span={"end_byte":8805,"end_column":151,"end_line":431,"start_byte":8659,"start_column":5,"start_line":431}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).password != "") and ((settings).password == (inputs).password)) or (((inputs).password == "") and ((settings).password == (environment).password))))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:3", phase="ensures", span={"end_byte":8980,"end_column":175,"end_line":432,"start_byte":8810,"start_column":5,"start_line":432}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (((((inputs).database != "") and ((settings).database == (inputs).database)) or (((inputs).database == "") and ((settings).database == (environment).database))))
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:4", phase="ensures", span={"end_byte":9155,"end_column":175,"end_line":433,"start_byte":8985,"start_column":5,"start_line":433}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionSettings, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]:
    request = _cott_validate_abi(request, ConnectionRequest, path="$.request")
    profile = _cott_validate_abi(profile, Option[ConnectionProfile], path="$.profile")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection_plan.py", "6424b38d66f539206fbfaad45173b78fc1de31680f5dbfd797539dea1ba95ff8", "resolve_connection_plan", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection_plan")
        _result = _implementation(request, profile)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection_plan"
        if _error.span is None:
            _error.span = {"end_byte":9669,"end_column":1,"end_line":454,"start_byte":9254,"start_column":1,"start_line":440}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection_plan", phase="implementation-call", span={"end_byte":9669,"end_column":1,"end_line":454,"start_byte":9254,"start_column":1,"start_line":440}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection_plan", phase="implementation-call", span={"end_byte":9669,"end_column":1,"end_line":454,"start_byte":9254,"start_column":1,"start_line":440}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionPlan, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection_plan", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_MissingDatabase, ConnectionError_InvalidPort, ConnectionError_InvalidDsn, ConnectionError_TlsInvalid, ConnectionError_SshInvalid,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection_plan", phase="error", span={"end_byte":9669,"end_column":1,"end_line":454,"start_byte":9254,"start_column":1,"start_line":440}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection_plan", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return ((((plan).settings).database != ""))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:0", phase="ensures", span={"end_byte":9459,"end_column":60,"end_line":444,"start_byte":9404,"start_column":5,"start_line":444}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionPlan, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]:
    no_prompt = _cott_validate_abi(no_prompt, bool, path="$.no_prompt")
    password = _cott_validate_abi(password, str, path="$.password")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((no_prompt and (password == ""))):
        _expected_error = ConnectionError_PromptDisabled
        _expected_error_span = {"end_byte":9988,"end_column":75,"end_line":457,"start_byte":9918,"start_column":5,"start_line":457}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/prompt_policy.py", "67253ee5c41c6b7033ffe13438f7206eec982f8c5c9ff1a02474de5ab9a0756e", "prompt_policy", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.prompt_policy")
        _result = _implementation(no_prompt, password)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.prompt_policy"
        if _error.span is None:
            _error.span = {"end_byte":10006,"end_column":1,"end_line":461,"start_byte":9669,"start_column":1,"start_line":454}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":10006,"end_column":1,"end_line":461,"start_byte":9669,"start_column":1,"start_line":454}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":10006,"end_column":1,"end_line":461,"start_byte":9669,"start_column":1,"start_line":454}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PromptAction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.prompt_policy", phase="error", span={"end_byte":10006,"end_column":1,"end_line":461,"start_byte":9669,"start_column":1,"start_line":454}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            action = _cott_match_value.value
            return ((((password != "") and (action == PromptAction_UsePassword())) or ((password == "") and (action == PromptAction_PromptPassword()))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.prompt_policy", clause="ensures:0", phase="ensures", span={"end_byte":9912,"end_column":153,"end_line":455,"start_byte":9764,"start_column":5,"start_line":455}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PromptAction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]:
    request = _cott_validate_abi(request, CredentialRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_credential.py", "145066fbfd8fab7b2ac1cade9fe8186b8431767040ac06713388267059abac50", "resolve_credential", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_credential")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_credential"
        if _error.span is None:
            _error.span = {"end_byte":10340,"end_column":1,"end_line":469,"start_byte":10006,"start_column":1,"start_line":461}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_credential", phase="implementation-call", span={"end_byte":10340,"end_column":1,"end_line":469,"start_byte":10006,"start_column":1,"start_line":461}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_credential", phase="implementation-call", span={"end_byte":10340,"end_column":1,"end_line":469,"start_byte":10006,"start_column":1,"start_line":461}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CredentialResolution, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_credential", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_CredentialUnavailable, ConnectionError_PromptDisabled,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_credential", phase="error", span={"end_byte":10340,"end_column":1,"end_line":469,"start_byte":10006,"start_column":1,"start_line":461}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_credential", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolution = _cott_match_value.value
            return ((((resolution).password != "") or ((resolution).source == PasswordSource_None())))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_credential", clause="ensures:0", phase="ensures", span={"end_byte":10214,"end_column":109,"end_line":462,"start_byte":10110,"start_column":5,"start_line":462}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CredentialResolution, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def connect(plan: ConnectionPlan) -> Result[Unit, ConnectionError]:
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connect.py", "4eca1cd1a33fdbcb87969eb2fbf9addb07f1f7c64b0229a903c4093ce8edcb28", "connect", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connect")
        _result = _implementation(plan)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connect"
        if _error.span is None:
            _error.span = {"end_byte":10558,"end_column":1,"end_line":476,"start_byte":10340,"start_column":1,"start_line":469}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connect", phase="implementation-call", span={"end_byte":10558,"end_column":1,"end_line":476,"start_byte":10340,"start_column":1,"start_line":469}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connect", phase="implementation-call", span={"end_byte":10558,"end_column":1,"end_line":476,"start_byte":10340,"start_column":1,"start_line":469}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_ConnectionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connect", phase="error", span={"end_byte":10558,"end_column":1,"end_line":476,"start_byte":10340,"start_column":1,"start_line":469}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connected = _cott_match_value.value
            return ((connected == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connect", clause="ensures:0", phase="ensures", span={"end_byte":10458,"end_column":52,"end_line":470,"start_byte":10411,"start_column":5,"start_line":470}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]:
    request = _cott_validate_abi(request, CatalogRefreshRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/refresh_catalog.py", "71640e8e80d2623892023dc6a8fc5cfb7967122479a554b825c1406b2dbbe3a0", "refresh_catalog", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.refresh_catalog")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.refresh_catalog"
        if _error.span is None:
            _error.span = {"end_byte":10854,"end_column":1,"end_line":484,"start_byte":10558,"start_column":1,"start_line":476}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.refresh_catalog", phase="implementation-call", span={"end_byte":10854,"end_column":1,"end_line":484,"start_byte":10558,"start_column":1,"start_line":476}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.refresh_catalog", phase="implementation-call", span={"end_byte":10854,"end_column":1,"end_line":484,"start_byte":10558,"start_column":1,"start_line":476}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Catalog, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_CatalogFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.refresh_catalog", phase="error", span={"end_byte":10854,"end_column":1,"end_line":484,"start_byte":10558,"start_column":1,"start_line":476}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (((catalog).limit == (request).limit))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:0", phase="ensures", span={"end_byte":10706,"end_column":65,"end_line":477,"start_byte":10646,"start_column":5,"start_line":477}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return ((len((catalog).relations) <= (request).limit))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:1", phase="ensures", span={"end_byte":10779,"end_column":73,"end_line":478,"start_byte":10711,"start_column":5,"start_line":478}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Catalog, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_sql.py", "13776ef61f3e995558e4c1d6646b0e3695662f01ef860da78757597dbce5f89c", "complete_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":10935,"end_column":1,"end_line":487,"start_byte":10854,"start_column":1,"start_line":484}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":10935,"end_column":1,"end_line":487,"start_byte":10854,"start_column":1,"start_line":484}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":10935,"end_column":1,"end_line":487,"start_byte":10854,"start_column":1,"start_line":484}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    policy = _cott_validate_abi(policy, CompletionPolicy, path="$.policy")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_catalog_sql.py", "6cef98e24e573daff1ed58dc6c710bf105c543fba46d70ef1bd3e03ffd53dbb3", "complete_catalog_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_catalog_sql")
        _result = _implementation(request, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_catalog_sql"
        if _error.span is None:
            _error.span = {"end_byte":11110,"end_column":1,"end_line":492,"start_byte":10935,"start_column":1,"start_line":487}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_catalog_sql", phase="implementation-call", span={"end_byte":11110,"end_column":1,"end_line":492,"start_byte":10935,"start_column":1,"start_line":487}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_catalog_sql", phase="implementation-call", span={"end_byte":11110,"end_column":1,"end_line":492,"start_byte":10935,"start_column":1,"start_line":487}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not ((len((_result).candidates) <= (policy).max_candidates)):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.complete_catalog_sql", clause="ensures:0", phase="ensures", span={"end_byte":11092,"end_column":59,"end_line":488,"start_byte":11038,"start_column":5,"start_line":488}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def highlight_sql(request: HighlightRequest) -> HighlightedSql:
    request = _cott_validate_abi(request, HighlightRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/highlight_sql.py", "207e31c823175ed39a0aa2603b8984b87529c99cab5dedccd5e88ef3b4d21e39", "highlight_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.highlight_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.highlight_sql"
        if _error.span is None:
            _error.span = {"end_byte":11189,"end_column":1,"end_line":495,"start_byte":11110,"start_column":1,"start_line":492}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.highlight_sql", phase="implementation-call", span={"end_byte":11189,"end_column":1,"end_line":495,"start_byte":11110,"start_column":1,"start_line":492}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.highlight_sql", phase="implementation-call", span={"end_byte":11189,"end_column":1,"end_line":495,"start_byte":11110,"start_column":1,"start_line":492}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HighlightedSql, path="$.return")
    _result = _cott_wrap_async_protocol(_result, HighlightedSql, path="$.return", validator=_cott_validate_abi)
    return _result

def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]:
    buffer = _cott_validate_abi(buffer, InputBuffer, path="$.buffer")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/plan_query.py", "ec05dc54bb06e5d3f57b91ce66f808764ec8c8890f2841ba1ad42f078b62985b", "plan_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.plan_query")
        _result = _implementation(buffer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.plan_query"
        if _error.span is None:
            _error.span = {"end_byte":11365,"end_column":1,"end_line":502,"start_byte":11189,"start_column":1,"start_line":495}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.plan_query", phase="implementation-call", span={"end_byte":11365,"end_column":1,"end_line":502,"start_byte":11189,"start_column":1,"start_line":495}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.plan_query", phase="implementation-call", span={"end_byte":11365,"end_column":1,"end_line":502,"start_byte":11189,"start_column":1,"start_line":495}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryPlan, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.plan_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.plan_query", phase="error", span={"end_byte":11365,"end_column":1,"end_line":502,"start_byte":11189,"start_column":1,"start_line":495}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.plan_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (((plan).sql == (buffer).text))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.plan_query", clause="ensures:0", phase="ensures", span={"end_byte":11313,"end_column":55,"end_line":496,"start_byte":11263,"start_column":5,"start_line":496}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryPlan, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer:
    buffer = _cott_validate_abi(buffer, InputBuffer, path="$.buffer")
    input = _cott_validate_abi(input, str, path="$.input")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/edit_multiline.py", "15f48fa77eda747ede00e9580ad1843143ad5c4e1e6ca2a086a071343b13dd48", "edit_multiline", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.edit_multiline")
        _result = _implementation(buffer, input)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.edit_multiline"
        if _error.span is None:
            _error.span = {"end_byte":11494,"end_column":1,"end_line":507,"start_byte":11365,"start_column":1,"start_line":502}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.edit_multiline", phase="implementation-call", span={"end_byte":11494,"end_column":1,"end_line":507,"start_byte":11365,"start_column":1,"start_line":502}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.edit_multiline", phase="implementation-call", span={"end_byte":11494,"end_column":1,"end_line":507,"start_byte":11365,"start_column":1,"start_line":502}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, InputBuffer, path="$.return")
    if not (((_result).cursor <= len((_result).text))):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_multiline", clause="ensures:0", phase="ensures", span={"end_byte":11476,"end_column":45,"end_line":503,"start_byte":11436,"start_column":5,"start_line":503}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, InputBuffer, path="$.return", validator=_cott_validate_abi)
    return _result

def recognize_backslash(source: str) -> BackslashCommand:
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/recognize_backslash.py", "dc7e103eb8a4c3ccc8c3100ec9ca957a84496f34a613b3cfb9901be0a3de7061", "recognize_backslash", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.recognize_backslash")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.recognize_backslash"
        if _error.span is None:
            _error.span = {"end_byte":11567,"end_column":1,"end_line":510,"start_byte":11494,"start_column":1,"start_line":507}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":11567,"end_column":1,"end_line":510,"start_byte":11494,"start_column":1,"start_line":507}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":11567,"end_column":1,"end_line":510,"start_byte":11494,"start_column":1,"start_line":507}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, BackslashCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, BackslashCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def parse_meta_command(source: str) -> MetaCommand:
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_meta_command.py", "a5e949ec4bb1fde49a42257344f88a293c284f0ca04145aa225e1c54a8dba947", "parse_meta_command", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_meta_command")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_meta_command"
        if _error.span is None:
            _error.span = {"end_byte":11634,"end_column":1,"end_line":513,"start_byte":11567,"start_column":1,"start_line":510}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_meta_command", phase="implementation-call", span={"end_byte":11634,"end_column":1,"end_line":513,"start_byte":11567,"start_column":1,"start_line":510}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_meta_command", phase="implementation-call", span={"end_byte":11634,"end_column":1,"end_line":513,"start_byte":11567,"start_column":1,"start_line":510}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, MetaCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, MetaCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def render_query(request: RenderRequest) -> RenderedQuery:
    request = _cott_validate_abi(request, RenderRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/render_query.py", "251b9136ee193527869dae5dbbd2e8fc1fa6f8fd521c0737346d42aa817e4c4b", "render_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.render_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.render_query"
        if _error.span is None:
            _error.span = {"end_byte":11708,"end_column":1,"end_line":516,"start_byte":11634,"start_column":1,"start_line":513}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":11708,"end_column":1,"end_line":516,"start_byte":11634,"start_column":1,"start_line":513}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":11708,"end_column":1,"end_line":516,"start_byte":11634,"start_column":1,"start_line":513}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, RenderedQuery, path="$.return")
    _result = _cott_wrap_async_protocol(_result, RenderedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def format_query(request: FormatRequest) -> FormattedQuery:
    request = _cott_validate_abi(request, FormatRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/format_query.py", "37ad61b92be97588a156f4dc527a7ab928e3c7a68b23645e0376f0737bbfd12d", "format_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.format_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.format_query"
        if _error.span is None:
            _error.span = {"end_byte":11838,"end_column":1,"end_line":521,"start_byte":11708,"start_column":1,"start_line":516}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.format_query", phase="implementation-call", span={"end_byte":11838,"end_column":1,"end_line":521,"start_byte":11708,"start_column":1,"start_line":516}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.format_query", phase="implementation-call", span={"end_byte":11838,"end_column":1,"end_line":521,"start_byte":11708,"start_column":1,"start_line":516}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, FormattedQuery, path="$.return")
    if not (((_result).truncated_rows <= (request).max_rows)):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.format_query", clause="ensures:0", phase="ensures", span={"end_byte":11820,"end_column":54,"end_line":517,"start_byte":11771,"start_column":5,"start_line":517}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FormattedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    connection = _cott_validate_abi(connection, ConnectionSettings, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_query.py", "815d1193dd48e4c722a25903b8aa1d9a44efaacfea7fe5f12a9a50da12093645", "execute_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_query")
        _result = _implementation(connection, sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_query"
        if _error.span is None:
            _error.span = {"end_byte":12158,"end_column":1,"end_line":529,"start_byte":11838,"start_column":1,"start_line":521}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":12158,"end_column":1,"end_line":529,"start_byte":11838,"start_column":1,"start_line":521}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":12158,"end_column":1,"end_line":529,"start_byte":11838,"start_column":1,"start_line":521}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryResult, DatabaseError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (DatabaseError_ConnectionFailed, DatabaseError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_query", phase="error", span={"end_byte":12158,"end_column":1,"end_line":529,"start_byte":11838,"start_column":1,"start_line":521}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            query_result = _cott_match_value.value
            return (((len((query_result).rows) == 0) or (len((query_result).columns) > 0)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_query", clause="ensures:0", phase="ensures", span={"end_byte":12033,"end_column":98,"end_line":522,"start_byte":11940,"start_column":5,"start_line":522}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryResult, DatabaseError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]:
    request = _cott_validate_abi(request, QueryRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_planned_query.py", "9bce2e403d00027c49f1e922855bc511ab52e542f20f7244e68edc1b3fa1657b", "execute_planned_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_planned_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_planned_query"
        if _error.span is None:
            _error.span = {"end_byte":12453,"end_column":1,"end_line":537,"start_byte":12158,"start_column":1,"start_line":529}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_planned_query", phase="implementation-call", span={"end_byte":12453,"end_column":1,"end_line":537,"start_byte":12158,"start_column":1,"start_line":529}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_planned_query", phase="implementation-call", span={"end_byte":12453,"end_column":1,"end_line":537,"start_byte":12158,"start_column":1,"start_line":529}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExecutedQuery, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_planned_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_QueryFailed, ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_planned_query", phase="error", span={"end_byte":12453,"end_column":1,"end_line":537,"start_byte":12158,"start_column":1,"start_line":529}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_planned_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            executed = _cott_match_value.value
            return ((len(((executed).result).rows) <= (request).max_rows))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_planned_query", clause="ensures:0", phase="ensures", span={"end_byte":12324,"end_column":80,"end_line":530,"start_byte":12249,"start_column":5,"start_line":530}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExecutedQuery, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def begin_transaction(mode: TransactionMode) -> TransactionState:
    mode = _cott_validate_abi(mode, TransactionMode, path="$.mode")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/begin_transaction.py", "5b9532c618911f88444acbe09e0066cb3cd58f8f2b345a3faa9237a4c2749631", "begin_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.begin_transaction")
        _result = _implementation(mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.begin_transaction"
        if _error.span is None:
            _error.span = {"end_byte":12581,"end_column":1,"end_line":542,"start_byte":12453,"start_column":1,"start_line":537}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.begin_transaction", phase="implementation-call", span={"end_byte":12581,"end_column":1,"end_line":542,"start_byte":12453,"start_column":1,"start_line":537}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.begin_transaction", phase="implementation-call", span={"end_byte":12581,"end_column":1,"end_line":542,"start_byte":12453,"start_column":1,"start_line":537}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TransactionState, path="$.return")
    if not (((_result).mode == mode)):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.begin_transaction", clause="ensures:0", phase="ensures", span={"end_byte":12549,"end_column":32,"end_line":538,"start_byte":12522,"start_column":5,"start_line":538}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TransactionState, path="$.return", validator=_cott_validate_abi)
    return _result

def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    transaction = _cott_validate_abi(transaction, TransactionState, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/commit_transaction.py", "6b4e27b16f85ed1c1d68dd55bab11570d1a357f418bacef2124329726b54c181", "commit_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.commit_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":12805,"end_column":1,"end_line":549,"start_byte":12581,"start_column":1,"start_line":542}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.commit_transaction", phase="implementation-call", span={"end_byte":12805,"end_column":1,"end_line":549,"start_byte":12581,"start_column":1,"start_line":542}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.commit_transaction", phase="implementation-call", span={"end_byte":12805,"end_column":1,"end_line":549,"start_byte":12581,"start_column":1,"start_line":542}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransactionState, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.commit_transaction", phase="error", span={"end_byte":12805,"end_column":1,"end_line":549,"start_byte":12581,"start_column":1,"start_line":542}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            committed = _cott_match_value.value
            return ((not (committed).active))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.commit_transaction", clause="ensures:0", phase="ensures", span={"end_byte":12732,"end_column":57,"end_line":543,"start_byte":12680,"start_column":5,"start_line":543}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransactionState, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    transaction = _cott_validate_abi(transaction, TransactionState, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/rollback_transaction.py", "aac8b61f4ec16b33124aa4f137a96fda12d0c516243b938a18534e01c3ec33d6", "rollback_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.rollback_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":13035,"end_column":1,"end_line":556,"start_byte":12805,"start_column":1,"start_line":549}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.rollback_transaction", phase="implementation-call", span={"end_byte":13035,"end_column":1,"end_line":556,"start_byte":12805,"start_column":1,"start_line":549}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.rollback_transaction", phase="implementation-call", span={"end_byte":13035,"end_column":1,"end_line":556,"start_byte":12805,"start_column":1,"start_line":549}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransactionState, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.rollback_transaction", phase="error", span={"end_byte":13035,"end_column":1,"end_line":556,"start_byte":12805,"start_column":1,"start_line":549}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rolled_back = _cott_match_value.value
            return ((not (rolled_back).active))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.rollback_transaction", clause="ensures:0", phase="ensures", span={"end_byte":12962,"end_column":61,"end_line":550,"start_byte":12906,"start_column":5,"start_line":550}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransactionState, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]:
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/load_history.py", "132eb9bfc469150bc6e5b2bbf04f01d1939cff71648186a033b3d4791a7c5a00", "load_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.load_history")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.load_history"
        if _error.span is None:
            _error.span = {"end_byte":13249,"end_column":1,"end_line":563,"start_byte":13035,"start_column":1,"start_line":556}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.load_history", phase="implementation-call", span={"end_byte":13249,"end_column":1,"end_line":563,"start_byte":13035,"start_column":1,"start_line":556}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.load_history", phase="implementation-call", span={"end_byte":13249,"end_column":1,"end_line":563,"start_byte":13035,"start_column":1,"start_line":556}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[HistoryEntry], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_HistoryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.load_history", phase="error", span={"end_byte":13249,"end_column":1,"end_line":563,"start_byte":13035,"start_column":1,"start_line":556}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return ((len(entries) <= (policy).max_entries))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_history", clause="ensures:0", phase="ensures", span={"end_byte":13185,"end_column":68,"end_line":557,"start_byte":13122,"start_column":5,"start_line":557}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[HistoryEntry], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]:
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    entries = _cott_validate_abi(entries, CottList[HistoryEntry], path="$.entries")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/save_history.py", "e3fff95d72de9f1787460569cfa4c63b978a960bcb9140c08aeaa531a93a4ed6", "save_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.save_history")
        _result = _implementation(policy, entries)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.save_history"
        if _error.span is None:
            _error.span = {"end_byte":13455,"end_column":1,"end_line":570,"start_byte":13249,"start_column":1,"start_line":563}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.save_history", phase="implementation-call", span={"end_byte":13455,"end_column":1,"end_line":570,"start_byte":13249,"start_column":1,"start_line":563}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.save_history", phase="implementation-call", span={"end_byte":13455,"end_column":1,"end_line":570,"start_byte":13249,"start_column":1,"start_line":563}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_HistoryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.save_history", phase="error", span={"end_byte":13455,"end_column":1,"end_line":570,"start_byte":13249,"start_column":1,"start_line":563}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return ((saved == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.save_history", clause="ensures:0", phase="ensures", span={"end_byte":13390,"end_column":44,"end_line":564,"start_byte":13351,"start_column":5,"start_line":564}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]:
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    entries = _cott_validate_abi(entries, CottList[HistoryEntry], path="$.entries")
    entry = _cott_validate_abi(entry, HistoryEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/remember_history.py", "ddc5f1110457a4261b3cf82f23cc272e49fcf71c1a68990bd84eeec7339ea8d2", "remember_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.remember_history")
        _result = _implementation(policy, entries, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.remember_history"
        if _error.span is None:
            _error.span = {"end_byte":13648,"end_column":1,"end_line":579,"start_byte":13455,"start_column":1,"start_line":570}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.remember_history", phase="implementation-call", span={"end_byte":13648,"end_column":1,"end_line":579,"start_byte":13455,"start_column":1,"start_line":570}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.remember_history", phase="implementation-call", span={"end_byte":13648,"end_column":1,"end_line":579,"start_byte":13455,"start_column":1,"start_line":570}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[HistoryEntry], path="$.return")
    if not ((len(_result) <= (policy).max_entries)):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.remember_history", clause="ensures:0", phase="ensures", span={"end_byte":13630,"end_column":45,"end_line":575,"start_byte":13590,"start_column":5,"start_line":575}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[HistoryEntry], path="$.return", validator=_cott_validate_abi)
    return _result

def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]:
    store = _cott_validate_abi(store, FavoriteStore, path="$.store")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/load_favorites.py", "8880789cc6521789c6caa78ccb393ec8d00ecf325d6bd944410fde345e53080a", "load_favorites", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.load_favorites")
        _result = _implementation(store)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.load_favorites"
        if _error.span is None:
            _error.span = {"end_byte":13863,"end_column":1,"end_line":586,"start_byte":13648,"start_column":1,"start_line":579}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.load_favorites", phase="implementation-call", span={"end_byte":13863,"end_column":1,"end_line":586,"start_byte":13648,"start_column":1,"start_line":579}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.load_favorites", phase="implementation-call", span={"end_byte":13863,"end_column":1,"end_line":586,"start_byte":13648,"start_column":1,"start_line":579}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[Favorite], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.load_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_FavoriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.load_favorites", phase="error", span={"end_byte":13863,"end_column":1,"end_line":586,"start_byte":13648,"start_column":1,"start_line":579}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.load_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            favorites = _cott_match_value.value
            return ((len(favorites) <= (store).max_entries))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_favorites", clause="ensures:0", phase="ensures", span={"end_byte":13798,"end_column":71,"end_line":580,"start_byte":13732,"start_column":5,"start_line":580}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[Favorite], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]:
    store = _cott_validate_abi(store, FavoriteStore, path="$.store")
    favorites = _cott_validate_abi(favorites, CottList[Favorite], path="$.favorites")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/save_favorites.py", "ce244738a6607cb1df00147b98702dc20b8174dac8f883dff7fc47a572c89b49", "save_favorites", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.save_favorites")
        _result = _implementation(store, favorites)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.save_favorites"
        if _error.span is None:
            _error.span = {"end_byte":14069,"end_column":1,"end_line":593,"start_byte":13863,"start_column":1,"start_line":586}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.save_favorites", phase="implementation-call", span={"end_byte":14069,"end_column":1,"end_line":593,"start_byte":13863,"start_column":1,"start_line":586}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.save_favorites", phase="implementation-call", span={"end_byte":14069,"end_column":1,"end_line":593,"start_byte":13863,"start_column":1,"start_line":586}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.save_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_FavoriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.save_favorites", phase="error", span={"end_byte":14069,"end_column":1,"end_line":593,"start_byte":13863,"start_column":1,"start_line":586}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.save_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return ((saved == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.save_favorites", clause="ensures:0", phase="ensures", span={"end_byte":14003,"end_column":44,"end_line":587,"start_byte":13964,"start_column":5,"start_line":587}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]:
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    request = _cott_validate_abi(request, ImportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/import_delimited.py", "c1abae9a85d68630a70726b5ec48f49911c49438b2c2dc556243f7af4b7bb182", "import_delimited", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.import_delimited")
        _result = _implementation(plan, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.import_delimited"
        if _error.span is None:
            _error.span = {"end_byte":14367,"end_column":1,"end_line":604,"start_byte":14069,"start_column":1,"start_line":593}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.import_delimited", phase="implementation-call", span={"end_byte":14367,"end_column":1,"end_line":604,"start_byte":14069,"start_column":1,"start_line":593}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.import_delimited", phase="implementation-call", span={"end_byte":14367,"end_column":1,"end_line":604,"start_byte":14069,"start_column":1,"start_line":593}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.import_delimited", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ImportFailed, ClientError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.import_delimited", phase="error", span={"end_byte":14367,"end_column":1,"end_line":604,"start_byte":14069,"start_column":1,"start_line":593}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.import_delimited", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            imported = _cott_match_value.value
            return (((imported).rows <= (request).max_rows))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.import_delimited", clause="ensures:0", phase="ensures", span={"end_byte":14254,"end_column":69,"end_line":597,"start_byte":14190,"start_column":5,"start_line":597}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]:
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    request = _cott_validate_abi(request, ExportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/export_query.py", "96a6509108fc7f85bede59d59c0df95ab5ae643c65047658eb88402615dafe89", "export_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.export_query")
        _result = _implementation(plan, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.export_query"
        if _error.span is None:
            _error.span = {"end_byte":14661,"end_column":1,"end_line":615,"start_byte":14367,"start_column":1,"start_line":604}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.export_query", phase="implementation-call", span={"end_byte":14661,"end_column":1,"end_line":615,"start_byte":14367,"start_column":1,"start_line":604}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.export_query", phase="implementation-call", span={"end_byte":14661,"end_column":1,"end_line":615,"start_byte":14367,"start_column":1,"start_line":604}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.export_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ExportFailed, ClientError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.export_query", phase="error", span={"end_byte":14661,"end_column":1,"end_line":615,"start_byte":14367,"start_column":1,"start_line":604}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.export_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            exported = _cott_match_value.value
            return (((exported).rows <= (request).max_rows))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.export_query", clause="ensures:0", phase="ensures", span={"end_byte":14548,"end_column":69,"end_line":608,"start_byte":14484,"start_column":5,"start_line":608}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    request = _cott_validate_abi(request, EditorRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/edit_in_editor.py", "836e82ec3dd976face336e480dc04bf1dfe0cd4e88cd043240cedf94a55df417", "edit_in_editor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.edit_in_editor")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.edit_in_editor"
        if _error.span is None:
            _error.span = {"end_byte":14880,"end_column":1,"end_line":622,"start_byte":14661,"start_column":1,"start_line":615}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.edit_in_editor", phase="implementation-call", span={"end_byte":14880,"end_column":1,"end_line":622,"start_byte":14661,"start_column":1,"start_line":615}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.edit_in_editor", phase="implementation-call", span={"end_byte":14880,"end_column":1,"end_line":622,"start_byte":14661,"start_column":1,"start_line":615}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[InputBuffer, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.edit_in_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_EditorFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.edit_in_editor", phase="error", span={"end_byte":14880,"end_column":1,"end_line":622,"start_byte":14661,"start_column":1,"start_line":615}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.edit_in_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            buffer = _cott_match_value.value
            return (((buffer).cursor <= len((buffer).text)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_in_editor", clause="ensures:0", phase="ensures", span={"end_byte":14805,"end_column":66,"end_line":616,"start_byte":14744,"start_column":5,"start_line":616}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[InputBuffer, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def page_output(request: PagerRequest) -> Result[Unit, ClientError]:
    request = _cott_validate_abi(request, PagerRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/page_output.py", "3fb6d48cafff66efee0c744a8fed2dbdeae59f83b7341e49de9952abebb14b24", "page_output", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.page_output")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.page_output"
        if _error.span is None:
            _error.span = {"end_byte":15065,"end_column":1,"end_line":629,"start_byte":14880,"start_column":1,"start_line":622}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.page_output", phase="implementation-call", span={"end_byte":15065,"end_column":1,"end_line":629,"start_byte":14880,"start_column":1,"start_line":622}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.page_output", phase="implementation-call", span={"end_byte":15065,"end_column":1,"end_line":629,"start_byte":14880,"start_column":1,"start_line":622}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.page_output", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_PagerFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.page_output", phase="error", span={"end_byte":15065,"end_column":1,"end_line":629,"start_byte":14880,"start_column":1,"start_line":622}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.page_output", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            paged = _cott_match_value.value
            return ((paged == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.page_output", clause="ensures:0", phase="ensures", span={"end_byte":14991,"end_column":44,"end_line":623,"start_byte":14952,"start_column":5,"start_line":623}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]:
    request = _cott_validate_abi(request, NotificationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/receive_notifications.py", "0d2297327075297b9021e8e339c2d48686143ee2b15b9d8037f33e587e58ddae", "receive_notifications", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.receive_notifications")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.receive_notifications"
        if _error.span is None:
            _error.span = {"end_byte":15330,"end_column":1,"end_line":636,"start_byte":15065,"start_column":1,"start_line":629}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.receive_notifications", phase="implementation-call", span={"end_byte":15330,"end_column":1,"end_line":636,"start_byte":15065,"start_column":1,"start_line":629}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.receive_notifications", phase="implementation-call", span={"end_byte":15330,"end_column":1,"end_line":636,"start_byte":15065,"start_column":1,"start_line":629}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[Notification], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.receive_notifications", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_NotificationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.receive_notifications", phase="error", span={"end_byte":15330,"end_column":1,"end_line":636,"start_byte":15065,"start_column":1,"start_line":629}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.receive_notifications", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            notifications = _cott_match_value.value
            return ((len(notifications) <= (request).max_notifications))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.receive_notifications", clause="ensures:0", phase="ensures", span={"end_byte":15250,"end_column":87,"end_line":630,"start_byte":15168,"start_column":5,"start_line":630}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[Notification], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]:
    request = _cott_validate_abi(request, WatchRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/watch_query.py", "90b03b31027223db721e6fb4c41513b1a3e97698ba1151943bd98fdd1df74ca9", "watch_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.watch_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.watch_query"
        if _error.span is None:
            _error.span = {"end_byte":15612,"end_column":1,"end_line":644,"start_byte":15330,"start_column":1,"start_line":636}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.watch_query", phase="implementation-call", span={"end_byte":15612,"end_column":1,"end_line":644,"start_byte":15330,"start_column":1,"start_line":636}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.watch_query", phase="implementation-call", span={"end_byte":15612,"end_column":1,"end_line":644,"start_byte":15330,"start_column":1,"start_line":636}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WatchResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.watch_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_QueryFailed, ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.watch_query", phase="error", span={"end_byte":15612,"end_column":1,"end_line":644,"start_byte":15330,"start_column":1,"start_line":636}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.watch_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            watched = _cott_match_value.value
            return (((watched).executions <= (request).max_iterations))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.watch_query", clause="ensures:0", phase="ensures", span={"end_byte":15483,"end_column":79,"end_line":637,"start_byte":15409,"start_column":5,"start_line":637}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/pgcli/run_meta_command.py", "d66651615814b149c574fc21fb2405d057db32a396986535a2deba4b875c4d8a", "run_meta_command", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run_meta_command")
        _result = _implementation(invocation, options, catalog)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run_meta_command"
        if _error.span is None:
            _error.span = {"end_byte":16324,"end_column":1,"end_line":665,"start_byte":15612,"start_column":1,"start_line":644}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.run_meta_command", phase="implementation-call", span={"end_byte":16324,"end_column":1,"end_line":665,"start_byte":15612,"start_column":1,"start_line":644}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run_meta_command", phase="implementation-call", span={"end_byte":16324,"end_column":1,"end_line":665,"start_byte":15612,"start_column":1,"start_line":644}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CommandResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.run_meta_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidCommand, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_ImportFailed, ClientError_ExportFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_NotificationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.run_meta_command", phase="error", span={"end_byte":16324,"end_column":1,"end_line":665,"start_byte":15612,"start_column":1,"start_line":644}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.run_meta_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            step = _cott_match_value.value
            return (((step).quit or (((step).buffer).cursor <= len(((step).buffer).text))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_meta_command", clause="ensures:0", phase="ensures", span={"end_byte":15846,"end_column":87,"end_line":649,"start_byte":15764,"start_column":5,"start_line":649}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CommandResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_interactive(request: InteractiveRequest) -> Result[Unit, ClientError]:
    request = _cott_validate_abi(request, InteractiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run_interactive.py", "79cbc261d2096221bf78000412c5654bea099c72817193dc036b317851885950", "run_interactive", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run_interactive")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run_interactive"
        if _error.span is None:
            _error.span = {"end_byte":16938,"end_column":1,"end_line":682,"start_byte":16324,"start_column":1,"start_line":665}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.run_interactive", phase="implementation-call", span={"end_byte":16938,"end_column":1,"end_line":682,"start_byte":16324,"start_column":1,"start_line":665}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run_interactive", phase="implementation-call", span={"end_byte":16938,"end_column":1,"end_line":682,"start_byte":16324,"start_column":1,"start_line":665}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.run_interactive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_NotificationFailed, ClientError_TerminalFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.run_interactive", phase="error", span={"end_byte":16938,"end_column":1,"end_line":682,"start_byte":16324,"start_column":1,"start_line":665}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.run_interactive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            finished = _cott_match_value.value
            return ((finished == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_interactive", clause="ensures:0", phase="ensures", span={"end_byte":16451,"end_column":50,"end_line":666,"start_byte":16406,"start_column":5,"start_line":666}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """Run an interactive PostgreSQL session and print client errors before exiting."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run.py", "4651de83b8b2a53ef785b4daef371e75746dbb6fd9dbc2399f074dd2c83b596f", "run", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run"
        if _error.span is None:
            _error.span = {"end_byte":17256,"end_column":1,"end_line":697,"start_byte":16938,"start_column":1,"start_line":682}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run", phase="implementation-call", span={"end_byte":17256,"end_column":1,"end_line":697,"start_byte":16938,"start_column":1,"start_line":682}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.pgcli.run", phase="return", span={"end_byte":17256,"end_column":1,"end_line":697,"start_byte":16938,"start_column":1,"start_line":682}, expected="Never", actual=repr(_result))

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "ClientError", "ClientError_CatalogFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionError_TlsInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_ClearOutput", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListNotifications", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_Password", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetLogFile", "MetaCommand_SetOptions", "MetaCommand_SetOutput", "MetaCommand_SetPager", "MetaCommand_Shell", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_VerboseErrors", "MetaCommand_Watch", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SessionOptions", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransferResult", "WatchRequest", "WatchResult", "begin_transaction", "commit_transaction", "complete_catalog_sql", "complete_sql", "connect", "edit_in_editor", "edit_multiline", "execute_planned_query", "execute_query", "export_query", "format_query", "highlight_sql", "import_delimited", "load_favorites", "load_history", "page_output", "parse_dsn", "parse_meta_command", "plan_query", "prompt_policy", "receive_notifications", "recognize_backslash", "refresh_catalog", "remember_history", "render_query", "resolve_connection", "resolve_connection_plan", "resolve_credential", "resolve_profile", "rollback_transaction", "run", "run_interactive", "run_meta_command", "save_favorites", "save_history", "watch_query"]
