from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_any_blank_by, _cott_starts_with, _cott_unique_by

from real.pgcli_types import BackslashCommand, BackslashCommand_Describe, BackslashCommand_Help, BackslashCommand_Quit, BackslashCommand_Tables, BackslashCommand_Unknown, Catalog, CatalogRefreshRequest, CliCommand, CliCommand_Help, CliCommand_Session, ClientCertificate, ClientError, ClientError_CatalogFailed, ClientError_ConnectionFailed, ClientError_EditorFailed, ClientError_ExportFailed, ClientError_FavoriteFailed, ClientError_HistoryFailed, ClientError_ImportFailed, ClientError_InvalidArguments, ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_NotificationFailed, ClientError_PagerFailed, ClientError_QueryFailed, ClientError_TerminalFailed, ClientError_TransactionFailed, ClientError_TunnelUnsupported, ClientError_UnsupportedFormat, ColumnCatalog, CommandInvocation, CommandResult, CompletionPolicy, CompletionRequest, CompletionResult, ConnectionError, ConnectionError_ConnectionFailed, ConnectionError_CredentialUnavailable, ConnectionError_InvalidDsn, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionError_ProfileMissing, ConnectionError_PromptDisabled, ConnectionError_SshInvalid, ConnectionInputs, ConnectionPlan, ConnectionProfile, ConnectionReceipt, ConnectionRequest, ConnectionSettings, CredentialRequest, CredentialResolution, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, EditorRequest, EnvironmentInputs, ExecutedQuery, ExportRequest, Favorite, FavoriteStore, FormatRequest, FormattedQuery, HighlightRequest, HighlightedSql, HistoryEntry, HistoryPolicy, ImportRequest, InputBuffer, InteractiveRequest, MetaCommand, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery, MetaCommand_Describe, MetaCommand_Echo, MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_Expanded, MetaCommand_Favorite, MetaCommand_Help, MetaCommand_History, MetaCommand_ListDataTypes, MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains, MetaCommand_ListExtensions, MetaCommand_ListFavorites, MetaCommand_ListForeignTables, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListPrivileges, MetaCommand_ListRoles, MetaCommand_ListSchemas, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews, MetaCommand_NamedQuery, MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho, MetaCommand_Quit, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery, MetaCommand_SetFormat, MetaCommand_SetPager, MetaCommand_ShowFunction, MetaCommand_SqlHelp, MetaCommand_Timing, MetaCommand_Unknown, MetaCommand_WriteBuffer, Notification, NotificationRequest, PagerRequest, PasswordSource, PasswordSource_Environment, PasswordSource_Keyring, PasswordSource_None, PasswordSource_Prompt, PasswordSource_Supplied, PromptAction, PromptAction_PromptPassword, PromptAction_UsePassword, QueryPlan, QueryRequest, QueryResult, RelationCatalog, RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery, RoutineCatalog, SQL_KEYWORDS, SessionMode, SessionMode_ExecuteOnce, SessionMode_Interactive, SessionOptions, SessionReport, SshSettings, TableCatalog, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical, TlsMode, TlsMode_Allow, TlsMode_Default, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TlsMode_VerifyFull, TlsSettings, TransactionMode, TransactionMode_AutoCommit, TransactionMode_Manual, TransactionMode_ReadOnly, TransactionState, TransactionStatus, TransactionStatus_Active, TransactionStatus_Failed, TransactionStatus_Idle, TransferResult, WatchRequest, WatchResult

