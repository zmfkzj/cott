from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.harlequin.core_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, CliError, CliError_ConflictingConnectionInputs, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, CliOptions, Configuration, ConfigurationError, ConfigurationError_Invalid, ConfigurationError_Missing, ConfigurationError_ProfileDuplicate, ConfigurationError_ProfileMissing, Connection, ConnectionError, ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed, ConnectionError_Failed, ConnectionError_InvalidEndpoint, ConnectionProfile, ConnectionRequest, DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, FileError, FileError_InvalidEncoding, FileError_NotFound, FileError_PermissionDenied, FileError_TransferFailed, FileLocation, FileLocation_Local, FileLocation_S3, FileReference, IdeSession, LoadedFile, QueryBatch, QueryHistory, QueryHistoryEntry, QueryResult, QueryTab, SavedFile, SessionError, SessionError_HistoryCapacityInvalid, SessionError_TabMissing, Setting, SqlClientError, SqlClientError_Cancelled, SqlClientError_EmptySql, SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql, Transaction, TypedRow

def adapter_descriptors() -> CottList[AdapterDescriptor]:
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/adapter_descriptors.py", "1322b3abb1b348de668e27f3e148091c040554da25fb4dde46f86876ca7f1ae2", "adapter_descriptors", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.adapter_descriptors")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.adapter_descriptors"
        if _error.span is None:
            _error.span = {"end_byte":3304,"end_column":1,"end_line":170,"start_byte":3205,"start_column":1,"start_line":165}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.adapter_descriptors", phase="implementation-call", span={"end_byte":3304,"end_column":1,"end_line":170,"start_byte":3205,"start_column":1,"start_line":165}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.adapter_descriptors", phase="implementation-call", span={"end_byte":3304,"end_column":1,"end_line":170,"start_byte":3205,"start_column":1,"start_line":165}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[AdapterDescriptor], path="$.return")
    if not ((len(_result) == 11)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.adapter_descriptors", clause="ensures:0", phase="ensures", span={"end_byte":3286,"end_column":29,"end_line":166,"start_byte":3262,"start_column":5,"start_line":166}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[AdapterDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]:
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/parse_cli.py", "9c81f5d88d7afeb6d0a8692a706c5c8cf3c511a13de1a8a3864e8f572dc5c6e8", "parse_cli", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.parse_cli")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.parse_cli"
        if _error.span is None:
            _error.span = {"end_byte":3623,"end_column":1,"end_line":180,"start_byte":3304,"start_column":1,"start_line":170}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.parse_cli", phase="implementation-call", span={"end_byte":3623,"end_column":1,"end_line":180,"start_byte":3304,"start_column":1,"start_line":170}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.parse_cli", phase="implementation-call", span={"end_byte":3623,"end_column":1,"end_line":180,"start_byte":3304,"start_column":1,"start_line":170}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CliOptions, CliError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.parse_cli", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CliError_UnknownOption, CliError_MissingOptionValue, CliError_InvalidAdapter, CliError_ConflictingConnectionInputs,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.parse_cli", phase="error", span={"end_byte":3623,"end_column":1,"end_line":180,"start_byte":3304,"start_column":1,"start_line":170}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.parse_cli", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return (((options).source_argument_count <= len(arguments)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.parse_cli", clause="ensures:0", phase="ensures", span={"end_byte":3452,"end_column":81,"end_line":171,"start_byte":3376,"start_column":5,"start_line":171}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CliOptions, CliError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_configuration(path: Path) -> Result[Configuration, ConfigurationError]:
    """Use tomllib; cast each dict/list to dict[str, object]/list[object] before use."""
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/load_configuration.py", "0134f317fb5f4b82352258f47296c979bfb69e3d612125790c6ff8b4d66a8d90", "load_configuration", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.load_configuration")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.load_configuration"
        if _error.span is None:
            _error.span = {"end_byte":4031,"end_column":1,"end_line":193,"start_byte":3623,"start_column":1,"start_line":180}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.load_configuration", phase="implementation-call", span={"end_byte":4031,"end_column":1,"end_line":193,"start_byte":3623,"start_column":1,"start_line":180}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.load_configuration", phase="implementation-call", span={"end_byte":4031,"end_column":1,"end_line":193,"start_byte":3623,"start_column":1,"start_line":180}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Configuration, ConfigurationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.load_configuration", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigurationError_Missing, ConfigurationError_Invalid, ConfigurationError_ProfileDuplicate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.load_configuration", phase="error", span={"end_byte":4031,"end_column":1,"end_line":193,"start_byte":3623,"start_column":1,"start_line":180}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.load_configuration", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            configuration = _cott_match_value.value
            return ((len((configuration).profiles) <= 100000))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_configuration", clause="ensures:1", phase="ensures", span={"end_byte":3883,"end_column":77,"end_line":185,"start_byte":3811,"start_column":5,"start_line":185}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Configuration, ConfigurationError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]:
    """Use isinstance, not match, for each Option; select the named or default profile."""
    configuration = _cott_validate_abi(configuration, Configuration, path="$.configuration")
    options = _cott_validate_abi(options, CliOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/resolve_profile.py", "dcbde0fafacacc1677db65870ffdf2ea83acaf79a61c66cc2710a205b25e79fc", "resolve_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.resolve_profile")
        _result = _implementation(configuration, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.resolve_profile"
        if _error.span is None:
            _error.span = {"end_byte":4389,"end_column":1,"end_line":207,"start_byte":4031,"start_column":1,"start_line":193}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.resolve_profile", phase="implementation-call", span={"end_byte":4389,"end_column":1,"end_line":207,"start_byte":4031,"start_column":1,"start_line":193}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.resolve_profile", phase="implementation-call", span={"end_byte":4389,"end_column":1,"end_line":207,"start_byte":4031,"start_column":1,"start_line":193}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionRequest, ConfigurationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigurationError_ProfileMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.resolve_profile", phase="error", span={"end_byte":4389,"end_column":1,"end_line":207,"start_byte":4031,"start_column":1,"start_line":193}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return ((len((request).endpoint) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.resolve_profile", clause="ensures:1", phase="ensures", span={"end_byte":4326,"end_column":59,"end_line":201,"start_byte":4272,"start_column":5,"start_line":201}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionRequest, ConfigurationError], path="$.return", validator=_cott_validate_abi)
    return _result