def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]:
    """Parse value as one libpq connection string: a postgresql:// or postgres://
URI (percent-decoded) or whitespace-separated key=value pairs. Return its
host, port, user, password and dbname parameters verbatim; an absent
parameter is "". A string libpq cannot parse, and one that names no
database, is InvalidDsn whose value is a fixed category message that never
contains any part of the input, which may include a password."""
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_dsn.py", "4f9d74466166d632b5d93130ea3c346ac3c34282e67fcaa48288b8ae7a05a86d", "parse_dsn", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_dsn")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_dsn"
        if _error.span is None:
            _error.span = {"end_byte":14549,"end_column":1,"end_line":579,"start_byte":13900,"start_column":1,"start_line":563}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_dsn", phase="implementation-call", span={"end_byte":14549,"end_column":1,"end_line":579,"start_byte":13900,"start_column":1,"start_line":563}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_dsn", phase="implementation-call", span={"end_byte":14549,"end_column":1,"end_line":579,"start_byte":13900,"start_column":1,"start_line":563}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionInputs, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.parse_dsn", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_InvalidDsn,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.parse_dsn", phase="error", span={"end_byte":14549,"end_column":1,"end_line":579,"start_byte":13900,"start_column":1,"start_line":563}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.parse_dsn", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.parse_dsn", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidDsn:
        _cott_contract_condition(True, "real.pgcli.parse_dsn", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (_cott_contract_condition((((inputs).database != "")), "real.pgcli.parse_dsn", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.parse_dsn", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.parse_dsn", clause="ensures:1", phase="ensures", span={"end_byte":14493,"end_column":55,"end_line":573,"start_byte":14443,"start_column":5,"start_line":573}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionInputs, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_profile(name: str, profiles: CottList[ConnectionProfile]) -> Result[ConnectionProfile, ConnectionError]:
    """Return the first profile in list order whose name equals name exactly
(case-sensitive, no trimming); when none does, return ProfileMissing(name: name)."""
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
            _error.span = {"end_byte":14967,"end_column":1,"end_line":594,"start_byte":14549,"start_column":1,"start_line":579}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_profile", phase="implementation-call", span={"end_byte":14967,"end_column":1,"end_line":594,"start_byte":14549,"start_column":1,"start_line":579}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_profile", phase="implementation-call", span={"end_byte":14967,"end_column":1,"end_line":594,"start_byte":14549,"start_column":1,"start_line":579}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionProfile, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_ProfileMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_profile", phase="error", span={"end_byte":14967,"end_column":1,"end_line":594,"start_byte":14549,"start_column":1,"start_line":579}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_profile", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_ProfileMissing:
        _cott_contract_condition(True, "real.pgcli.resolve_profile", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            profile = _cott_match_value.value
            return (_cott_contract_condition((((profile).name == name)), "real.pgcli.resolve_profile", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.resolve_profile", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_profile", clause="ensures:1", phase="ensures", span={"end_byte":14907,"end_column":55,"end_line":588,"start_byte":14857,"start_column":5,"start_line":588}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionProfile, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    """Merge explicit inputs over environment values field by field. The merged
database must be nonempty. A nonempty merged port must consist of ASCII
digits denoting 1..65535, otherwise return InvalidPort(value: the merged
port); an empty port stays empty and means libpq's default."""
    inputs = _cott_validate_abi(inputs, ConnectionInputs, path="$.inputs")
    environment = _cott_validate_abi(environment, EnvironmentInputs, path="$.environment")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((inputs).database == "") and ((environment).database == ""))), "real.pgcli.resolve_connection", "error:6:condition")):
        _expected_error = ConnectionError_MissingDatabase
        _expected_error_span = {"end_byte":16324,"end_column":100,"end_line":611,"start_byte":16229,"start_column":5,"start_line":611}
        _expected_error_clause = "error:6"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection.py", "9b2695d30b8c3eea9762d8e6fea061655285e7cb9a47bc434bfc0c87186922a6", "resolve_connection", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection")
        _result = _implementation(inputs, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection"
        if _error.span is None:
            _error.span = {"end_byte":16380,"end_column":1,"end_line":616,"start_byte":14967,"start_column":1,"start_line":594}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":16380,"end_column":1,"end_line":616,"start_byte":14967,"start_column":1,"start_line":594}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection", phase="implementation-call", span={"end_byte":16380,"end_column":1,"end_line":616,"start_byte":14967,"start_column":1,"start_line":594}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionSettings, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_InvalidPort,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection", phase="error", span={"end_byte":16380,"end_column":1,"end_line":616,"start_byte":14967,"start_column":1,"start_line":594}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_connection", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidPort:
        _cott_contract_condition(True, "real.pgcli.resolve_connection", "error:7")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).host != "") and ((settings).host == (inputs).host)) or (((inputs).host == "") and ((settings).host == (environment).host)))), "real.pgcli.resolve_connection", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:1", phase="ensures", span={"end_byte":15571,"end_column":151,"end_line":605,"start_byte":15425,"start_column":5,"start_line":605}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).port != "") and ((settings).port == (inputs).port)) or (((inputs).port == "") and ((settings).port == (environment).port)))), "real.pgcli.resolve_connection", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:2", phase="ensures", span={"end_byte":15722,"end_column":151,"end_line":606,"start_byte":15576,"start_column":5,"start_line":606}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).user != "") and ((settings).user == (inputs).user)) or (((inputs).user == "") and ((settings).user == (environment).user)))), "real.pgcli.resolve_connection", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:3", phase="ensures", span={"end_byte":15873,"end_column":151,"end_line":607,"start_byte":15727,"start_column":5,"start_line":607}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).password != "") and ((settings).password == (inputs).password)) or (((inputs).password == "") and ((settings).password == (environment).password)))), "real.pgcli.resolve_connection", "ensures:4"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:4", phase="ensures", span={"end_byte":16048,"end_column":175,"end_line":608,"start_byte":15878,"start_column":5,"start_line":608}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settings = _cott_match_value.value
            return (_cott_contract_condition((((((inputs).database != "") and ((settings).database == (inputs).database)) or (((inputs).database == "") and ((settings).database == (environment).database)))), "real.pgcli.resolve_connection", "ensures:5"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection", clause="ensures:5", phase="ensures", span={"end_byte":16223,"end_column":175,"end_line":609,"start_byte":16053,"start_column":5,"start_line":609}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionSettings, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]:
    """Build a session plan from four layers, highest first: request.inputs, the
effective connection string, the profile's inputs when profile is Some, then
request.environment. The effective connection string is request.dsn when
nonempty, otherwise the profile's dsn, otherwise ""; it contributes its host,
port, user, password and dbname parameters as parsed by libpq. For host,
port, user, password and database take the first nonempty layer value.
request.profile is the name the caller resolved with resolve_profile; only
the profile argument is used here.

plan.dsn is the effective connection string. plan.tls is request.tls when its
mode is not Default, otherwise the profile's tls when profile is Some,
otherwise request.tls. plan.ssh is request.ssh when Some, otherwise the
profile's ssh when profile is Some, otherwise Nothing.

Validate in this order: the selected SSH hop needs a nonempty host that does
not start with "-", a nonempty user and a nonzero port (SshInvalid); the
effective connection string must parse (InvalidDsn); the merged port follows
resolve_connection's port rule (InvalidPort); the merged database must be
nonempty (MissingDatabase)."""
    request = _cott_validate_abi(request, ConnectionRequest, path="$.request")
    profile = _cott_validate_abi(profile, Option[ConnectionProfile], path="$.profile")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_8() -> bool:
        _cott_match_value = (request).ssh
        if type(_cott_match_value) is Some and True:
            hop = _cott_match_value.value
            return (_cott_contract_condition(((((((hop).host == "") or _cott_starts_with((hop).host, "-")) or ((hop).user == "")) or ((hop).port == 0))), "real.pgcli.resolve_connection_plan", "error:8:condition"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "error:8:applicable")
        return False
    if _expected_error is None and (_cott_match_error_8()):
        _expected_error = ConnectionError_SshInvalid
        _expected_error_span = {"end_byte":18634,"end_column":166,"end_line":650,"start_byte":18473,"start_column":5,"start_line":650}
        _expected_error_clause = "error:8"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_connection_plan.py", "143bf556d34441d1e7c7d4ae9ced70893ae89b264600960cccd294e9667faed6", "resolve_connection_plan", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_connection_plan")
        _result = _implementation(request, profile)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_connection_plan"
        if _error.span is None:
            _error.span = {"end_byte":18806,"end_column":1,"end_line":658,"start_byte":16380,"start_column":1,"start_line":616}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_connection_plan", phase="implementation-call", span={"end_byte":18806,"end_column":1,"end_line":658,"start_byte":16380,"start_column":1,"start_line":616}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_connection_plan", phase="implementation-call", span={"end_byte":18806,"end_column":1,"end_line":658,"start_byte":16380,"start_column":1,"start_line":616}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionPlan, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_connection_plan", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_SshInvalid, ConnectionError_InvalidDsn, ConnectionError_InvalidPort, ConnectionError_MissingDatabase,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_connection_plan", phase="error", span={"end_byte":18806,"end_column":1,"end_line":658,"start_byte":16380,"start_column":1,"start_line":616}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_connection_plan", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_SshInvalid:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:9")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidDsn:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:10")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidPort:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:11")
    if type(_result) is Err and type(_result.error) is ConnectionError_MissingDatabase:
        _cott_contract_condition(True, "real.pgcli.resolve_connection_plan", "error:12")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition(((((plan).settings).database != "")), "real.pgcli.resolve_connection_plan", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:1", phase="ensures", span={"end_byte":17845,"end_column":60,"end_line":642,"start_byte":17790,"start_column":5,"start_line":642}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((((request).inputs).host == "") or (((plan).settings).host == ((request).inputs).host))), "real.pgcli.resolve_connection_plan", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:2", phase="ensures", span={"end_byte":17949,"end_column":104,"end_line":643,"start_byte":17850,"start_column":5,"start_line":643}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((((request).inputs).port == "") or (((plan).settings).port == ((request).inputs).port))), "real.pgcli.resolve_connection_plan", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:3", phase="ensures", span={"end_byte":18053,"end_column":104,"end_line":644,"start_byte":17954,"start_column":5,"start_line":644}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((((request).inputs).user == "") or (((plan).settings).user == ((request).inputs).user))), "real.pgcli.resolve_connection_plan", "ensures:4"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:4", phase="ensures", span={"end_byte":18157,"end_column":104,"end_line":645,"start_byte":18058,"start_column":5,"start_line":645}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((((request).inputs).password == "") or (((plan).settings).password == ((request).inputs).password))), "real.pgcli.resolve_connection_plan", "ensures:5"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:5", phase="ensures", span={"end_byte":18273,"end_column":116,"end_line":646,"start_byte":18162,"start_column":5,"start_line":646}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((((request).inputs).database == "") or (((plan).settings).database == ((request).inputs).database))), "real.pgcli.resolve_connection_plan", "ensures:6"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:6", phase="ensures", span={"end_byte":18389,"end_column":116,"end_line":647,"start_byte":18278,"start_column":5,"start_line":647}, expected="true", actual="false")
    def _cott_match_ensures_7() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition(((((request).dsn == "") or ((plan).dsn == (request).dsn))), "real.pgcli.resolve_connection_plan", "ensures:7"))
        _cott_contract_condition((False), "real.pgcli.resolve_connection_plan", "ensures:7:applicable")
        return True
    if not (_cott_match_ensures_7()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_connection_plan", clause="ensures:7", phase="ensures", span={"end_byte":18467,"end_column":78,"end_line":648,"start_byte":18394,"start_column":5,"start_line":648}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionPlan, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_arguments(arguments: CottList[str], environment: EnvironmentInputs) -> Result[CliCommand, ClientError]:
    """Parse the pgcli-cott command line; arguments excludes the program name.
--help anywhere selects Help. The options -h/--host, -p/--port,
-U/--username, -d/--dbname and -c/--command take the next argument as their
value, or use the --long=value form; a repeated option keeps its last value.
The first other argument that does not start with "-" is the positional
connection string. An option without a value, a second positional argument
and any other argument starting with "-" are InvalidArguments whose message
names the offending option or says that a positional argument is extra and
never contains an argument value.

Session carries ConnectionRequest(dsn: the positional value or "", profile: "",
inputs: host, port, user and database from the options ("" when absent) with
password "", environment: environment, tls: TlsSettings(Default, Nothing,
Nothing), ssh: Nothing). The CLI never accepts a password argument. -c selects
ExecuteOnce with initial_sql = its value; otherwise the mode is Interactive
with initial_sql ""."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    environment = _cott_validate_abi(environment, EnvironmentInputs, path="$.environment")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_arguments.py", "42c3eb0c2f19a188047ff37a526db1628110926139d7c46e94d551e1a2a56751", "parse_arguments", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_arguments")
        _result = _implementation(arguments, environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":20400,"end_column":1,"end_line":689,"start_byte":18806,"start_column":1,"start_line":658}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_arguments", phase="implementation-call", span={"end_byte":20400,"end_column":1,"end_line":689,"start_byte":18806,"start_column":1,"start_line":658}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_arguments", phase="implementation-call", span={"end_byte":20400,"end_column":1,"end_line":689,"start_byte":18806,"start_column":1,"start_line":658}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CliCommand, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidArguments,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.parse_arguments", phase="error", span={"end_byte":20400,"end_column":1,"end_line":689,"start_byte":18806,"start_column":1,"start_line":658}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidArguments:
        _cott_contract_condition(True, "real.pgcli.parse_arguments", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is CliCommand_Session and True and True and True:
            connection = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition((((connection).environment == environment)), "real.pgcli.parse_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.parse_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":20140,"end_column":101,"end_line":681,"start_byte":20044,"start_column":5,"start_line":681}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is CliCommand_Session and True and True and True:
            connection = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((((connection).inputs).password == "")), "real.pgcli.parse_arguments", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.parse_arguments", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.parse_arguments", clause="ensures:2", phase="ensures", span={"end_byte":20236,"end_column":96,"end_line":682,"start_byte":20145,"start_column":5,"start_line":682}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is CliCommand_Session and True and True and True:
            mode = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[1].name)
            sql = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[2].name)
            return (_cott_contract_condition((((mode == SessionMode_ExecuteOnce()) or (sql == ""))), "real.pgcli.parse_arguments", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.parse_arguments", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.parse_arguments", clause="ensures:3", phase="ensures", span={"end_byte":20342,"end_column":106,"end_line":683,"start_byte":20241,"start_column":5,"start_line":683}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CliCommand, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]:
    """Decide how to obtain a password: a nonempty password is used as is; an empty
one is prompted for unless prompting is disabled."""
    no_prompt = _cott_validate_abi(no_prompt, bool, path="$.no_prompt")
    password = _cott_validate_abi(password, str, path="$.password")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((no_prompt and (password == ""))), "real.pgcli.prompt_policy", "error:3:condition")):
        _expected_error = ConnectionError_PromptDisabled
        _expected_error_span = {"end_byte":20895,"end_column":75,"end_line":698,"start_byte":20825,"start_column":5,"start_line":698}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/prompt_policy.py", "a43b76c00b63c68e78d7dec858586b55e8cd85ea53e1d774600e6d845934c94c", "prompt_policy", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.prompt_policy")
        _result = _implementation(no_prompt, password)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.prompt_policy"
        if _error.span is None:
            _error.span = {"end_byte":20913,"end_column":1,"end_line":702,"start_byte":20400,"start_column":1,"start_line":689}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":20913,"end_column":1,"end_line":702,"start_byte":20400,"start_column":1,"start_line":689}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.prompt_policy", phase="implementation-call", span={"end_byte":20913,"end_column":1,"end_line":702,"start_byte":20400,"start_column":1,"start_line":689}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PromptAction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.prompt_policy", phase="error", span={"end_byte":20913,"end_column":1,"end_line":702,"start_byte":20400,"start_column":1,"start_line":689}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.prompt_policy", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.prompt_policy", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            action = _cott_match_value.value
            return (_cott_contract_condition(((((password != "") and (action == PromptAction_UsePassword())) or ((password == "") and (action == PromptAction_PromptPassword())))), "real.pgcli.prompt_policy", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.prompt_policy", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.prompt_policy", clause="ensures:1", phase="ensures", span={"end_byte":20799,"end_column":153,"end_line":695,"start_byte":20651,"start_column":5,"start_line":695}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PromptAction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]:
    """Resolve a password with short-circuit priority. A nonempty supplied_password
returns it with Supplied; otherwise a nonempty environment_password returns
it with Environment. These fields are already-resolved inputs: do not read
the process environment. Otherwise, when use_keyring is true, service and
user must be nonempty (else CredentialUnavailable) and the lock-selected
keyring is asked for the password stored for (service, user): a nonempty
answer returns it with Keyring; no entry or an empty entry continues; a
backend or lookup failure is CredentialUnavailable. Keyring entries are only
read, never written or deleted.
Still unresolved, call prompt_policy(no_prompt, "") and return its
PromptDisabled unchanged without touching the terminal. For PromptPassword,
prompt exactly once on the controlling terminal with the fixed prompt
"Password: " and hidden input; when hidden input is unavailable fail with
CredentialUnavailable instead of reading echoed input. A nonempty answer
returns it with Prompt; a submitted empty answer returns password "" with
source None (passwordless authentication). End of input, cancellation or
terminal failure is CredentialUnavailable."""
    request = _cott_validate_abi(request, CredentialRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((((request).supplied_password == "") and ((request).environment_password == "")) and (request).use_keyring) and (((request).service == "") or ((request).user == "")))), "real.pgcli.resolve_credential", "error:4:condition")):
        _expected_error = ConnectionError_CredentialUnavailable
        _expected_error_span = {"end_byte":22982,"end_column":200,"end_line":727,"start_byte":22787,"start_column":5,"start_line":727}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((((((request).supplied_password == "") and ((request).environment_password == "")) and (not (request).use_keyring)) and (request).no_prompt)), "real.pgcli.resolve_credential", "error:5:condition")):
        _expected_error = ConnectionError_PromptDisabled
        _expected_error_span = {"end_byte":23151,"end_column":169,"end_line":728,"start_byte":22987,"start_column":5,"start_line":728}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/resolve_credential.py", "a1bcae917c119be97428ecefbabf8e8bb19aea98f26e5ef33abb8b6d95cf4e5e", "resolve_credential", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.resolve_credential")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.resolve_credential"
        if _error.span is None:
            _error.span = {"end_byte":23288,"end_column":1,"end_line":734,"start_byte":20913,"start_column":1,"start_line":702}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.resolve_credential", phase="implementation-call", span={"end_byte":23288,"end_column":1,"end_line":734,"start_byte":20913,"start_column":1,"start_line":702}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.resolve_credential", phase="implementation-call", span={"end_byte":23288,"end_column":1,"end_line":734,"start_byte":20913,"start_column":1,"start_line":702}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CredentialResolution, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.resolve_credential", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_CredentialUnavailable, ConnectionError_PromptDisabled,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.resolve_credential", phase="error", span={"end_byte":23288,"end_column":1,"end_line":734,"start_byte":20913,"start_column":1,"start_line":702}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.resolve_credential", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.resolve_credential", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_CredentialUnavailable:
        _cott_contract_condition(True, "real.pgcli.resolve_credential", "error:6")
    if type(_result) is Err and type(_result.error) is ConnectionError_PromptDisabled:
        _cott_contract_condition(True, "real.pgcli.resolve_credential", "error:7")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolution = _cott_match_value.value
            return (_cott_contract_condition(((((resolution).password != "") or ((resolution).source == PasswordSource_None()))), "real.pgcli.resolve_credential", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.resolve_credential", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_credential", clause="ensures:1", phase="ensures", span={"end_byte":22389,"end_column":109,"end_line":723,"start_byte":22285,"start_column":5,"start_line":723}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolution = _cott_match_value.value
            return (_cott_contract_condition(((((request).supplied_password == "") or (((resolution).source == PasswordSource_Supplied()) and ((resolution).password == (request).supplied_password)))), "real.pgcli.resolve_credential", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.resolve_credential", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_credential", clause="ensures:2", phase="ensures", span={"end_byte":22563,"end_column":174,"end_line":724,"start_byte":22394,"start_column":5,"start_line":724}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolution = _cott_match_value.value
            return (_cott_contract_condition((((((request).supplied_password != "") or ((request).environment_password == "")) or (((resolution).source == PasswordSource_Environment()) and ((resolution).password == (request).environment_password)))), "real.pgcli.resolve_credential", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.resolve_credential", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.resolve_credential", clause="ensures:3", phase="ensures", span={"end_byte":22781,"end_column":218,"end_line":725,"start_byte":22568,"start_column":5,"start_line":725}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CredentialResolution, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def connect(plan: ConnectionPlan) -> Result[ConnectionReceipt, ConnectionError]:
    """Probe the server described by plan with the lock-selected psycopg driver:
open one authenticated connection with the ConnectionPlan parameters, execute
SELECT current_database(), current_user, current_setting('server_version'),
close the connection and return those values as the receipt. Success means an
authenticated query completed, not that a socket opened. The probe writes no
data and leaves no session, transaction, tunnel or process behind.

Without ssh connect directly. With Some(hop) use the installed OpenSSH ssh
executable with an argument vector, never a shell. The database host must be
a single host name or address (no comma-separated list, Unix socket path or
control characters); a missing host means localhost as seen from the jump
host. Keep that host name for TLS verification but connect with
hostaddr=127.0.0.1 and the forwarded local port.
Launch a foreground control master with -M -N, a private mode-0700 temporary
directory holding the control socket, BatchMode=yes, StrictHostKeyChecking=yes,
ExitOnForwardFailure=yes, ConnectTimeout=10, ControlPersist=no and
GatewayPorts=no, -p for the jump port, -l for the jump user and -i for
private_key when Some. The existing known_hosts is the authority: never
accept an unknown host key. Wait at most ten monotonic seconds for
ssh -S socket -O check to succeed. Pick a free loopback port through a
short-lived bound socket, then ask the master for
-O forward -L 127.0.0.1:port:dbhost:dbport, bracketing IPv6 hosts. Confirm the
forward succeeded before contacting PostgreSQL; a bind race is a failure,
never a reason to connect elsewhere. Every ssh command is bounded, has stdin
connected to the null device, never prompts, never carries a password in its
arguments, and its output is not copied into diagnostics.
On every path close the psycopg connection, ask the control master to exit,
terminate then kill and wait for the owned master process if it still runs,
and remove the temporary directory. Never signal an unrelated process.

Any validation, driver, authentication, TLS, SSH, query, timeout or cleanup
failure is ConnectionFailed with a fixed category message."""
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_3() -> bool:
        _cott_match_value = (plan).ssh
        if type(_cott_match_value) is Some and True:
            hop = _cott_match_value.value
            return (_cott_contract_condition(((((((hop).host == "") or _cott_starts_with((hop).host, "-")) or ((hop).user == "")) or ((hop).port == 0))), "real.pgcli.connect", "error:3:condition"))
        _cott_contract_condition((False), "real.pgcli.connect", "error:3:applicable")
        return False
    if _expected_error is None and (_cott_match_error_3()):
        _expected_error = ConnectionError_ConnectionFailed
        _expected_error_span = {"end_byte":26041,"end_column":169,"end_line":773,"start_byte":25877,"start_column":5,"start_line":773}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connect.py", "2694b9efe7e21ad086615c396dd4587ed3bb7aaf8c28cafff760324541ce610a", "connect", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connect")
        _result = _implementation(plan)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connect"
        if _error.span is None:
            _error.span = {"end_byte":26154,"end_column":1,"end_line":778,"start_byte":23288,"start_column":1,"start_line":734}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connect", phase="implementation-call", span={"end_byte":26154,"end_column":1,"end_line":778,"start_byte":23288,"start_column":1,"start_line":734}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connect", phase="implementation-call", span={"end_byte":26154,"end_column":1,"end_line":778,"start_byte":23288,"start_column":1,"start_line":734}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionReceipt, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_ConnectionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connect", phase="error", span={"end_byte":26154,"end_column":1,"end_line":778,"start_byte":23288,"start_column":1,"start_line":734}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connect", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.connect", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((((plan).settings).database == "") or ((receipt).database == ((plan).settings).database))), "real.pgcli.connect", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connect", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connect", clause="ensures:1", phase="ensures", span={"end_byte":25772,"end_column":111,"end_line":770,"start_byte":25666,"start_column":5,"start_line":770}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((((plan).settings).user == "") or ((receipt).user == ((plan).settings).user))), "real.pgcli.connect", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.connect", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connect", clause="ensures:2", phase="ensures", span={"end_byte":25871,"end_column":99,"end_line":771,"start_byte":25777,"start_column":5,"start_line":771}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionReceipt, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def begin_transaction(mode: TransactionMode) -> TransactionState:
    """Open an explicit transaction in the client's transaction model."""
    mode = _cott_validate_abi(mode, TransactionMode, path="$.mode")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/begin_transaction.py", "ee5b76a6d9c556710ed1e423d8079cd77a3e873874319b110ab6afe63ebb4502", "begin_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.begin_transaction")
        _result = _implementation(mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.begin_transaction"
        if _error.span is None:
            _error.span = {"end_byte":26411,"end_column":1,"end_line":788,"start_byte":26154,"start_column":1,"start_line":778}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.begin_transaction", phase="implementation-call", span={"end_byte":26411,"end_column":1,"end_line":788,"start_byte":26154,"start_column":1,"start_line":778}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.begin_transaction", phase="implementation-call", span={"end_byte":26411,"end_column":1,"end_line":788,"start_byte":26154,"start_column":1,"start_line":778}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TransactionState, path="$.return")
    if not (_cott_contract_condition((((_result).mode == mode)), "real.pgcli.begin_transaction", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.begin_transaction", clause="ensures:1", phase="ensures", span={"end_byte":26339,"end_column":32,"end_line":783,"start_byte":26312,"start_column":5,"start_line":783}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).status == TransactionStatus_Active())), "real.pgcli.begin_transaction", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.begin_transaction", clause="ensures:2", phase="ensures", span={"end_byte":26393,"end_column":54,"end_line":784,"start_byte":26344,"start_column":5,"start_line":784}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TransactionState, path="$.return", validator=_cott_validate_abi)
    return _result

def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    """Commit the open transaction. Committing when no transaction is open, or after
it failed (PostgreSQL rolls a failed transaction back instead), is
TransactionFailed."""
    transaction = _cott_validate_abi(transaction, TransactionState, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((transaction).status != TransactionStatus_Active())), "real.pgcli.commit_transaction", "error:3:condition")):
        _expected_error = ClientError_TransactionFailed
        _expected_error_span = {"end_byte":26935,"end_column":92,"end_line":798,"start_byte":26848,"start_column":5,"start_line":798}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/commit_transaction.py", "83027801a268dba6d45302a389a6c76beaa8eeef428b8ab565eb9308f68d408c", "commit_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.commit_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":26953,"end_column":1,"end_line":802,"start_byte":26411,"start_column":1,"start_line":788}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.commit_transaction", phase="implementation-call", span={"end_byte":26953,"end_column":1,"end_line":802,"start_byte":26411,"start_column":1,"start_line":788}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.commit_transaction", phase="implementation-call", span={"end_byte":26953,"end_column":1,"end_line":802,"start_byte":26411,"start_column":1,"start_line":788}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransactionState, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.commit_transaction", phase="error", span={"end_byte":26953,"end_column":1,"end_line":802,"start_byte":26411,"start_column":1,"start_line":788}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.commit_transaction", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            committed = _cott_match_value.value
            return (_cott_contract_condition(((((committed).mode == (transaction).mode) and ((committed).status == TransactionStatus_Idle()))), "real.pgcli.commit_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.commit_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.commit_transaction", clause="ensures:1", phase="ensures", span={"end_byte":26822,"end_column":120,"end_line":795,"start_byte":26707,"start_column":5,"start_line":795}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransactionState, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    """Roll back an open or failed transaction. Rolling back when no transaction is
open is TransactionFailed."""
    transaction = _cott_validate_abi(transaction, TransactionState, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((transaction).status == TransactionStatus_Idle())), "real.pgcli.rollback_transaction", "error:3:condition")):
        _expected_error = ClientError_TransactionFailed
        _expected_error_span = {"end_byte":27419,"end_column":90,"end_line":811,"start_byte":27334,"start_column":5,"start_line":811}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/rollback_transaction.py", "a4e51ac2fbd6910dc99f54d3b5468150bd01579c183ce1d85f303c0bf0e8fb45", "rollback_transaction", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.rollback_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":27437,"end_column":1,"end_line":815,"start_byte":26953,"start_column":1,"start_line":802}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.rollback_transaction", phase="implementation-call", span={"end_byte":27437,"end_column":1,"end_line":815,"start_byte":26953,"start_column":1,"start_line":802}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.rollback_transaction", phase="implementation-call", span={"end_byte":27437,"end_column":1,"end_line":815,"start_byte":26953,"start_column":1,"start_line":802}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransactionState, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.rollback_transaction", phase="error", span={"end_byte":27437,"end_column":1,"end_line":815,"start_byte":26953,"start_column":1,"start_line":802}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.rollback_transaction", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rolled_back = _cott_match_value.value
            return (_cott_contract_condition(((((rolled_back).mode == (transaction).mode) and ((rolled_back).status == TransactionStatus_Idle()))), "real.pgcli.rollback_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.rollback_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.rollback_transaction", clause="ensures:1", phase="ensures", span={"end_byte":27308,"end_column":126,"end_line":808,"start_byte":27187,"start_column":5,"start_line":808}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransactionState, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult:
    """Complete the word that ends at request.cursor. The word starts right after
the last character before the cursor that is not a Unicode letter or digit,
"_" or "."; replace_start is that position and the prefix is the text from
replace_start to the cursor. A candidate matches when it starts with the
prefix ignoring ASCII case.
Candidates, in this order: for each catalog table, its name, then
schema + "." + name, then each column name unless in relation context; then,
when policy.include_keywords is true and not in relation context, each word
of SQL_KEYWORDS. Relation context means the nearest whitespace-separated word
before replace_start equals FROM, JOIN, INTO, UPDATE or TABLE ignoring ASCII
case. Keep matching candidates, drop exact duplicates, sort by the
ASCII-lowercased text and then by the text itself, and return the first
policy.max_candidates."""
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    policy = _cott_validate_abi(policy, CompletionPolicy, path="$.policy")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_catalog_sql.py", "8453d569d49c8c7dab8ad00aa9a2f42b80e4368dffc36d6610a012cfe3eb6d15", "complete_catalog_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_catalog_sql")
        _result = _implementation(request, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_catalog_sql"
        if _error.span is None:
            _error.span = {"end_byte":28599,"end_column":1,"end_line":837,"start_byte":27437,"start_column":1,"start_line":815}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_catalog_sql", phase="implementation-call", span={"end_byte":28599,"end_column":1,"end_line":837,"start_byte":27437,"start_column":1,"start_line":815}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_catalog_sql", phase="implementation-call", span={"end_byte":28599,"end_column":1,"end_line":837,"start_byte":27437,"start_column":1,"start_line":815}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not (_cott_contract_condition(((len((_result).candidates) <= (policy).max_candidates)), "real.pgcli.complete_catalog_sql", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.complete_catalog_sql", clause="ensures:1", phase="ensures", span={"end_byte":28530,"end_column":59,"end_line":832,"start_byte":28476,"start_column":5,"start_line":832}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).replace_start <= (request).cursor)), "real.pgcli.complete_catalog_sql", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.complete_catalog_sql", clause="ensures:2", phase="ensures", span={"end_byte":28581,"end_column":51,"end_line":833,"start_byte":28535,"start_column":5,"start_line":833}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest) -> CompletionResult:
    """Complete with the default interactive policy: the result is exactly
complete_catalog_sql(request, CompletionPolicy(max_candidates: 50,
include_keywords: true))."""
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/complete_sql.py", "d5e2055264ad97f904f928eca526c8dc715e65e4670b2df672a937a82b11ea01", "complete_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.complete_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":28966,"end_column":1,"end_line":849,"start_byte":28599,"start_column":1,"start_line":837}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":28966,"end_column":1,"end_line":849,"start_byte":28599,"start_column":1,"start_line":837}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.complete_sql", phase="implementation-call", span={"end_byte":28966,"end_column":1,"end_line":849,"start_byte":28599,"start_column":1,"start_line":837}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not (_cott_contract_condition(((len((_result).candidates) <= 50)), "real.pgcli.complete_sql", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.complete_sql", clause="ensures:1", phase="ensures", span={"end_byte":28897,"end_column":40,"end_line":844,"start_byte":28862,"start_column":5,"start_line":844}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).replace_start <= (request).cursor)), "real.pgcli.complete_sql", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.complete_sql", clause="ensures:2", phase="ensures", span={"end_byte":28948,"end_column":51,"end_line":845,"start_byte":28902,"start_column":5,"start_line":845}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def highlight_sql(request: HighlightRequest) -> HighlightedSql:
    """Mark SQL for a terminal. contains_error is true exactly when the source ends
inside a single-quoted string, a double-quoted identifier, a dollar-quoted
string ($$ or $tag$) or a /* block comment; quotes are escaped by doubling
and a -- comment ends at a line feed.
When color is false text is source. When color is true text is source with
each keyword wrapped between ESC "[1m" and ESC "[0m" and each complete
single-quoted string literal, quotes included, wrapped between ESC "[32m" and
ESC "[0m", where ESC is U+001B. A keyword is a maximal sequence of ASCII letters
and "_" outside quotes and comments that equals a word of SQL_KEYWORDS
ignoring ASCII case. All other characters are copied unchanged."""
    request = _cott_validate_abi(request, HighlightRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/highlight_sql.py", "118b144eb79ef7a653a264fc128d634b89e9c73ec689d528b7e60f42f796cb78", "highlight_sql", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.highlight_sql")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.highlight_sql"
        if _error.span is None:
            _error.span = {"end_byte":29873,"end_column":1,"end_line":867,"start_byte":28966,"start_column":1,"start_line":849}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.highlight_sql", phase="implementation-call", span={"end_byte":29873,"end_column":1,"end_line":867,"start_byte":28966,"start_column":1,"start_line":849}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.highlight_sql", phase="implementation-call", span={"end_byte":29873,"end_column":1,"end_line":867,"start_byte":28966,"start_column":1,"start_line":849}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, HighlightedSql, path="$.return")
    if not (_cott_contract_condition((((request).color or ((_result).text == (request).source))), "real.pgcli.highlight_sql", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.highlight_sql", clause="ensures:1", phase="ensures", span={"end_byte":29855,"end_column":61,"end_line":863,"start_byte":29799,"start_column":5,"start_line":863}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, HighlightedSql, path="$.return", validator=_cott_validate_abi)
    return _result

def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]:
    """Plan the buffer's SQL text for one submission. Statements are separated by
semicolons outside single-quoted strings (quotes escaped by doubling),
double-quoted identifiers, dollar-quoted strings ($$ or $tag$), -- line
comments and /* */ block comments. statement_count counts separated pieces
that contain something other than whitespace and comments; sql is
buffer.text unchanged. requires_terminator is true exactly when
buffer.multiline is true and the text does not end with a separating
semicolon once trailing whitespace and comments are ignored, including when
it ends inside a quote or comment. A text without any statement is
InvalidSql, and so is a text that ends inside a quote, identifier, dollar
quote or block comment when buffer.multiline is false."""
    buffer = _cott_validate_abi(buffer, InputBuffer, path="$.buffer")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((buffer).text == "")), "real.pgcli.plan_query", "error:4:condition")):
        _expected_error = ClientError_InvalidSql
        _expected_error_span = {"end_byte":31021,"end_column":56,"end_line":886,"start_byte":30970,"start_column":5,"start_line":886}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/plan_query.py", "a0ca66198ff8c1ec12f611197ade7b87988d86a74532f134f00931f646e68e35", "plan_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.plan_query")
        _result = _implementation(buffer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.plan_query"
        if _error.span is None:
            _error.span = {"end_byte":31072,"end_column":1,"end_line":891,"start_byte":29873,"start_column":1,"start_line":867}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.plan_query", phase="implementation-call", span={"end_byte":31072,"end_column":1,"end_line":891,"start_byte":29873,"start_column":1,"start_line":867}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.plan_query", phase="implementation-call", span={"end_byte":31072,"end_column":1,"end_line":891,"start_byte":29873,"start_column":1,"start_line":867}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryPlan, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.plan_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.plan_query", phase="error", span={"end_byte":31072,"end_column":1,"end_line":891,"start_byte":29873,"start_column":1,"start_line":867}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.plan_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.plan_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidSql:
        _cott_contract_condition(True, "real.pgcli.plan_query", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((plan).sql == (buffer).text)), "real.pgcli.plan_query", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.plan_query", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.plan_query", clause="ensures:1", phase="ensures", span={"end_byte":30826,"end_column":55,"end_line":882,"start_byte":30776,"start_column":5,"start_line":882}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((plan).statement_count > 0)), "real.pgcli.plan_query", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.plan_query", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.plan_query", clause="ensures:2", phase="ensures", span={"end_byte":30882,"end_column":56,"end_line":883,"start_byte":30831,"start_column":5,"start_line":883}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((((buffer).multiline or (not (plan).requires_terminator))), "real.pgcli.plan_query", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.plan_query", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.plan_query", clause="ensures:3", phase="ensures", span={"end_byte":30964,"end_column":82,"end_line":884,"start_byte":30887,"start_column":5,"start_line":884}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryPlan, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer:
    """Insert input into buffer.text at buffer.cursor and move the cursor to the end
of the inserted text."""
    buffer = _cott_validate_abi(buffer, InputBuffer, path="$.buffer")
    input = _cott_validate_abi(input, str, path="$.input")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/edit_multiline.py", "ac5c6c23809133b82bd7831d2a68523b50323863107da3200dc0fff104c8e3ed", "edit_multiline", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.edit_multiline")
        _result = _implementation(buffer, input)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.edit_multiline"
        if _error.span is None:
            _error.span = {"end_byte":31448,"end_column":1,"end_line":903,"start_byte":31072,"start_column":1,"start_line":891}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.edit_multiline", phase="implementation-call", span={"end_byte":31448,"end_column":1,"end_line":903,"start_byte":31072,"start_column":1,"start_line":891}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.edit_multiline", phase="implementation-call", span={"end_byte":31448,"end_column":1,"end_line":903,"start_byte":31072,"start_column":1,"start_line":891}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, InputBuffer, path="$.return")
    if not (_cott_contract_condition(((len((_result).text) == (len((buffer).text) + len(input)))), "real.pgcli.edit_multiline", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_multiline", clause="ensures:1", phase="ensures", span={"end_byte":31326,"end_column":59,"end_line":897,"start_byte":31272,"start_column":5,"start_line":897}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).cursor == ((buffer).cursor + len(input)))), "real.pgcli.edit_multiline", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_multiline", clause="ensures:2", phase="ensures", span={"end_byte":31381,"end_column":55,"end_line":898,"start_byte":31331,"start_column":5,"start_line":898}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).multiline == (buffer).multiline)), "real.pgcli.edit_multiline", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_multiline", clause="ensures:3", phase="ensures", span={"end_byte":31430,"end_column":49,"end_line":899,"start_byte":31386,"start_column":5,"start_line":899}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, InputBuffer, path="$.return", validator=_cott_validate_abi)
    return _result

def parse_meta_command(source: str) -> MetaCommand:
    """Parse one backslash-command line. Trim surrounding whitespace, drop one
trailing ";" and trim again. The command word is the text before the first
whitespace; the argument is the rest with surrounding whitespace removed.
A command word longer than two characters that ends in "+" is read without
the "+". Command words are case-sensitive. An unrecognized word, a missing
required argument, an argument given to a no-argument command and an invalid
argument value all give Unknown(source: source) with the original source.

No argument: \\q, \\quit, quit, exit -> Quit; \\# or \\refresh -> RefreshCatalog;
\\? or help -> Help; \\conninfo -> ConnectionInfo; \\du or \\dg -> ListRoles;
\\dx -> ListExtensions; \\l or \\list -> ListDatabases; \\e -> EditBuffer;
\\timing -> Timing; \\x -> Expanded; \\g -> ExecuteBuffer; \\G -> ExecuteExpanded;
\\p -> PrintBuffer; \\r -> ResetBuffer.
Pattern (the argument, possibly ""): \\d Describe, \\dD ListDomains,
\\dE ListForeignTables, \\dF ListTextSearchConfigurations, \\dT ListDataTypes,
\\db ListTablespaces, \\ddp ListDefaultPrivileges, \\df ListFunctions,
\\di ListIndexes, \\dm ListMaterializedViews, \\dn ListSchemas, \\dp or \\z
ListPrivileges, \\ds ListSequences, \\dt ListTables, \\dv ListViews, \\s History,
\\fl ListFavorites.
Required single-word argument: \\sf ShowFunction, \\c or \\connect Connect,
\\nd DeleteNamedQuery, \\np PrintNamedQuery, \\fd DeleteFavorite; path
arguments \\i ReadFile, \\ir ReadRelativeFile, \\w WriteBuffer, where one pair of
matching surrounding single or double quotes is removed.
Optional argument: \\h topic -> SqlHelp(topic), or Help when empty;
\\echo text -> Echo; \\qecho text -> QueryOutputEcho; \\f name -> Favorite, or
ListFavorites(pattern: "") when empty.
Structured: \\T name -> SetFormat(format) when name, ignoring ASCII case, is
that format's \\T name; \\pager on|off -> SetPager; \\n name [words...] -> NamedQuery with the
whitespace-separated words after the name as arguments; \\ns name sql ->
SaveNamedQuery with sql the nonempty rest after the name; \\copy table to|from
path -> Copy(table, path, from_file: the direction is "from" ignoring ASCII
case), removing matching quotes around path."""
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/parse_meta_command.py", "7d972c21dca5ecf415b92babd1c9165ca437210cb10ca1575d7acc24ddfe63d7", "parse_meta_command", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.parse_meta_command")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.parse_meta_command"
        if _error.span is None:
            _error.span = {"end_byte":33804,"end_column":1,"end_line":941,"start_byte":31448,"start_column":1,"start_line":903}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.parse_meta_command", phase="implementation-call", span={"end_byte":33804,"end_column":1,"end_line":941,"start_byte":31448,"start_column":1,"start_line":903}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.parse_meta_command", phase="implementation-call", span={"end_byte":33804,"end_column":1,"end_line":941,"start_byte":31448,"start_column":1,"start_line":903}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, MetaCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, MetaCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def recognize_backslash(source: str) -> BackslashCommand:
    """Classify source through parse_meta_command(source): Quit -> Quit, Help -> Help,
ListTables -> Tables, Describe -> Describe, every other command -> Unknown."""
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/recognize_backslash.py", "fb17e09d1766d78c5f3554676403cb67a67b794a40dc8d4287fff360b008d907", "recognize_backslash", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.recognize_backslash")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.recognize_backslash"
        if _error.span is None:
            _error.span = {"end_byte":34062,"end_column":1,"end_line":949,"start_byte":33804,"start_column":1,"start_line":941}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":34062,"end_column":1,"end_line":949,"start_byte":33804,"start_column":1,"start_line":941}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.recognize_backslash", phase="implementation-call", span={"end_byte":34062,"end_column":1,"end_line":949,"start_byte":33804,"start_column":1,"start_line":941}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, BackslashCommand, path="$.return")
    _result = _cott_wrap_async_protocol(_result, BackslashCommand, path="$.return", validator=_cott_validate_abi)
    return _result