def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    request = _cott_validate_abi(request, ConnectionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/connect.py", "9c13e8966104e3c144a9cdbb8fc4634bc9d14b18f61c911bda1a50524074bd8c", "connect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.connect")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.connect"
        if _error.span is None:
            _error.span = {"end_byte":4750,"end_column":1,"end_line":217,"start_byte":4389,"start_column":1,"start_line":207}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.connect", phase="implementation-call", span={"end_byte":4750,"end_column":1,"end_line":217,"start_byte":4389,"start_column":1,"start_line":207}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.connect", phase="implementation-call", span={"end_byte":4750,"end_column":1,"end_line":217,"start_byte":4389,"start_column":1,"start_line":207}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Connection, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_AdapterUnavailable, ConnectionError_InvalidEndpoint, ConnectionError_AuthenticationFailed, ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.connect", phase="error", span={"end_byte":4750,"end_column":1,"end_line":217,"start_byte":4389,"start_column":1,"start_line":207}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (((connection).adapter == (request).adapter))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:0", phase="ensures", span={"end_byte":4542,"end_column":75,"end_line":208,"start_byte":4472,"start_column":5,"start_line":208}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Connection, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def disconnect(connection: Connection) -> Unit:
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/disconnect.py", "2ef4a4ca619a34f6d1fe6601688cff400fcca1a31b25cfea084650b727a7b1e7", "disconnect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.disconnect")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.disconnect"
        if _error.span is None:
            _error.span = {"end_byte":4835,"end_column":1,"end_line":220,"start_byte":4750,"start_column":1,"start_line":217}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.disconnect", phase="implementation-call", span={"end_byte":4835,"end_column":1,"end_line":220,"start_byte":4750,"start_column":1,"start_line":217}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.disconnect", phase="implementation-call", span={"end_byte":4835,"end_column":1,"end_line":220,"start_byte":4750,"start_column":1,"start_line":217}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=_cott_validate_abi)
    return _result

def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]:
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/begin_transaction.py", "3a11e0c1920c3cd6ccc4f2faf1f560d0aca753b5ede7ef2fd4625e3d7d3c4bb9", "begin_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.begin_transaction")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.begin_transaction"
        if _error.span is None:
            _error.span = {"end_byte":5076,"end_column":1,"end_line":227,"start_byte":4835,"start_column":1,"start_line":220}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.begin_transaction", phase="implementation-call", span={"end_byte":5076,"end_column":1,"end_line":227,"start_byte":4835,"start_column":1,"start_line":220}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.begin_transaction", phase="implementation-call", span={"end_byte":5076,"end_column":1,"end_line":227,"start_byte":4835,"start_column":1,"start_line":220}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.begin_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.begin_transaction", phase="error", span={"end_byte":5076,"end_column":1,"end_line":227,"start_byte":4835,"start_column":1,"start_line":220}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.begin_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            transaction = _cott_match_value.value
            return (((transaction).connection_id == (connection).id))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.begin_transaction", clause="ensures:0", phase="ensures", span={"end_byte":5001,"end_column":81,"end_line":221,"start_byte":4925,"start_column":5,"start_line":221}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    transaction = _cott_validate_abi(transaction, Transaction, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/commit_transaction.py", "a27812815794bc5a701134b7257018a2fd8a5ac318b4141a36014ed9cc26ff4b", "commit_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.commit_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":5324,"end_column":1,"end_line":234,"start_byte":5076,"start_column":1,"start_line":227}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.commit_transaction", phase="implementation-call", span={"end_byte":5324,"end_column":1,"end_line":234,"start_byte":5076,"start_column":1,"start_line":227}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.commit_transaction", phase="implementation-call", span={"end_byte":5324,"end_column":1,"end_line":234,"start_byte":5076,"start_column":1,"start_line":227}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.commit_transaction", phase="error", span={"end_byte":5324,"end_column":1,"end_line":234,"start_byte":5076,"start_column":1,"start_line":227}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (((updated).connection_id == (transaction).connection_id))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.commit_transaction", clause="ensures:0", phase="ensures", span={"end_byte":5249,"end_column":85,"end_line":228,"start_byte":5169,"start_column":5,"start_line":228}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def rollback_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    transaction = _cott_validate_abi(transaction, Transaction, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/rollback_transaction.py", "4a3de60fb81423412ba11cbda7f650bfa35a470e0dbcf14ed6eec9b2e0702d58", "rollback_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.rollback_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":5574,"end_column":1,"end_line":241,"start_byte":5324,"start_column":1,"start_line":234}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.rollback_transaction", phase="implementation-call", span={"end_byte":5574,"end_column":1,"end_line":241,"start_byte":5324,"start_column":1,"start_line":234}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.rollback_transaction", phase="implementation-call", span={"end_byte":5574,"end_column":1,"end_line":241,"start_byte":5324,"start_column":1,"start_line":234}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.rollback_transaction", phase="error", span={"end_byte":5574,"end_column":1,"end_line":241,"start_byte":5324,"start_column":1,"start_line":234}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (((updated).connection_id == (transaction).connection_id))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.rollback_transaction", clause="ensures:0", phase="ensures", span={"end_byte":5499,"end_column":85,"end_line":235,"start_byte":5419,"start_column":5,"start_line":235}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def open_query_tab(id: str, title: str, source: str) -> QueryTab:
    id = _cott_validate_abi(id, str, path="$.id")
    title = _cott_validate_abi(title, str, path="$.title")
    source = _cott_validate_abi(source, str, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/open_query_tab.py", "7dac985426221ee11b5a2ef7ad2316df98eecb61e13dd6a856c6e532be02d756", "open_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.open_query_tab")
        _result = _implementation(id, title, source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.open_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":5655,"end_column":1,"end_line":244,"start_byte":5574,"start_column":1,"start_line":241}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.open_query_tab", phase="implementation-call", span={"end_byte":5655,"end_column":1,"end_line":244,"start_byte":5574,"start_column":1,"start_line":241}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.open_query_tab", phase="implementation-call", span={"end_byte":5655,"end_column":1,"end_line":244,"start_byte":5574,"start_column":1,"start_line":241}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryTab, path="$.return")
    _result = _cott_wrap_async_protocol(_result, QueryTab, path="$.return", validator=_cott_validate_abi)
    return _result

def edit_query_tab(tab: QueryTab, source: str, cursor: U64) -> QueryTab:
    tab = _cott_validate_abi(tab, QueryTab, path="$.tab")
    source = _cott_validate_abi(source, str, path="$.source")
    cursor = _cott_validate_abi(cursor, U64, path="$.cursor")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/edit_query_tab.py", "b623f5f6e50230be128fc4b72f876c772c256b8399e26a0d65341f6b087eed7b", "edit_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.edit_query_tab")
        _result = _implementation(tab, source, cursor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.edit_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":5791,"end_column":1,"end_line":249,"start_byte":5655,"start_column":1,"start_line":244}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.edit_query_tab", phase="implementation-call", span={"end_byte":5791,"end_column":1,"end_line":249,"start_byte":5655,"start_column":1,"start_line":244}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.edit_query_tab", phase="implementation-call", span={"end_byte":5791,"end_column":1,"end_line":249,"start_byte":5655,"start_column":1,"start_line":244}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryTab, path="$.return")
    if not (((_result).cursor <= len((_result).source))):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":5773,"end_column":47,"end_line":245,"start_byte":5731,"start_column":5,"start_line":245}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryTab, path="$.return", validator=_cott_validate_abi)
    return _result

def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory:
    history = _cott_validate_abi(history, QueryHistory, path="$.history")
    entry = _cott_validate_abi(entry, QueryHistoryEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/append_query_history.py", "470b3f9ef7a186b0c3b5c6f0d0665d7d9521860bf6a6f1935d1a8945295e6697", "append_query_history", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.append_query_history")
        _result = _implementation(history, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.append_query_history"
        if _error.span is None:
            _error.span = {"end_byte":5949,"end_column":1,"end_line":254,"start_byte":5791,"start_column":1,"start_line":249}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.append_query_history", phase="implementation-call", span={"end_byte":5949,"end_column":1,"end_line":254,"start_byte":5791,"start_column":1,"start_line":249}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.append_query_history", phase="implementation-call", span={"end_byte":5949,"end_column":1,"end_line":254,"start_byte":5791,"start_column":1,"start_line":249}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryHistory, path="$.return")
    if not ((len((_result).entries) <= (history).capacity)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.append_query_history", clause="ensures:0", phase="ensures", span={"end_byte":5931,"end_column":51,"end_line":250,"start_byte":5885,"start_column":5,"start_line":250}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryHistory, path="$.return", validator=_cott_validate_abi)
    return _result

def start_session(connection: Connection, history_capacity: U64) -> IdeSession:
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    history_capacity = _cott_validate_abi(history_capacity, U64, path="$.history_capacity")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/start_session.py", "f9a8920dd34bfb77ea951efb8c42f058b6d0f388a9313a013acbd25ea56e4fba", "start_session", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.start_session")
        _result = _implementation(connection, history_capacity)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.start_session"
        if _error.span is None:
            _error.span = {"end_byte":6222,"end_column":1,"end_line":262,"start_byte":5949,"start_column":1,"start_line":254}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.start_session", phase="implementation-call", span={"end_byte":6222,"end_column":1,"end_line":262,"start_byte":5949,"start_column":1,"start_line":254}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.start_session", phase="implementation-call", span={"end_byte":6222,"end_column":1,"end_line":262,"start_byte":5949,"start_column":1,"start_line":254}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, IdeSession, path="$.return")
    if not (((_result).connection == connection)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:0", phase="ensures", span={"end_byte":6071,"end_column":44,"end_line":255,"start_byte":6032,"start_column":5,"start_line":255}, expected="true", actual="false")
    if not ((len((_result).tabs) == 0)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:1", phase="ensures", span={"end_byte":6104,"end_column":33,"end_line":256,"start_byte":6076,"start_column":5,"start_line":256}, expected="true", actual="false")
    if not ((len(((_result).history).entries) == 0)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:2", phase="ensures", span={"end_byte":6148,"end_column":44,"end_line":257,"start_byte":6109,"start_column":5,"start_line":257}, expected="true", actual="false")
    if not ((((_result).history).capacity == history_capacity)):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:3", phase="ensures", span={"end_byte":6204,"end_column":56,"end_line":258,"start_byte":6153,"start_column":5,"start_line":258}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=_cott_validate_abi)
    return _result

def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession:
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab = _cott_validate_abi(tab, QueryTab, path="$.tab")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/add_query_tab.py", "2f396a1b651639f2aedc8f72a2e54666281142f765b33d9e8c2f936e482db66f", "add_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.add_query_tab")
        _result = _implementation(session, tab)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.add_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":6359,"end_column":1,"end_line":267,"start_byte":6222,"start_column":1,"start_line":262}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.add_query_tab", phase="implementation-call", span={"end_byte":6359,"end_column":1,"end_line":267,"start_byte":6222,"start_column":1,"start_line":262}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.add_query_tab", phase="implementation-call", span={"end_byte":6359,"end_column":1,"end_line":267,"start_byte":6222,"start_column":1,"start_line":262}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, IdeSession, path="$.return")
    if not ((len((_result).tabs) == (len((session).tabs) + 1))):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.add_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":6341,"end_column":52,"end_line":263,"start_byte":6294,"start_column":5,"start_line":263}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=_cott_validate_abi)
    return _result

def activate_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab_id = _cott_validate_abi(tab_id, str, path="$.tab_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/activate_query_tab.py", "52ed8211d5dcee22f91d36f562917a9b1bc0d176076a55b28657dce2fd6d1874", "activate_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.activate_query_tab")
        _result = _implementation(session, tab_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.activate_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":6575,"end_column":1,"end_line":274,"start_byte":6359,"start_column":1,"start_line":267}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.activate_query_tab", phase="implementation-call", span={"end_byte":6575,"end_column":1,"end_line":274,"start_byte":6359,"start_column":1,"start_line":267}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.activate_query_tab", phase="implementation-call", span={"end_byte":6575,"end_column":1,"end_line":274,"start_byte":6359,"start_column":1,"start_line":267}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IdeSession, SessionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.activate_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SessionError_TabMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.activate_query_tab", phase="error", span={"end_byte":6575,"end_column":1,"end_line":274,"start_byte":6359,"start_column":1,"start_line":267}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.activate_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return ((len((updated).tabs) == len((session).tabs)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.activate_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":6522,"end_column":71,"end_line":268,"start_byte":6456,"start_column":5,"start_line":268}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[IdeSession, SessionError], path="$.return", validator=_cott_validate_abi)
    return _result

def close_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    """Use isinstance checks, not match, for active_tab_id."""
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab_id = _cott_validate_abi(tab_id, str, path="$.tab_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/close_query_tab.py", "dc526ebe2692c6e22547311c908eff02ad20633507af292783548fda90f12fcb", "close_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.close_query_tab")
        _result = _implementation(session, tab_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.close_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":6865,"end_column":1,"end_line":285,"start_byte":6575,"start_column":1,"start_line":274}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.close_query_tab", phase="implementation-call", span={"end_byte":6865,"end_column":1,"end_line":285,"start_byte":6575,"start_column":1,"start_line":274}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.close_query_tab", phase="implementation-call", span={"end_byte":6865,"end_column":1,"end_line":285,"start_byte":6575,"start_column":1,"start_line":274}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IdeSession, SessionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.close_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SessionError_TabMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.close_query_tab", phase="error", span={"end_byte":6865,"end_column":1,"end_line":285,"start_byte":6575,"start_column":1,"start_line":274}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.close_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return ((len((updated).tabs) < len((session).tabs)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.close_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":6812,"end_column":70,"end_line":279,"start_byte":6747,"start_column":5,"start_line":279}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[IdeSession, SessionError], path="$.return", validator=_cott_validate_abi)
    return _result

def split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/split_statements.py", "6948ff3d8868b1fb975ec1ff651704e05da6ee593e20cbaec6488f554d177c0f", "split_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.split_statements")
        _result = _implementation(sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.split_statements"
        if _error.span is None:
            _error.span = {"end_byte":7082,"end_column":1,"end_line":293,"start_byte":6865,"start_column":1,"start_line":285}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":7082,"end_column":1,"end_line":293,"start_byte":6865,"start_column":1,"start_line":285}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":7082,"end_column":1,"end_line":293,"start_byte":6865,"start_column":1,"start_line":285}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.split_statements", phase="error", span={"end_byte":7082,"end_column":1,"end_line":293,"start_byte":6865,"start_column":1,"start_line":285}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            statements = _cott_match_value.value
            return ((len(statements) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.split_statements", clause="ensures:0", phase="ensures", span={"end_byte":6988,"end_column":56,"end_line":286,"start_byte":6937,"start_column":5,"start_line":286}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_sql.py", "b87f01c8890f1bf41d47cdad3e09ec78badbd0fc0d6f107c90003913422eeaa9", "execute_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_sql")
        _result = _implementation(database, sql, read_only)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_sql"
        if _error.span is None:
            _error.span = {"end_byte":7507,"end_column":1,"end_line":308,"start_byte":7082,"start_column":1,"start_line":293}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":7507,"end_column":1,"end_line":308,"start_byte":7082,"start_column":1,"start_line":293}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":7507,"end_column":1,"end_line":308,"start_byte":7082,"start_column":1,"start_line":293}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[QueryResult], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_sql", phase="error", span={"end_byte":7507,"end_column":1,"end_line":308,"start_byte":7082,"start_column":1,"start_line":293}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            results = _cott_match_value.value
            return ((len(results) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_sql", clause="ensures:0", phase="ensures", span={"end_byte":7260,"end_column":50,"end_line":298,"start_byte":7215,"start_column":5,"start_line":298}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[QueryResult], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]:
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    maximum_rows = _cott_validate_abi(maximum_rows, U32, path="$.maximum_rows")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_statements.py", "cf4d85f23c73f38c65ffc883384af8d82ba3e438d9cf1fa4c3ff815e3d33be34", "execute_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_statements")
        _result = _implementation(connection, sql, maximum_rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_statements"
        if _error.span is None:
            _error.span = {"end_byte":8005,"end_column":1,"end_line":324,"start_byte":7507,"start_column":1,"start_line":308}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_statements", phase="implementation-call", span={"end_byte":8005,"end_column":1,"end_line":324,"start_byte":7507,"start_column":1,"start_line":308}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_statements", phase="implementation-call", span={"end_byte":8005,"end_column":1,"end_line":324,"start_byte":7507,"start_column":1,"start_line":308}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryBatch, SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_ExecutionFailed, SqlClientError_ResultLimitExceeded, SqlClientError_Cancelled,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_statements", phase="error", span={"end_byte":8005,"end_column":1,"end_line":324,"start_byte":7507,"start_column":1,"start_line":308}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            batch = _cott_match_value.value
            return ((len((batch).statements) == len((batch).results)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_statements", clause="ensures:0", phase="ensures", span={"end_byte":7709,"end_column":74,"end_line":313,"start_byte":7640,"start_column":5,"start_line":313}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryBatch, SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]:
    """Set sdk: Any = boto3; client: Any = sdk.client("s3"); decode Body to source: str."""
    reference = _cott_validate_abi(reference, FileReference, path="$.reference")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/load_query_file.py", "004c2783cf538bb7ecf9c2fccaddad2fedf2a662657315bedb490efdee89b73b", "load_query_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.load_query_file")
        _result = _implementation(reference)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.load_query_file"
        if _error.span is None:
            _error.span = {"end_byte":8427,"end_column":1,"end_line":338,"start_byte":8005,"start_column":1,"start_line":324}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.load_query_file", phase="implementation-call", span={"end_byte":8427,"end_column":1,"end_line":338,"start_byte":8005,"start_column":1,"start_line":324}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.load_query_file", phase="implementation-call", span={"end_byte":8427,"end_column":1,"end_line":338,"start_byte":8005,"start_column":1,"start_line":324}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LoadedFile, FileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.load_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileError_NotFound, FileError_PermissionDenied, FileError_InvalidEncoding, FileError_TransferFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.load_query_file", phase="error", span={"end_byte":8427,"end_column":1,"end_line":338,"start_byte":8005,"start_column":1,"start_line":324}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.load_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (((loaded).reference == reference))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:1", phase="ensures", span={"end_byte":8253,"end_column":63,"end_line":329,"start_byte":8195,"start_column":5,"start_line":329}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LoadedFile, FileError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]:
    reference = _cott_validate_abi(reference, FileReference, path="$.reference")
    source = _cott_validate_abi(source, str, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/save_query_file.py", "7706c3644dffb45684ac3f516f0bb374a1856376bcc21275b4631a81b109f2f4", "save_query_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.save_query_file")
        _result = _implementation(reference, source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.save_query_file"
        if _error.span is None:
            _error.span = {"end_byte":8688,"end_column":1,"end_line":346,"start_byte":8427,"start_column":1,"start_line":338}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.save_query_file", phase="implementation-call", span={"end_byte":8688,"end_column":1,"end_line":346,"start_byte":8427,"start_column":1,"start_line":338}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.save_query_file", phase="implementation-call", span={"end_byte":8688,"end_column":1,"end_line":346,"start_byte":8427,"start_column":1,"start_line":338}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[SavedFile, FileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.save_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileError_PermissionDenied, FileError_TransferFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.save_query_file", phase="error", span={"end_byte":8688,"end_column":1,"end_line":346,"start_byte":8427,"start_column":1,"start_line":338}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.save_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (((saved).reference == reference))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.save_query_file", clause="ensures:0", phase="ensures", span={"end_byte":8578,"end_column":61,"end_line":339,"start_byte":8522,"start_column":5,"start_line":339}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[SavedFile, FileError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """Parse/connect; read SQL at sql> until .quit/EOF; execute and print tab-separated results."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/run.py", "1c307ded536b93271f11ee7ea5cd2d33b6e541c1e5e39e9fdfc7a0e2710dd5df", "run", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.run"
        if _error.span is None:
            _error.span = {"end_byte":8939,"end_column":1,"end_line":352,"start_byte":8688,"start_column":1,"start_line":346}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.run", phase="implementation-call", span={"end_byte":8939,"end_column":1,"end_line":352,"start_byte":8688,"start_column":1,"start_line":346}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.harlequin.core.run", phase="return", span={"end_byte":8939,"end_column":1,"end_line":352,"start_byte":8688,"start_column":1,"start_line":346}, expected="Never", actual=repr(_result))

__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_HistoryCapacityInvalid", "SessionError_TabMissing", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TypedRow", "activate_query_tab", "adapter_descriptors", "add_query_tab", "append_query_history", "begin_transaction", "close_query_tab", "commit_transaction", "connect", "disconnect", "edit_query_tab", "execute_sql", "execute_statements", "load_configuration", "load_query_file", "open_query_tab", "parse_cli", "resolve_profile", "rollback_transaction", "run", "save_query_file", "split_statements", "start_session"]