def render_query(request: RenderRequest) -> RenderedQuery:
    """Render a text table. Each row is read as exactly columns.len cells: missing
cells are "" and extra cells are ignored. Lengths count Unicode code points.
Horizontal: a header line of the column names, a separator line, then one
line per row. Each cell is left-justified with spaces to its column width
(the longest of the name and that column's cells) and cells are joined by
" | "; the separator joins runs of "-" of each column width with "-+-".
Vertical: for each row n counted from 1, the line "-[ RECORD n ]" followed by
one line per column holding the name left-justified to the longest column
name, " | ", then the cell.
Trailing spaces are removed from every line and lines are joined by line
feeds without a final one; no columns gives "". terminal_width neither wraps
nor truncates. layout is request.layout."""
    request = _cott_validate_abi(request, RenderRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/render_query.py", "b0821953f30c7ec71547893569f436956a16b5efbad22ec5060aa35c54d59cf8", "render_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.render_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.render_query"
        if _error.span is None:
            _error.span = {"end_byte":35068,"end_column":1,"end_line":969,"start_byte":34062,"start_column":1,"start_line":949}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":35068,"end_column":1,"end_line":969,"start_byte":34062,"start_column":1,"start_line":949}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.render_query", phase="implementation-call", span={"end_byte":35068,"end_column":1,"end_line":969,"start_byte":34062,"start_column":1,"start_line":949}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, RenderedQuery, path="$.return")
    if not (_cott_contract_condition((((_result).layout == (request).layout)), "real.pgcli.render_query", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.render_query", clause="ensures:1", phase="ensures", span={"end_byte":35050,"end_column":44,"end_line":965,"start_byte":35011,"start_column":5,"start_line":965}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, RenderedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def format_query(request: FormatRequest) -> FormattedQuery:
    """Format a query result. Keep the first max_rows rows (0 keeps none);
truncated_rows is the number of rows left out. When max_column_width is
positive each kept cell longer than it (in code points) becomes its first
max_column_width - 1 code points followed by "…"; column names are not
clipped. By format:
Aligned: render_query with Horizontal layout; when that result's width
exceeds terminal_width use render_query with Vertical layout instead.
Vertical: render_query with Vertical layout.
Csv and Tsv: RFC 4180 records with "," or a tab as delimiter, a header record
of the column names, a field quoted with '"' (inner quotes doubled) only when
it contains the delimiter, a quote, CR or LF, records joined by line feeds
without a final one.
Json: a JSON array holding per row an object that maps each column name to its
cell string in column order (a repeated name keeps its last cell), indented
by 2 spaces, non-ASCII characters unescaped. JsonLines: the same objects, one
compact object per line.
Html: the lines "<table>", "<thead><tr>" + one "<th>name</th>" per column +
"</tr></thead>", "<tbody>", one "<tr>" + "<td>cell</td>" per cell + "</tr>"
line per row, "</tbody>", "</table>", escaping &, <, >, " and '.
Latex: "\\begin{tabular}{" + one "l" per column + "}", the header row, "\\hline",
the rows, "\\end{tabular}"; cells are joined by " & ", each row ends with
" \\\\"; in cells \\ becomes \\textbackslash{} and each of & % $ # _ { } gets a
preceding \\.
Markdown: "| " + cells joined by " | " + " |" for the header and each row, with
a "|" + "---|" per column separator after the header; "|" in cells is "\\|".
rendered.layout is Vertical for Vertical and for auto-expanded Aligned
output, Horizontal otherwise."""
    request = _cott_validate_abi(request, FormatRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/format_query.py", "cd77d80cf717586bf869c973165432f093cc8960d7cb443e1362b80e2e596e79", "format_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.format_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.format_query"
        if _error.span is None:
            _error.span = {"end_byte":37309,"end_column":1,"end_line":1006,"start_byte":35068,"start_column":1,"start_line":969}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.format_query", phase="implementation-call", span={"end_byte":37309,"end_column":1,"end_line":1006,"start_byte":35068,"start_column":1,"start_line":969}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.format_query", phase="implementation-call", span={"end_byte":37309,"end_column":1,"end_line":1006,"start_byte":35068,"start_column":1,"start_line":969}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, FormattedQuery, path="$.return")
    if not (_cott_contract_condition((((len(((request).query).rows) <= (request).max_rows) or ((_result).truncated_rows == (len(((request).query).rows) - (request).max_rows)))), "real.pgcli.format_query", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.format_query", clause="ensures:1", phase="ensures", span={"end_byte":37101,"end_column":127,"end_line":1000,"start_byte":36979,"start_column":5,"start_line":1000}, expected="true", actual="false")
    if not (_cott_contract_condition((((len(((request).query).rows) > (request).max_rows) or ((_result).truncated_rows == 0))), "real.pgcli.format_query", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.format_query", clause="ensures:2", phase="ensures", span={"end_byte":37187,"end_column":86,"end_line":1001,"start_byte":37106,"start_column":5,"start_line":1001}, expected="true", actual="false")
    if not (_cott_contract_condition((((not ((request).format == TableFormat_Vertical())) or (((_result).rendered).layout == RenderLayout_Vertical()))), "real.pgcli.format_query", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.format_query", clause="ensures:3", phase="ensures", span={"end_byte":37291,"end_column":104,"end_line":1002,"start_byte":37192,"start_column":5,"start_line":1002}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FormattedQuery, path="$.return", validator=_cott_validate_abi)
    return _result

def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]:
    """Append entry to entries, then apply HistoryPolicy normalization. This is a
pure list transformation with no clock or filesystem access."""
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    entries = _cott_validate_abi(entries, CottList[HistoryEntry], path="$.entries")
    entry = _cott_validate_abi(entry, HistoryEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/remember_history.py", "31b998c36d56fa22fd71590ca562e29796c47fa5f20316460145f23ebf9089ff", "remember_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.remember_history")
        _result = _implementation(policy, entries, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.remember_history"
        if _error.span is None:
            _error.span = {"end_byte":37667,"end_column":1,"end_line":1020,"start_byte":37309,"start_column":1,"start_line":1006}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.remember_history", phase="implementation-call", span={"end_byte":37667,"end_column":1,"end_line":1020,"start_byte":37309,"start_column":1,"start_line":1006}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.remember_history", phase="implementation-call", span={"end_byte":37667,"end_column":1,"end_line":1020,"start_byte":37309,"start_column":1,"start_line":1006}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[HistoryEntry], path="$.return")
    if not (_cott_contract_condition(((len(_result) <= (policy).max_entries)), "real.pgcli.remember_history", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.remember_history", clause="ensures:1", phase="ensures", span={"end_byte":37649,"end_column":45,"end_line":1016,"start_byte":37609,"start_column":5,"start_line":1016}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[HistoryEntry], path="$.return", validator=_cott_validate_abi)
    return _result

def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]:
    """Read policy.path as the HistoryEntry JSON format, validate every element,
including elements normalization later drops, and then apply HistoryPolicy
normalization. A missing file is an empty success. Invalid UTF-8 or JSON, a
root that is not an array, an element that is not an object with exactly the
four fields and their types, a file larger than 16 MiB (read with a bounded
read), a symlink or non-regular file and any other I/O failure return
HistoryFailed(path: policy.path, message: a fixed category). File content is
data and is never executed. policy.path is read from the file system the
program runs against: the fs fixture root while a Cott scenario with an fs
fixture is active, otherwise the host file system."""
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/load_history.py", "c05f520c1192471605221846a1954e248616bf6e2d0a8414394db4d15290e721", "load_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.load_history")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.load_history"
        if _error.span is None:
            _error.span = {"end_byte":38666,"end_column":1,"end_line":1040,"start_byte":37667,"start_column":1,"start_line":1020}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.load_history", phase="implementation-call", span={"end_byte":38666,"end_column":1,"end_line":1040,"start_byte":37667,"start_column":1,"start_line":1020}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.load_history", phase="implementation-call", span={"end_byte":38666,"end_column":1,"end_line":1040,"start_byte":37667,"start_column":1,"start_line":1020}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[HistoryEntry], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_HistoryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.load_history", phase="error", span={"end_byte":38666,"end_column":1,"end_line":1040,"start_byte":37667,"start_column":1,"start_line":1020}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_history", clause="ensures:1", phase="ensures", span={"end_byte":38602,"end_column":68,"end_line":1034,"start_byte":38539,"start_column":5,"start_line":1034}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[HistoryEntry], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]:
    """Apply HistoryPolicy normalization to entries and write the HistoryEntry JSON
format with non-ASCII characters unescaped, compact separators and one final
line feed, preserving field values exactly; serialized data larger than
16 MiB is rejected. Replace policy.path atomically: write an exclusively
created same-directory temporary file with mode 0600, flush and fsync it,
rename it over the target, then fsync the parent directory. Parent
directories are not created; a symlink or non-regular existing target is
rejected. A failure before the rename keeps the previous file and removes the
temporary file. Serialization and I/O failures return
HistoryFailed(path: policy.path, message: a fixed category). policy.path is
replaced in the file system the program runs against: the fs fixture root
while a Cott scenario with an fs fixture is active, otherwise the host file
system."""
    policy = _cott_validate_abi(policy, HistoryPolicy, path="$.policy")
    entries = _cott_validate_abi(entries, CottList[HistoryEntry], path="$.entries")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/save_history.py", "9b8be600acb649a9dce2289d4c949a3349199e64d1666ede5e565aa4a76d220f", "save_history", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.save_history")
        _result = _implementation(policy, entries)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.save_history"
        if _error.span is None:
            _error.span = {"end_byte":39908,"end_column":1,"end_line":1064,"start_byte":38666,"start_column":1,"start_line":1040}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.save_history", phase="implementation-call", span={"end_byte":39908,"end_column":1,"end_line":1064,"start_byte":38666,"start_column":1,"start_line":1040}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.save_history", phase="implementation-call", span={"end_byte":39908,"end_column":1,"end_line":1064,"start_byte":38666,"start_column":1,"start_line":1040}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_HistoryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.save_history", phase="error", span={"end_byte":39908,"end_column":1,"end_line":1064,"start_byte":38666,"start_column":1,"start_line":1040}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.save_history", clause="ensures:1", phase="ensures", span={"end_byte":39843,"end_column":44,"end_line":1058,"start_byte":39804,"start_column":5,"start_line":1058}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]:
    """Read store.path as the Favorite JSON format; a missing file is an empty
success. Entries are checked in file order and the first problem decides the
error: an entry whose name is blank or repeats an earlier name gives
FavoriteFailed(name: that name), and an entry with a wrong shape gives
FavoriteFailed(name: ""). After all entries pass, more than store.max_entries
entries is FavoriteFailed(name: ""). Invalid UTF-8 or JSON, a root that is not
an array, a file larger than 16 MiB (read with a bounded read), a symlink or
non-regular file and any other I/O failure are FavoriteFailed(name: "").
Valid entries keep file order and invalid entries are never skipped.
store.path is read from the file system the program runs against: the fs
fixture root while a Cott scenario with an fs fixture is active, otherwise the
host file system."""
    store = _cott_validate_abi(store, FavoriteStore, path="$.store")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/load_favorites.py", "3f3460e5940298d0a20aa51c3169c0dae7c0e6c24c1dfa2c47a0db0d435317bf", "load_favorites", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.load_favorites")
        _result = _implementation(store)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.load_favorites"
        if _error.span is None:
            _error.span = {"end_byte":41178,"end_column":1,"end_line":1088,"start_byte":39908,"start_column":1,"start_line":1064}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.load_favorites", phase="implementation-call", span={"end_byte":41178,"end_column":1,"end_line":1088,"start_byte":39908,"start_column":1,"start_line":1064}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.load_favorites", phase="implementation-call", span={"end_byte":41178,"end_column":1,"end_line":1088,"start_byte":39908,"start_column":1,"start_line":1064}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[Favorite], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.load_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_FavoriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.load_favorites", phase="error", span={"end_byte":41178,"end_column":1,"end_line":1088,"start_byte":39908,"start_column":1,"start_line":1064}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.load_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.load_favorites", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.load_favorites", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            favorites = _cott_match_value.value
            return (_cott_contract_condition(((len(favorites) <= (store).max_entries)), "real.pgcli.load_favorites", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.load_favorites", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_favorites", clause="ensures:1", phase="ensures", span={"end_byte":40962,"end_column":71,"end_line":1080,"start_byte":40896,"start_column":5,"start_line":1080}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            favorites = _cott_match_value.value
            return (_cott_contract_condition((_cott_unique_by(favorites, "name")), "real.pgcli.load_favorites", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.load_favorites", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_favorites", clause="ensures:2", phase="ensures", span={"end_byte":41034,"end_column":72,"end_line":1081,"start_byte":40967,"start_column":5,"start_line":1081}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            favorites = _cott_match_value.value
            return (_cott_contract_condition(((not _cott_any_blank_by(favorites, "name"))), "real.pgcli.load_favorites", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.load_favorites", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.load_favorites", clause="ensures:3", phase="ensures", span={"end_byte":41113,"end_column":79,"end_line":1082,"start_byte":41039,"start_column":5,"start_line":1082}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[Favorite], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]:
    """Write favorites in the given order as the Favorite JSON format with non-ASCII
characters unescaped, compact separators and one final line feed; serialized
data larger than 16 MiB is rejected. Replace store.path atomically: write an
exclusively created same-directory temporary file with mode 0600, flush and
fsync it, rename it over the target, then fsync the parent directory. Parent
directories are not created; a symlink or non-regular existing target is
rejected; a failure before the rename keeps the previous file and removes the
temporary file. The first entry whose name is blank or repeats an earlier name
is reported as FavoriteFailed(name: that name); capacity, serialization and
I/O failures are FavoriteFailed(name: ""). store.path is replaced in the file
system the program runs against: the fs fixture root while a Cott scenario
with an fs fixture is active, otherwise the host file system."""
    store = _cott_validate_abi(store, FavoriteStore, path="$.store")
    favorites = _cott_validate_abi(favorites, CottList[Favorite], path="$.favorites")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((_cott_any_blank_by(favorites, "name")), "real.pgcli.save_favorites", "error:2:condition")):
        _expected_error = ClientError_FavoriteFailed
        _expected_error_span = {"end_byte":42461,"end_column":81,"end_line":1107,"start_byte":42385,"start_column":5,"start_line":1107}
        _expected_error_clause = "error:2"
    if _expected_error is None and (_cott_contract_condition(((not _cott_unique_by(favorites, "name"))), "real.pgcli.save_favorites", "error:3:condition")):
        _expected_error = ClientError_FavoriteFailed
        _expected_error_span = {"end_byte":42543,"end_column":82,"end_line":1108,"start_byte":42466,"start_column":5,"start_line":1108}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition(((len(favorites) > (store).max_entries)), "real.pgcli.save_favorites", "error:4:condition")):
        _expected_error = ClientError_FavoriteFailed
        _expected_error_span = {"end_byte":42619,"end_column":76,"end_line":1109,"start_byte":42548,"start_column":5,"start_line":1109}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/save_favorites.py", "07fbdc18c0705079d24289dfa0f67342b4681c607775982b212253c6f6dd0760", "save_favorites", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.save_favorites")
        _result = _implementation(store, favorites)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.save_favorites"
        if _error.span is None:
            _error.span = {"end_byte":42684,"end_column":1,"end_line":1114,"start_byte":41178,"start_column":1,"start_line":1088}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.save_favorites", phase="implementation-call", span={"end_byte":42684,"end_column":1,"end_line":1114,"start_byte":41178,"start_column":1,"start_line":1088}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.save_favorites", phase="implementation-call", span={"end_byte":42684,"end_column":1,"end_line":1114,"start_byte":41178,"start_column":1,"start_line":1088}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.save_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_FavoriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.save_favorites", phase="error", span={"end_byte":42684,"end_column":1,"end_line":1114,"start_byte":41178,"start_column":1,"start_line":1088}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.save_favorites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.save_favorites", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.save_favorites", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition(((saved == UNIT)), "real.pgcli.save_favorites", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.save_favorites", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.save_favorites", clause="ensures:1", phase="ensures", span={"end_byte":42379,"end_column":44,"end_line":1105,"start_byte":42340,"start_column":5,"start_line":1105}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    """Run sql once on a new autocommit connection built only from the nonempty
fields of connection (host, port, user, password, dbname; libpq defaults
otherwise; no connection string, TLS settings or SSH hop), then close it.
Return the columns and all rows of the last statement that produced rows, in
server order, with QueryResult cell text; no columns and no rows when no
statement produced rows. Failing to open the connection or authenticate is
ConnectionFailed; a statement error is QueryFailed."""
    connection = _cott_validate_abi(connection, ConnectionSettings, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_query.py", "acb6e612b4a9981f7b561ed713c2cd4d331bddd0f73e7c6007d4087cb52b2bed", "execute_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_query")
        _result = _implementation(connection, sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_query"
        if _error.span is None:
            _error.span = {"end_byte":43552,"end_column":1,"end_line":1132,"start_byte":42684,"start_column":1,"start_line":1114}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":43552,"end_column":1,"end_line":1132,"start_byte":42684,"start_column":1,"start_line":1114}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_query", phase="implementation-call", span={"end_byte":43552,"end_column":1,"end_line":1132,"start_byte":42684,"start_column":1,"start_line":1114}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryResult, DatabaseError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (DatabaseError_ConnectionFailed, DatabaseError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_query", phase="error", span={"end_byte":43552,"end_column":1,"end_line":1132,"start_byte":42684,"start_column":1,"start_line":1114}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.execute_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is DatabaseError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.execute_query", "error:2")
    if type(_result) is Err and type(_result.error) is DatabaseError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.execute_query", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            query_result = _cott_match_value.value
            return (_cott_contract_condition((((len((query_result).rows) == 0) or (len((query_result).columns) > 0))), "real.pgcli.execute_query", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.execute_query", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_query", clause="ensures:1", phase="ensures", span={"end_byte":43427,"end_column":100,"end_line":1125,"start_byte":43332,"start_column":5,"start_line":1125}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryResult, DatabaseError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]:
    """Execute request.sql as one submission over a new connection with the
ConnectionPlan parameters, then close the connection. The text may hold
several statements and is sent as one simple-protocol query. AutoCommit
commits each statement; Manual runs the text in one transaction committed
after the last statement; ReadOnly runs it in one READ ONLY transaction that
is always rolled back. A statement error rolls back an open transaction and is
QueryFailed; a failed commit or rollback is TransactionFailed; failing to open
the connection or authenticate is ConnectionFailed.
result holds the columns and the first max_rows rows, in server order, of the
last statement that produced rows (no columns and no rows when none did);
status is the last statement's command status tag such as "SELECT 2";
affected_rows is its row count (0 when unknown); notices are the server
notices' primary messages in arrival order; elapsed_ms is the monotonic
milliseconds spent executing when timing is true and 0 otherwise."""
    request = _cott_validate_abi(request, QueryRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_3() -> bool:
        _cott_match_value = ((request).connection).ssh
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((True), "real.pgcli.execute_planned_query", "error:3:condition"))
        _cott_contract_condition((False), "real.pgcli.execute_planned_query", "error:3:applicable")
        return False
    if _expected_error is None and (_cott_match_error_3()):
        _expected_error = ClientError_TunnelUnsupported
        _expected_error_span = {"end_byte":44973,"end_column":91,"end_line":1153,"start_byte":44887,"start_column":5,"start_line":1153}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/execute_planned_query.py", "8a59b8adfd0138d67b22e8fe76d19c504cd6e3949e34cbeccdb133d5f1f8c3eb", "execute_planned_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.execute_planned_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.execute_planned_query"
        if _error.span is None:
            _error.span = {"end_byte":45140,"end_column":1,"end_line":1160,"start_byte":43552,"start_column":1,"start_line":1132}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.execute_planned_query", phase="implementation-call", span={"end_byte":45140,"end_column":1,"end_line":1160,"start_byte":43552,"start_column":1,"start_line":1132}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.execute_planned_query", phase="implementation-call", span={"end_byte":45140,"end_column":1,"end_line":1160,"start_byte":43552,"start_column":1,"start_line":1132}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExecutedQuery, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.execute_planned_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ConnectionFailed, ClientError_QueryFailed, ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.execute_planned_query", phase="error", span={"end_byte":45140,"end_column":1,"end_line":1160,"start_byte":43552,"start_column":1,"start_line":1132}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.execute_planned_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", "error:4")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", "error:5")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.execute_planned_query", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            executed = _cott_match_value.value
            return (_cott_contract_condition(((len(((executed).result).rows) <= (request).max_rows)), "real.pgcli.execute_planned_query", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.execute_planned_query", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_planned_query", clause="ensures:1", phase="ensures", span={"end_byte":44801,"end_column":80,"end_line":1150,"start_byte":44726,"start_column":5,"start_line":1150}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            executed = _cott_match_value.value
            return (_cott_contract_condition((((request).timing or ((executed).elapsed_ms == 0))), "real.pgcli.execute_planned_query", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.execute_planned_query", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.execute_planned_query", clause="ensures:2", phase="ensures", span={"end_byte":44881,"end_column":80,"end_line":1151,"start_byte":44806,"start_column":5,"start_line":1151}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExecutedQuery, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]:
    """Execute request.query max_iterations times through execute_planned_query,
waiting interval_ms milliseconds between consecutive executions and not
after the last. The first failing execution stops the watch and its error is
returned unchanged. last_result is the final execution's result."""
    request = _cott_validate_abi(request, WatchRequest, path="$.request")
    if not (_cott_contract_condition((((request).max_iterations > 0)), "real.pgcli.watch_query", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="real.pgcli.watch_query", clause="requires:1", phase="requires", span={"end_byte":45579,"end_column":40,"end_line":1168,"start_byte":45544,"start_column":5,"start_line":1168}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_3() -> bool:
        _cott_match_value = (((request).query).connection).ssh
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((True), "real.pgcli.watch_query", "error:3:condition"))
        _cott_contract_condition((False), "real.pgcli.watch_query", "error:3:applicable")
        return False
    if _expected_error is None and (_cott_match_error_3()):
        _expected_error = ClientError_TunnelUnsupported
        _expected_error_span = {"end_byte":45757,"end_column":97,"end_line":1172,"start_byte":45665,"start_column":5,"start_line":1172}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/watch_query.py", "857d36ea42fc43ae64c73146334b6db4a9bb61311574855e68ce923576430f72", "watch_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.watch_query")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.watch_query"
        if _error.span is None:
            _error.span = {"end_byte":45924,"end_column":1,"end_line":1179,"start_byte":45140,"start_column":1,"start_line":1160}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.watch_query", phase="implementation-call", span={"end_byte":45924,"end_column":1,"end_line":1179,"start_byte":45140,"start_column":1,"start_line":1160}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.watch_query", phase="implementation-call", span={"end_byte":45924,"end_column":1,"end_line":1179,"start_byte":45140,"start_column":1,"start_line":1160}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WatchResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.watch_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ConnectionFailed, ClientError_QueryFailed, ClientError_TransactionFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.watch_query", phase="error", span={"end_byte":45924,"end_column":1,"end_line":1179,"start_byte":45140,"start_column":1,"start_line":1160}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.watch_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.watch_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.watch_query", "error:4")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.watch_query", "error:5")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.watch_query", "error:6")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            watched = _cott_match_value.value
            return (_cott_contract_condition((((watched).executions == (request).max_iterations)), "real.pgcli.watch_query", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.watch_query", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.watch_query", clause="ensures:2", phase="ensures", span={"end_byte":45659,"end_column":79,"end_line":1170,"start_byte":45585,"start_column":5,"start_line":1170}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[WatchResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]:
    """Read a Catalog snapshot through one read-only connection with the
ConnectionPlan parameters using fixed, parameterized catalog queries, then
close the connection. Connection and query failures are CatalogFailed."""
    request = _cott_validate_abi(request, CatalogRefreshRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_5() -> bool:
        _cott_match_value = ((request).connection).ssh
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((True), "real.pgcli.refresh_catalog", "error:5:condition"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "error:5:applicable")
        return False
    if _expected_error is None and (_cott_match_error_5()):
        _expected_error = ClientError_TunnelUnsupported
        _expected_error_span = {"end_byte":46625,"end_column":91,"end_line":1191,"start_byte":46539,"start_column":5,"start_line":1191}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/refresh_catalog.py", "dfb3095ad84d04e8b22ad715a1a91aea4358be6033ec0ec1fd565a3820c24ee4", "refresh_catalog", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.refresh_catalog")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.refresh_catalog"
        if _error.span is None:
            _error.span = {"end_byte":46699,"end_column":1,"end_line":1196,"start_byte":45924,"start_column":1,"start_line":1179}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.refresh_catalog", phase="implementation-call", span={"end_byte":46699,"end_column":1,"end_line":1196,"start_byte":45924,"start_column":1,"start_line":1179}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.refresh_catalog", phase="implementation-call", span={"end_byte":46699,"end_column":1,"end_line":1196,"start_byte":45924,"start_column":1,"start_line":1179}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Catalog, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_CatalogFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.refresh_catalog", phase="error", span={"end_byte":46699,"end_column":1,"end_line":1196,"start_byte":45924,"start_column":1,"start_line":1179}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.refresh_catalog", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_CatalogFailed:
        _cott_contract_condition(True, "real.pgcli.refresh_catalog", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (_cott_contract_condition((((catalog).limit == (request).limit)), "real.pgcli.refresh_catalog", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:1", phase="ensures", span={"end_byte":46317,"end_column":65,"end_line":1186,"start_byte":46257,"start_column":5,"start_line":1186}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (_cott_contract_condition(((len((catalog).relations) <= (request).limit)), "real.pgcli.refresh_catalog", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:2", phase="ensures", span={"end_byte":46390,"end_column":73,"end_line":1187,"start_byte":46322,"start_column":5,"start_line":1187}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (_cott_contract_condition(((len((catalog).routines) <= (request).limit)), "real.pgcli.refresh_catalog", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:3", phase="ensures", span={"end_byte":46462,"end_column":72,"end_line":1188,"start_byte":46395,"start_column":5,"start_line":1188}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog = _cott_match_value.value
            return (_cott_contract_condition(((len((catalog).schemas) <= (request).limit)), "real.pgcli.refresh_catalog", "ensures:4"))
        _cott_contract_condition((False), "real.pgcli.refresh_catalog", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.refresh_catalog", clause="ensures:4", phase="ensures", span={"end_byte":46533,"end_column":71,"end_line":1189,"start_byte":46467,"start_column":5,"start_line":1189}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Catalog, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]:
    """Load request.source into request.table in one transaction over a connection
with the plan's parameters. table is a table name, optionally
schema-qualified with one "."; each part is quoted as an SQL identifier. The
file is UTF-8 text with RFC 4180 quoting and the one-character delimiter; when
header is true the first record is skipped; a field equal to null_text loads
as SQL NULL. Records are loaded with COPY FROM STDIN or parameterized
statements, never by building SQL from field text. More than max_rows data
records, or a missing, unreadable or malformed file, is
ImportFailed(path: request.source, message: a fixed category) and loads
nothing. A connection failure is ConnectionFailed; a server error rolls
everything back and is QueryFailed. On success rows is the number of loaded
records and path is request.source. request.source is read from the file
system the program runs against: the fs fixture root while a Cott scenario
with an fs fixture is active, otherwise the host file system."""
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    request = _cott_validate_abi(request, ImportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len((request).delimiter) != 1)), "real.pgcli.import_delimited", "error:3:condition")):
        _expected_error = ClientError_ImportFailed
        _expected_error_span = {"end_byte":48098,"end_column":67,"end_line":1220,"start_byte":48036,"start_column":5,"start_line":1220}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition((((request).table == "")), "real.pgcli.import_delimited", "error:4:condition")):
        _expected_error = ClientError_ImportFailed
        _expected_error_span = {"end_byte":48158,"end_column":60,"end_line":1221,"start_byte":48103,"start_column":5,"start_line":1221}
        _expected_error_clause = "error:4"
    def _cott_match_error_5() -> bool:
        _cott_match_value = (plan).ssh
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((True), "real.pgcli.import_delimited", "error:5:condition"))
        _cott_contract_condition((False), "real.pgcli.import_delimited", "error:5:applicable")
        return False
    if _expected_error is None and (_cott_match_error_5()):
        _expected_error = ClientError_TunnelUnsupported
        _expected_error_span = {"end_byte":48235,"end_column":77,"end_line":1222,"start_byte":48163,"start_column":5,"start_line":1222}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/import_delimited.py", "ac917a2faf80dc035527526822cf2a3732abd2785277bbfc395256820f2bd6ab", "import_delimited", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.import_delimited")
        _result = _implementation(plan, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.import_delimited"
        if _error.span is None:
            _error.span = {"end_byte":48386,"end_column":1,"end_line":1229,"start_byte":46699,"start_column":1,"start_line":1196}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.import_delimited", phase="implementation-call", span={"end_byte":48386,"end_column":1,"end_line":1229,"start_byte":46699,"start_column":1,"start_line":1196}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.import_delimited", phase="implementation-call", span={"end_byte":48386,"end_column":1,"end_line":1229,"start_byte":46699,"start_column":1,"start_line":1196}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.import_delimited", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ImportFailed, ClientError_ConnectionFailed, ClientError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.import_delimited", phase="error", span={"end_byte":48386,"end_column":1,"end_line":1229,"start_byte":46699,"start_column":1,"start_line":1196}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.import_delimited", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.import_delimited", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_ImportFailed:
        _cott_contract_condition(True, "real.pgcli.import_delimited", "error:6")
    if type(_result) is Err and type(_result.error) is ClientError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.import_delimited", "error:7")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.import_delimited", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            imported = _cott_match_value.value
            return (_cott_contract_condition((((imported).rows <= (request).max_rows)), "real.pgcli.import_delimited", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.import_delimited", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.import_delimited", clause="ensures:1", phase="ensures", span={"end_byte":47963,"end_column":69,"end_line":1217,"start_byte":47899,"start_column":5,"start_line":1217}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            imported = _cott_match_value.value
            return (_cott_contract_condition((((imported).path == (request).source)), "real.pgcli.import_delimited", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.import_delimited", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.import_delimited", clause="ensures:2", phase="ensures", span={"end_byte":48030,"end_column":67,"end_line":1218,"start_byte":47968,"start_column":5,"start_line":1218}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]:
    """Execute request.sql in one READ ONLY transaction over a connection with the
plan's parameters and write its rows to request.target as UTF-8 delimited
text: Csv uses request.delimiter and Tsv uses a tab (request.delimiter is then
ignored). A header record of column names is written when header is true;
fields use RFC 4180 quoting, records end with a line feed, and SQL NULL is an
empty field. The target is replaced only after every row was read, through an
exclusively created same-directory temporary file with mode 0600 that is
flushed, fsynced and renamed over the target, followed by a parent directory
fsync; parent directories are not created and a symlink or non-regular target
is rejected. More than max_rows result rows, or an
I/O failure, is ExportFailed(path: request.target, message: a fixed category)
and leaves the target unchanged. Other formats are
UnsupportedFormat(value: the format's \\T name). A connection failure is
ConnectionFailed and a statement error QueryFailed. On success rows is the
number of data rows written and path is request.target. request.target is
replaced in the file system the program runs against: the fs fixture root
while a Cott scenario with an fs fixture is active, otherwise the host file
system."""
    plan = _cott_validate_abi(plan, ConnectionPlan, path="$.plan")
    request = _cott_validate_abi(request, ExportRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((request).format != TableFormat_Csv()) and ((request).format != TableFormat_Tsv()))), "real.pgcli.export_query", "error:3:condition")):
        _expected_error = ClientError_UnsupportedFormat
        _expected_error_span = {"end_byte":50093,"end_column":119,"end_line":1257,"start_byte":49979,"start_column":5,"start_line":1257}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition(((((request).format == TableFormat_Csv()) and (len((request).delimiter) != 1))), "real.pgcli.export_query", "error:4:condition")):
        _expected_error = ClientError_ExportFailed
        _expected_error_span = {"end_byte":50200,"end_column":107,"end_line":1258,"start_byte":50098,"start_column":5,"start_line":1258}
        _expected_error_clause = "error:4"
    def _cott_match_error_5() -> bool:
        _cott_match_value = (plan).ssh
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((True), "real.pgcli.export_query", "error:5:condition"))
        _cott_contract_condition((False), "real.pgcli.export_query", "error:5:applicable")
        return False
    if _expected_error is None and (_cott_match_error_5()):
        _expected_error = ClientError_TunnelUnsupported
        _expected_error_span = {"end_byte":50277,"end_column":77,"end_line":1259,"start_byte":50205,"start_column":5,"start_line":1259}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/export_query.py", "7f9a0991305711673398fb86616eae4c29c2754f83a324406128e0482bed2c5e", "export_query", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.export_query")
        _result = _implementation(plan, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.export_query"
        if _error.span is None:
            _error.span = {"end_byte":50428,"end_column":1,"end_line":1266,"start_byte":48386,"start_column":1,"start_line":1229}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.export_query", phase="implementation-call", span={"end_byte":50428,"end_column":1,"end_line":1266,"start_byte":48386,"start_column":1,"start_line":1229}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.export_query", phase="implementation-call", span={"end_byte":50428,"end_column":1,"end_line":1266,"start_byte":48386,"start_column":1,"start_line":1229}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.export_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_ExportFailed, ClientError_ConnectionFailed, ClientError_QueryFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.export_query", phase="error", span={"end_byte":50428,"end_column":1,"end_line":1266,"start_byte":48386,"start_column":1,"start_line":1229}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.export_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.export_query", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_ExportFailed:
        _cott_contract_condition(True, "real.pgcli.export_query", "error:6")
    if type(_result) is Err and type(_result.error) is ClientError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.export_query", "error:7")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.export_query", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            exported = _cott_match_value.value
            return (_cott_contract_condition((((exported).rows <= (request).max_rows)), "real.pgcli.export_query", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.export_query", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.export_query", clause="ensures:1", phase="ensures", span={"end_byte":49906,"end_column":69,"end_line":1254,"start_byte":49842,"start_column":5,"start_line":1254}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            exported = _cott_match_value.value
            return (_cott_contract_condition((((exported).path == (request).target)), "real.pgcli.export_query", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.export_query", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.export_query", clause="ensures:2", phase="ensures", span={"end_byte":49973,"end_column":67,"end_line":1255,"start_byte":49911,"start_column":5,"start_line":1255}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]:
    """LISTEN on every channel, each quoted as an SQL identifier, over one
autocommit connection with the ConnectionPlan parameters. Collect
notifications in arrival order until max_notifications have arrived or
timeout_ms monotonic milliseconds have passed since listening began,
whichever comes first; each carries its channel, payload and sender pid.
UNLISTEN and close the connection on every path. Connection and listening
failures are NotificationFailed."""
    request = _cott_validate_abi(request, NotificationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len((request).channels) == 0)), "real.pgcli.receive_notifications", "error:2:condition")):
        _expected_error = ClientError_NotificationFailed
        _expected_error_span = {"end_byte":51189,"end_column":72,"end_line":1279,"start_byte":51122,"start_column":5,"start_line":1279}
        _expected_error_clause = "error:2"
    def _cott_match_error_3() -> bool:
        _cott_match_value = ((request).connection).ssh
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((True), "real.pgcli.receive_notifications", "error:3:condition"))
        _cott_contract_condition((False), "real.pgcli.receive_notifications", "error:3:applicable")
        return False
    if _expected_error is None and (_cott_match_error_3()):
        _expected_error = ClientError_TunnelUnsupported
        _expected_error_span = {"end_byte":51280,"end_column":91,"end_line":1280,"start_byte":51194,"start_column":5,"start_line":1280}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/receive_notifications.py", "dd61e32ae2036e13bc7872ebbe1a4ea8dcf4952ea3c0654f98c87b91178ad303", "receive_notifications", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.receive_notifications")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.receive_notifications"
        if _error.span is None:
            _error.span = {"end_byte":51359,"end_column":1,"end_line":1285,"start_byte":50428,"start_column":1,"start_line":1266}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.receive_notifications", phase="implementation-call", span={"end_byte":51359,"end_column":1,"end_line":1285,"start_byte":50428,"start_column":1,"start_line":1266}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.receive_notifications", phase="implementation-call", span={"end_byte":51359,"end_column":1,"end_line":1285,"start_byte":50428,"start_column":1,"start_line":1266}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[Notification], ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.receive_notifications", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_NotificationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.receive_notifications", phase="error", span={"end_byte":51359,"end_column":1,"end_line":1285,"start_byte":50428,"start_column":1,"start_line":1266}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.receive_notifications", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.receive_notifications", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_NotificationFailed:
        _cott_contract_condition(True, "real.pgcli.receive_notifications", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            notifications = _cott_match_value.value
            return (_cott_contract_condition(((len(notifications) <= (request).max_notifications)), "real.pgcli.receive_notifications", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.receive_notifications", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.receive_notifications", clause="ensures:1", phase="ensures", span={"end_byte":51116,"end_column":87,"end_line":1277,"start_byte":51034,"start_column":5,"start_line":1277}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[Notification], ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    """Write buffer.text as UTF-8 to temporary_path, start the editor on it and wait
for it to exit, then read the file back. editor is split into words at
whitespace (no shell) and temporary_path is appended as the last argument; the
editor inherits the terminal. A zero exit status returns the file's text
without one trailing line feed, with the cursor at its end and
buffer.multiline kept. temporary_path is removed on every path. A missing
editor executable, a nonzero exit or signal, and I/O or decoding failures
are EditorFailed with a fixed category message."""
    request = _cott_validate_abi(request, EditorRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((request).editor == "")), "real.pgcli.edit_in_editor", "error:3:condition")):
        _expected_error = ClientError_EditorFailed
        _expected_error_span = {"end_byte":52256,"end_column":61,"end_line":1300,"start_byte":52200,"start_column":5,"start_line":1300}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/edit_in_editor.py", "be9c6b9292525a0accc7dd3dc12f4c24f9daaeab734ab4af8effb9da787e20bb", "edit_in_editor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.edit_in_editor")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.edit_in_editor"
        if _error.span is None:
            _error.span = {"end_byte":52330,"end_column":1,"end_line":1305,"start_byte":51359,"start_column":1,"start_line":1285}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.edit_in_editor", phase="implementation-call", span={"end_byte":52330,"end_column":1,"end_line":1305,"start_byte":51359,"start_column":1,"start_line":1285}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.edit_in_editor", phase="implementation-call", span={"end_byte":52330,"end_column":1,"end_line":1305,"start_byte":51359,"start_column":1,"start_line":1285}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[InputBuffer, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.edit_in_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_EditorFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.edit_in_editor", phase="error", span={"end_byte":52330,"end_column":1,"end_line":1305,"start_byte":51359,"start_column":1,"start_line":1285}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.edit_in_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.edit_in_editor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_EditorFailed:
        _cott_contract_condition(True, "real.pgcli.edit_in_editor", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            edited = _cott_match_value.value
            return (_cott_contract_condition((((edited).cursor == len((edited).text))), "real.pgcli.edit_in_editor", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.edit_in_editor", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_in_editor", clause="ensures:1", phase="ensures", span={"end_byte":52116,"end_column":66,"end_line":1297,"start_byte":52055,"start_column":5,"start_line":1297}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            edited = _cott_match_value.value
            return (_cott_contract_condition((((edited).multiline == ((request).buffer).multiline)), "real.pgcli.edit_in_editor", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.edit_in_editor", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.edit_in_editor", clause="ensures:2", phase="ensures", span={"end_byte":52194,"end_column":78,"end_line":1298,"start_byte":52121,"start_column":5,"start_line":1298}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[InputBuffer, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def page_output(request: PagerRequest) -> Result[Unit, ClientError]:
    """Show text on the terminal. When enabled is false, or text has at most
terminal_height lines, write text and one line feed to standard output.
Otherwise start the pager command, split into words at whitespace (no shell),
with text and one line feed on its standard input, and wait for it to exit;
a pager that exits with status 0 after closing its input early succeeds.
A pager that cannot start or exits nonzero, and a failed write to standard
output, are PagerFailed with a fixed category message."""
    request = _cott_validate_abi(request, PagerRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/page_output.py", "abb6d93b046b79c8f73c473836760a885f9af44bf469a4eb0c4609a5ecce4de6", "page_output", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.page_output")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.page_output"
        if _error.span is None:
            _error.span = {"end_byte":53137,"end_column":1,"end_line":1323,"start_byte":52330,"start_column":1,"start_line":1305}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.page_output", phase="implementation-call", span={"end_byte":53137,"end_column":1,"end_line":1323,"start_byte":52330,"start_column":1,"start_line":1305}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.page_output", phase="implementation-call", span={"end_byte":53137,"end_column":1,"end_line":1323,"start_byte":52330,"start_column":1,"start_line":1305}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.page_output", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_PagerFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.page_output", phase="error", span={"end_byte":53137,"end_column":1,"end_line":1323,"start_byte":52330,"start_column":1,"start_line":1305}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.page_output", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.page_output", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_PagerFailed:
        _cott_contract_condition(True, "real.pgcli.page_output", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            paged = _cott_match_value.value
            return (_cott_contract_condition(((paged == UNIT)), "real.pgcli.page_output", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.page_output", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.page_output", clause="ensures:1", phase="ensures", span={"end_byte":53063,"end_column":44,"end_line":1317,"start_byte":53024,"start_column":5,"start_line":1317}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]:
    """Execute one parsed backslash command against the session state and return
the resulting buffer, options and catalog with the text to show in output
("" for none). quit is true only for Quit. Unless stated otherwise buffer,
options and catalog are returned unchanged, output never contains the
connection password, and a facade error is returned unchanged with no later
step. "A table" below means the output of format_query(FormatRequest(query,
options.format, 80, 0, options.max_rows)) for the named columns, rows in
source order. A pattern matches psql-style: "" matches everything, "*" any
sequence of characters, "?" one character, anything else itself
(case-sensitive); a pattern containing "." is matched against "schema.name",
otherwise the name.

Session: Quit -> output "". Help -> one line per supported command word with a
short description. SqlHelp(topic) -> the URL
"https://www.postgresql.org/docs/current/sql-" + topic lower-cased without
spaces + ".html", or "https://www.postgresql.org/docs/current/sql-commands.html"
for "". SetFormat(format) -> options.format = format; "Output format: " + its
\\T name. Timing -> toggle options.timing; "Timing is on." or "Timing is off.".
Expanded -> options.format becomes Vertical, or Aligned when it was Vertical;
"Expanded display is on." or "Expanded display is off.". SetPager(enabled) ->
options.pager = enabled; "Pager usage is on." or "Pager usage is off.".
ConnectionInfo -> 'You are connected to database "D" as user "U" on host "H"
at port "P".' from options.connection.settings. Echo(text) and
QueryOutputEcho(text) -> text. PrintBuffer -> buffer.text, or
"Query buffer is empty.". ResetBuffer -> empty buffer text with cursor 0 and
the same multiline; "Query buffer reset (cleared).".

Catalog argument (no database access): Describe("") -> a table Schema, Name,
Type of every relation; Describe(pattern) -> a table Schema, Relation, Column
of each column of every matching relation. ListTables (kinds table and
partitioned table), ListViews (view), ListMaterializedViews
(materialized view) and ListSequences (sequence) -> a table Schema, Name, Type
of matching relations. ListSchemas -> Name; ListFunctions -> Schema, Name,
Result data type, Argument data types; ListRoles, ListExtensions and
ListDatabases -> Name.

Server queries: ListDomains (Schema, Name, Type), ListForeignTables (Schema,
Name, Server), ListTextSearchConfigurations (Schema, Name), ListDataTypes
(Schema, Name), ListTablespaces (Name, Owner, Location),
ListDefaultPrivileges (Owner, Schema, Type, Privileges), ListIndexes (Schema,
Name, Table) and ListPrivileges (Schema, Name, Privileges) call
execute_planned_query(QueryRequest(options.connection, a fixed catalog query
containing no user text, options.max_rows, ReadOnly, false)) and show a table
of the result rows whose Name (Schema for ListDefaultPrivileges) matches the
pattern. ShowFunction(pattern) fetches non-system function definitions the
same way and shows those whose name matches, separated by blank lines, or
'No function matches "pattern".'.

Connect(database): candidate = options.connection with settings.database =
database; connect(candidate), whose error becomes ConnectionFailed with a
fixed message; then refresh_catalog(CatalogRefreshRequest(candidate, false,
options.catalog_limit)); then options.connection = candidate, catalog = the
refreshed catalog, output 'You are now connected to database "D" as user "U".'
from the receipt. RefreshCatalog: the same refresh with options.connection;
catalog replaced; "Catalog refreshed: N relations, M routines.".

ExecuteBuffer and ExecuteExpanded: plan_query(buffer), then
execute_planned_query(QueryRequest(options.connection, plan.sql,
options.max_rows, options.transaction, options.timing)), then format_query
with options.format (Vertical for ExecuteExpanded); output is the rendered
text, then the status when nonempty, then "Time: N ms" when options.timing,
joined by line feeds; the buffer becomes empty with the same multiline.
EditBuffer: edit_in_editor(EditorRequest(buffer, $VISUAL, else $EDITOR, else
"vi", a new unique file in the system temporary directory)); buffer = its
result; output "". ReadFile(path) and ReadRelativeFile(path) (relative to the
current directory): buffer = the file's UTF-8 text with the cursor at its end
and the same multiline; a read failure is ImportFailed(path, a fixed
category). WriteBuffer(path): replace path with buffer.text as UTF-8; a
failure is ExportFailed(path, a fixed category); 'Wrote query buffer to
"path".'. These ReadFile, ReadRelativeFile and WriteBuffer paths are read
from or replaced in the file system the program runs against: the fs fixture
root while a Cott scenario with an fs fixture is active, otherwise the host
file system. Copy(table, path, from_file): when from_file,
import_delimited(options.connection, ImportRequest(table, path, ",", true, "",
1000000)); otherwise export_query(options.connection, ExportRequest(
"SELECT * FROM " + table with each dot-separated part quoted as an SQL
identifier, path, Csv, ",", true, 1000000)); output "COPY " + rows.

History(pattern): with options.history Nothing, "History is disabled.";
otherwise load_history(policy) and one line per entry whose sql contains
pattern ("" matches all): its 1-based stored position, two spaces, the sql,
lines joined by line feeds.

Favorites: with options.favorites Nothing every favorite command is
FavoriteFailed(name: ""); otherwise load_favorites(store) first; a missing
favorite is FavoriteFailed(name: name). NamedQuery(name, arguments): the
favorite's sql with "$k" replaced by the k-th argument for k from
arguments.len down to 1, executed like ExecuteBuffer while the buffer stays
unchanged. SaveNamedQuery(name, sql) and Favorite(name) with sql =
buffer.text: replace the sql of the favorite with that name, keeping its
position and tags, or append Favorite(name, sql, no tags), then
save_favorites; 'Saved favorite "name".'. DeleteNamedQuery(name) and
DeleteFavorite(name): remove it, then save_favorites; 'Deleted favorite
"name".'. PrintNamedQuery(name): "name: sql". ListFavorites(pattern): a table
Name, Query of favorites whose name matches.

Unknown(source): InvalidCommand(source: source)."""
    invocation = _cott_validate_abi(invocation, CommandInvocation, path="$.invocation")
    options = _cott_validate_abi(options, SessionOptions, path="$.options")
    catalog = _cott_validate_abi(catalog, Catalog, path="$.catalog")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_3() -> bool:
        _cott_match_value = (invocation).command
        if type(_cott_match_value) is MetaCommand_Unknown and True:
            return (_cott_contract_condition((True), "real.pgcli.run_meta_command", "error:3:condition"))
        _cott_contract_condition((False), "real.pgcli.run_meta_command", "error:3:applicable")
        return False
    if _expected_error is None and (_cott_match_error_3()):
        _expected_error = ClientError_InvalidCommand
        _expected_error_span = {"end_byte":60209,"end_column":92,"end_line":1431,"start_byte":60122,"start_column":5,"start_line":1431}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run_meta_command.py", "25ecf5bbc70a8fa7fd9f16f2047c53975a91282df7bec937f8018bb566b6a6ba", "run_meta_command", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run_meta_command")
        _result = _implementation(invocation, options, catalog)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run_meta_command"
        if _error.span is None:
            _error.span = {"end_byte":60695,"end_column":1,"end_line":1446,"start_byte":53137,"start_column":1,"start_line":1323}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.run_meta_command", phase="implementation-call", span={"end_byte":60695,"end_column":1,"end_line":1446,"start_byte":53137,"start_column":1,"start_line":1323}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run_meta_command", phase="implementation-call", span={"end_byte":60695,"end_column":1,"end_line":1446,"start_byte":53137,"start_column":1,"start_line":1323}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CommandResult, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.run_meta_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidSql, ClientError_ConnectionFailed, ClientError_TunnelUnsupported, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_ImportFailed, ClientError_ExportFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.run_meta_command", phase="error", span={"end_byte":60695,"end_column":1,"end_line":1446,"start_byte":53137,"start_column":1,"start_line":1323}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.run_meta_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidSql:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:4")
    if type(_result) is Err and type(_result.error) is ClientError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:5")
    if type(_result) is Err and type(_result.error) is ClientError_TunnelUnsupported:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:6")
    if type(_result) is Err and type(_result.error) is ClientError_CatalogFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:7")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:8")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:9")
    if type(_result) is Err and type(_result.error) is ClientError_ImportFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:10")
    if type(_result) is Err and type(_result.error) is ClientError_ExportFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:11")
    if type(_result) is Err and type(_result.error) is ClientError_HistoryFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:12")
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:13")
    if type(_result) is Err and type(_result.error) is ClientError_EditorFailed:
        _cott_contract_condition(True, "real.pgcli.run_meta_command", "error:14")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            step = _cott_match_value.value
            return (_cott_contract_condition((((step).quit == ((invocation).command == MetaCommand_Quit()))), "real.pgcli.run_meta_command", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.run_meta_command", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_meta_command", clause="ensures:1", phase="ensures", span={"end_byte":59995,"end_column":85,"end_line":1428,"start_byte":59915,"start_column":5,"start_line":1428}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            step = _cott_match_value.value
            return (_cott_contract_condition((((((step).options).history == (options).history) and (((step).options).favorites == (options).favorites))), "real.pgcli.run_meta_command", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.run_meta_command", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_meta_command", clause="ensures:2", phase="ensures", span={"end_byte":60116,"end_column":121,"end_line":1429,"start_byte":60000,"start_column":5,"start_line":1429}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CommandResult, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_interactive(request: InteractiveRequest) -> Result[SessionReport, ClientError]:
    """Run one client session over request.options and report its submissions.
Setup, stopping at the first error, which is returned unchanged: when
options.history is Some(policy) call load_history(policy) and keep the
entries. In Interactive mode, and in ExecuteOnce mode when initial_sql is a
backslash command, call refresh_catalog(CatalogRefreshRequest(
options.connection, false, options.catalog_limit)); otherwise the catalog is
empty (every list empty, refreshed_at_ms 0, limit 0).

A submission is a text. A text whose first non-whitespace character is "\\",
or that equals quit or exit after trimming, is a command:
run_meta_command(CommandInvocation(parse_meta_command(text), the pending
buffer), options, catalog). Other text is SQL: run_meta_command(
CommandInvocation(ExecuteBuffer, InputBuffer(text, its length,
options.multiline)), options, catalog). A successful submission replaces the
session's buffer, options and catalog with the command result and, when its
output is nonempty, shows it with page_output(PagerRequest(output, $PAGER or
"less -SRXF", options.pager, the terminal height or 24)). After every SQL
submission, when history is enabled, set entries = remember_history(policy,
entries, HistoryEntry(sql: the text, executed_at_ms: wall-clock Unix
milliseconds at submission, database: options.connection.settings.database,
success: whether it succeeded)) and call save_history(policy, entries).

ExecuteOnce: submit initial_sql once without reading the terminal. Its error
is returned unchanged; otherwise the report is SessionReport(1, 0).

Interactive: submit a nonempty initial_sql first, then read standard input one
line at a time until end of input or a Quit command. Print the prompt
"pgcli> ", or "....> " while the pending buffer is nonempty, to standard output
only when standard input is a terminal. A command line is submitted at once
with the pending buffer. Any other line is added to the pending buffer with
edit_multiline, preceded by a line feed when the buffer is nonempty; a blank
pending buffer is discarded; when options.multiline is true and
plan_query(pending buffer) succeeds with requires_terminator, reading
continues; otherwise the pending text is submitted and the buffer cleared. At
end of input a nonblank pending buffer is submitted. A submission error, or a
PagerFailed while showing output, writes one fixed category line for the
ClientError variant to standard error, counts as a failure and the session
continues. A standard input or output failure ends the session with
TerminalFailed, and a save_history failure ends it with HistoryFailed."""
    request = _cott_validate_abi(request, InteractiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run_interactive.py", "7e1a5459d85142d4831677c19234ad02a4cb212ae5b0fb8a82b78a1420e16922", "run_interactive", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run_interactive")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run_interactive"
        if _error.span is None:
            _error.span = {"end_byte":64280,"end_column":1,"end_line":1508,"start_byte":60695,"start_column":1,"start_line":1446}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.run_interactive", phase="implementation-call", span={"end_byte":64280,"end_column":1,"end_line":1508,"start_byte":60695,"start_column":1,"start_line":1446}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run_interactive", phase="implementation-call", span={"end_byte":64280,"end_column":1,"end_line":1508,"start_byte":60695,"start_column":1,"start_line":1446}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[SessionReport, ClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.run_interactive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_ConnectionFailed, ClientError_TunnelUnsupported, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_ImportFailed, ClientError_ExportFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_TerminalFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.run_interactive", phase="error", span={"end_byte":64280,"end_column":1,"end_line":1508,"start_byte":60695,"start_column":1,"start_line":1446}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.run_interactive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.run_interactive", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ClientError_InvalidCommand:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:2")
    if type(_result) is Err and type(_result.error) is ClientError_InvalidSql:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:3")
    if type(_result) is Err and type(_result.error) is ClientError_ConnectionFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:4")
    if type(_result) is Err and type(_result.error) is ClientError_TunnelUnsupported:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:5")
    if type(_result) is Err and type(_result.error) is ClientError_CatalogFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:6")
    if type(_result) is Err and type(_result.error) is ClientError_QueryFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:7")
    if type(_result) is Err and type(_result.error) is ClientError_TransactionFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:8")
    if type(_result) is Err and type(_result.error) is ClientError_ImportFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:9")
    if type(_result) is Err and type(_result.error) is ClientError_ExportFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:10")
    if type(_result) is Err and type(_result.error) is ClientError_HistoryFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:11")
    if type(_result) is Err and type(_result.error) is ClientError_FavoriteFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:12")
    if type(_result) is Err and type(_result.error) is ClientError_EditorFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:13")
    if type(_result) is Err and type(_result.error) is ClientError_PagerFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:14")
    if type(_result) is Err and type(_result.error) is ClientError_TerminalFailed:
        _cott_contract_condition(True, "real.pgcli.run_interactive", "error:15")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            report = _cott_match_value.value
            return (_cott_contract_condition(((((request).mode != SessionMode_ExecuteOnce()) or (((report).submissions == 1) and ((report).failures == 0)))), "real.pgcli.run_interactive", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.run_interactive", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.run_interactive", clause="ensures:1", phase="ensures", span={"end_byte":63685,"end_column":129,"end_line":1489,"start_byte":63561,"start_column":5,"start_line":1489}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[SessionReport, ClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """The pgcli-cott command-line entry point; arguments excludes the program name.
Call parse_arguments(arguments, EnvironmentInputs read from PGHOST, PGPORT,
PGUSER, PGPASSWORD and PGDATABASE, "" when unset).
Help: write the usage text to standard output and exit 0 without connecting.
InvalidArguments: write the usage text and the error message to standard
error and exit 2.
Session(connection, mode, initial_sql): call
resolve_connection_plan(connection, Nothing); on error write a fixed category
message to standard error and exit 2. Otherwise call
run_interactive(InteractiveRequest(SessionOptions(connection: the plan,
catalog_limit: 1000, max_rows: 1000, history: Nothing, favorites: Nothing,
format: Aligned, timing: false, pager: false, multiline: false,
transaction: AutoCommit), initial_sql, mode)). Ok(report) exits 0 when
report.failures is 0 and 1 otherwise; Err writes a fixed category message for
its variant to standard error and exits 1. An interrupt (Ctrl-C) exits 130.
The usage text lists [DSN], -h/--host, -p/--port, -U/--username,
-d/--dbname, -c/--command and --help. run adds no connection, execution or
argument behavior of its own and never prints a password."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/run.py", "413e22e371808b905c28c0536a353689427294a98721a372b005cd1fbf9872f5", "run", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.run"
        if _error.span is None:
            _error.span = {"end_byte":65693,"end_column":1,"end_line":1532,"start_byte":64280,"start_column":1,"start_line":1508}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.run", phase="implementation-call", span={"end_byte":65693,"end_column":1,"end_line":1532,"start_byte":64280,"start_column":1,"start_line":1508}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.pgcli.run", phase="return", span={"end_byte":65693,"end_column":1,"end_line":1532,"start_byte":64280,"start_column":1,"start_line":1508}, expected="Never", actual=repr(_result))

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "CliCommand", "CliCommand_Help", "CliCommand_Session", "ClientCertificate", "ClientError", "ClientError_CatalogFailed", "ClientError_ConnectionFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidArguments", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_TunnelUnsupported", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionReceipt", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetPager", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SQL_KEYWORDS", "SessionMode", "SessionMode_ExecuteOnce", "SessionMode_Interactive", "SessionOptions", "SessionReport", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsMode", "TlsMode_Allow", "TlsMode_Default", "TlsMode_Disable", "TlsMode_Prefer", "TlsMode_Require", "TlsMode_VerifyCa", "TlsMode_VerifyFull", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Failed", "TransactionStatus_Idle", "TransferResult", "WatchRequest", "WatchResult", "begin_transaction", "commit_transaction", "complete_catalog_sql", "complete_sql", "connect", "edit_in_editor", "edit_multiline", "execute_planned_query", "execute_query", "export_query", "format_query", "highlight_sql", "import_delimited", "load_favorites", "load_history", "page_output", "parse_arguments", "parse_dsn", "parse_meta_command", "plan_query", "prompt_policy", "receive_notifications", "recognize_backslash", "refresh_catalog", "remember_history", "render_query", "resolve_connection", "resolve_connection_plan", "resolve_credential", "resolve_profile", "rollback_transaction", "run", "run_interactive", "run_meta_command", "save_favorites", "save_history", "watch_query"]
