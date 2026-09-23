from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.core_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, CliError, CliError_ConflictingConnectionInputs, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, CliOptions, Configuration, ConfigurationError, ConfigurationError_Invalid, ConfigurationError_Missing, ConfigurationError_ProfileDuplicate, ConfigurationError_ProfileMissing, Connection, ConnectionError, ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed, ConnectionError_Failed, ConnectionError_InvalidEndpoint, ConnectionProfile, ConnectionRequest, DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, FileError, FileError_InvalidEncoding, FileError_NotFound, FileError_PermissionDenied, FileError_TransferFailed, FileLocation, FileLocation_Local, FileLocation_S3, FileReference, IdeSession, LoadedFile, QueryBatch, QueryHistory, QueryHistoryEntry, QueryResult, QueryTab, SavedFile, SessionError, SessionError_HistoryCapacityInvalid, SessionError_TabMissing, SessionHandle, Setting, SqlClientError, SqlClientError_Cancelled, SqlClientError_EmptySql, SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql, Transaction, TransactionLease, TypedRow

def adapter_descriptors() -> CottList[AdapterDescriptor]:
    """Return these eleven descriptors in this exact order. Fields below are
kind | display_name | uri_schemes | supports_transactions | supports_catalog |
supports_files. Scheme names are discovery labels without ":"; they do not
replace the endpoint formats documented by AdapterKind. Capabilities describe
this client's adapter policy, not every feature of the underlying database.
DuckDb | DuckDB | ["duckdb"] | true | true | true
Sqlite | SQLite | ["sqlite"] | true | true | true
PostgreSql | PostgreSQL | ["postgres", "postgresql"] | true | true | false
MySql | MySQL | ["mysql"] | true | true | false
Odbc | ODBC | ["odbc"] | true | true | false
BigQuery | BigQuery | ["bigquery"] | false | true | false
Trino | Trino | ["trino"] | false | true | false
Databricks | Databricks | ["databricks"] | false | true | true
Adbc | ADBC | ["adbc"] | true | true | false
Cassandra | Cassandra | ["cassandra"] | false | true | false
NebulaGraph | NebulaGraph | ["nebula"] | false | true | false"""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/adapter_descriptors.py", "e2d23e7afaf87d6ed448c2cbaaa85108d8aa7738740bd2f0a819bc226aebac7c", "adapter_descriptors", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.adapter_descriptors")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.adapter_descriptors"
        if _error.span is None:
            _error.span = {"end_byte":9211,"end_column":1,"end_line":265,"start_byte":8043,"start_column":1,"start_line":241}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.adapter_descriptors", phase="implementation-call", span={"end_byte":9211,"end_column":1,"end_line":265,"start_byte":8043,"start_column":1,"start_line":241}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.adapter_descriptors", phase="implementation-call", span={"end_byte":9211,"end_column":1,"end_line":265,"start_byte":8043,"start_column":1,"start_line":241}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[AdapterDescriptor], path="$.return")
    if not (_cott_contract_condition(((len(_result) == 11)), "real.harlequin.core.adapter_descriptors", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.adapter_descriptors", clause="ensures:1", phase="ensures", span={"end_byte":9193,"end_column":29,"end_line":261,"start_byte":9169,"start_column":5,"start_line":261}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[AdapterDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]:
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/parse_cli.py", "d51f67591593f7fab59cfa7578b344ca4869a3161c097a435f94451a1cbe15f3", "parse_cli", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.parse_cli")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.parse_cli"
        if _error.span is None:
            _error.span = {"end_byte":9530,"end_column":1,"end_line":275,"start_byte":9211,"start_column":1,"start_line":265}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.parse_cli", phase="implementation-call", span={"end_byte":9530,"end_column":1,"end_line":275,"start_byte":9211,"start_column":1,"start_line":265}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.parse_cli", phase="implementation-call", span={"end_byte":9530,"end_column":1,"end_line":275,"start_byte":9211,"start_column":1,"start_line":265}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CliOptions, CliError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.parse_cli", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CliError_UnknownOption, CliError_MissingOptionValue, CliError_InvalidAdapter, CliError_ConflictingConnectionInputs,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.parse_cli", phase="error", span={"end_byte":9530,"end_column":1,"end_line":275,"start_byte":9211,"start_column":1,"start_line":265}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.parse_cli", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is CliError_UnknownOption:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:1")
    if type(_result) is Err and type(_result.error) is CliError_MissingOptionValue:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:2")
    if type(_result) is Err and type(_result.error) is CliError_InvalidAdapter:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:3")
    if type(_result) is Err and type(_result.error) is CliError_ConflictingConnectionInputs:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:4")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return (_cott_contract_condition((((options).source_argument_count <= len(arguments))), "real.harlequin.core.parse_cli", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.core.parse_cli", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.parse_cli", clause="ensures:0", phase="ensures", span={"end_byte":9359,"end_column":81,"end_line":266,"start_byte":9283,"start_column":5,"start_line":266}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CliOptions, CliError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_configuration(path: Path) -> Result[Configuration, ConfigurationError]:
    """Use tomllib; cast each dict/list to dict[str, object]/list[object] before use."""
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/load_configuration.py", "a6a5ba73c8541518e2fee8dedf2244aef7e38e21fd769931e300c56193bb2b6a", "load_configuration", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.load_configuration")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.load_configuration"
        if _error.span is None:
            _error.span = {"end_byte":9938,"end_column":1,"end_line":288,"start_byte":9530,"start_column":1,"start_line":275}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.load_configuration", phase="implementation-call", span={"end_byte":9938,"end_column":1,"end_line":288,"start_byte":9530,"start_column":1,"start_line":275}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.load_configuration", phase="implementation-call", span={"end_byte":9938,"end_column":1,"end_line":288,"start_byte":9530,"start_column":1,"start_line":275}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Configuration, ConfigurationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.load_configuration", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigurationError_Missing, ConfigurationError_Invalid, ConfigurationError_ProfileDuplicate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.load_configuration", phase="error", span={"end_byte":9938,"end_column":1,"end_line":288,"start_byte":9530,"start_column":1,"start_line":275}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.load_configuration", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigurationError_Missing:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", "error:2")
    if type(_result) is Err and type(_result.error) is ConfigurationError_Invalid:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", "error:3")
    if type(_result) is Err and type(_result.error) is ConfigurationError_ProfileDuplicate:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            configuration = _cott_match_value.value
            return (_cott_contract_condition(((len((configuration).profiles) <= 100000)), "real.harlequin.core.load_configuration", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.load_configuration", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_configuration", clause="ensures:1", phase="ensures", span={"end_byte":9790,"end_column":77,"end_line":280,"start_byte":9718,"start_column":5,"start_line":280}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/harlequin/core/resolve_profile.py", "4cdce0bd3953fc1b3accc253bd1423f7f70fa28fc775426eb020936ccd17d43b", "resolve_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.resolve_profile")
        _result = _implementation(configuration, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.resolve_profile"
        if _error.span is None:
            _error.span = {"end_byte":10296,"end_column":1,"end_line":302,"start_byte":9938,"start_column":1,"start_line":288}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.resolve_profile", phase="implementation-call", span={"end_byte":10296,"end_column":1,"end_line":302,"start_byte":9938,"start_column":1,"start_line":288}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.resolve_profile", phase="implementation-call", span={"end_byte":10296,"end_column":1,"end_line":302,"start_byte":9938,"start_column":1,"start_line":288}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionRequest, ConfigurationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigurationError_ProfileMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.resolve_profile", phase="error", span={"end_byte":10296,"end_column":1,"end_line":302,"start_byte":9938,"start_column":1,"start_line":288}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.resolve_profile", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigurationError_ProfileMissing:
        _cott_contract_condition(True, "real.harlequin.core.resolve_profile", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition(((len((request).endpoint) > 0)), "real.harlequin.core.resolve_profile", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.resolve_profile", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.resolve_profile", clause="ensures:1", phase="ensures", span={"end_byte":10233,"end_column":59,"end_line":296,"start_byte":10179,"start_column":5,"start_line":296}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionRequest, ConfigurationError], path="$.return", validator=_cott_validate_abi)
    return _result

def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    """Open and retain a real SDK session using AdapterKind's endpoint formats.
Return a fresh UUID hex id and SessionHandle with the exact documented payload.
The returned driver stays open; no probe-and-close success is allowed.
Register actual resource cleanup callbacks with ExitStack as resources are
acquired, and transfer that stack into the session only on complete success.
A failed construction closes every acquired resource before returning an error.
Do not use SDK connection context managers that implicitly commit on exit.

Reject duplicate settings names. For JSON endpoint adapters, settings override
known top-level fields: string fields use literal text, integers use decimal,
booleans use true/false, and object/list fields use JSON. Validate the resulting
object against AdapterKind's fields and retain its canonical JSON as endpoint.
PostgreSQL settings are libpq string parameters merged with make_conninfo.
ODBC settings are connection-string keyword/value overrides: keyword names
contain only ASCII letters/digits/underscore/space; brace-quote values and
double embedded closing braces, never concatenate unescaped input.
SQLite settings permit only timeout (positive finite seconds); DuckDB settings
permit only threads and memory_limit as documented driver config strings.
Unknown/invalid settings are InvalidEndpoint, not silently ignored.

SQLite uses sqlite3.Connection, isolation_level=None and check_same_thread=False;
its session lock serializes operations. :memory: remains alive in this connection.
A file endpoint opens an existing file URI with mode=ro or mode=rw according
to read_only, never silently creates a missing file. Apply query_only when
read_only is true. DuckDB retains DuckDBPyConnection; pass read_only for files,
and use an in-memory connection for :memory:.
PostgreSQL retains psycopg.Connection; MySQL retains pymysql.Connection;
ODBC retains pyodbc.Connection; ADBC retains adbc_driver_manager.dbapi.Connection.
These four use manual-commit mode for their lifetime; outside an explicit
transaction execute_statements commits each successful statement. ADBC driver
failure to support manual commit is an error, not an ignored warning.
BigQuery retains google.cloud.bigquery.Client, Trino retains its DBAPI
Connection, and Databricks retains databricks.sql.Connection.
Cassandra retains the real Session and registers Session.shutdown before
Cluster.shutdown in cleanup execution order. NebulaGraph retains its Session
and registers Session.release before ConnectionPool.close.
Every other SDK registers its real connection/client close callback.

Missing driver capabilities return AdapterUnavailable; malformed endpoint or
settings return InvalidEndpoint with an empty redacted endpoint payload.
Recognizable authentication failures return AuthenticationFailed with a fixed
nonsecret message; other actual connection failures return Failed similarly.
Never return a descriptor without a usable SDK driver or retain a hidden owner."""
    request = _cott_validate_abi(request, ConnectionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/connect.py", "4f7b589b417f8bb1c17073dcb62d16a7d5293de48bd914b01d9506aa454c2253", "connect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.connect")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.connect"
        if _error.span is None:
            _error.span = {"end_byte":14004,"end_column":1,"end_line":360,"start_byte":10296,"start_column":1,"start_line":302}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.connect", phase="implementation-call", span={"end_byte":14004,"end_column":1,"end_line":360,"start_byte":10296,"start_column":1,"start_line":302}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.connect", phase="implementation-call", span={"end_byte":14004,"end_column":1,"end_line":360,"start_byte":10296,"start_column":1,"start_line":302}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Connection, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_AdapterUnavailable, ConnectionError_InvalidEndpoint, ConnectionError_AuthenticationFailed, ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.connect", phase="error", span={"end_byte":14004,"end_column":1,"end_line":360,"start_byte":10296,"start_column":1,"start_line":302}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.connect", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_AdapterUnavailable:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:4")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidEndpoint:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:5")
    if type(_result) is Err and type(_result.error) is ConnectionError_AuthenticationFailed:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:6")
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:7")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (_cott_contract_condition((((connection).adapter == (request).adapter)), "real.harlequin.core.connect", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:1", phase="ensures", span={"end_byte":13623,"end_column":75,"end_line":349,"start_byte":13553,"start_column":5,"start_line":349}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (_cott_contract_condition(((len((connection).id) > 0)), "real.harlequin.core.connect", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:2", phase="ensures", span={"end_byte":13682,"end_column":59,"end_line":350,"start_byte":13628,"start_column":5,"start_line":350}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (_cott_contract_condition((((connection).read_only == (request).read_only)), "real.harlequin.core.connect", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:3", phase="ensures", span={"end_byte":13761,"end_column":79,"end_line":351,"start_byte":13687,"start_column":5,"start_line":351}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Connection, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def disconnect(connection: Connection) -> Result[Unit, ConnectionError]:
    """Validate SessionHandle and lock it. If already closed, return Unit successfully.
Otherwise invalidate the active lease and mark closed before cleanup, so no
stale handle can regain authority even if the SDK reports a close failure.
Roll back an outstanding supported transaction on this same driver, then close
the ExitStack so every registered callback is attempted. Do not commit or
reopen any connection. Cleanup failure returns Failed with a fixed message;
success returns Unit. No resource is transferred to a hidden registry."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/disconnect.py", "23897145cd22249aa2c07fb3259acf0b2f885b2ded9668eb969bb3c979b663ed", "disconnect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.disconnect")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.disconnect"
        if _error.span is None:
            _error.span = {"end_byte":14792,"end_column":1,"end_line":377,"start_byte":14004,"start_column":1,"start_line":360}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.disconnect", phase="implementation-call", span={"end_byte":14792,"end_column":1,"end_line":377,"start_byte":14004,"start_column":1,"start_line":360}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.disconnect", phase="implementation-call", span={"end_byte":14792,"end_column":1,"end_line":377,"start_byte":14004,"start_column":1,"start_line":360}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.disconnect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.disconnect", phase="error", span={"end_byte":14792,"end_column":1,"end_line":377,"start_byte":14004,"start_column":1,"start_line":360}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.disconnect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.disconnect", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.disconnect", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            closed = _cott_match_value.value
            return (_cott_contract_condition(((closed == UNIT)), "real.harlequin.core.disconnect", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.disconnect", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.disconnect", clause="ensures:1", phase="ensures", span={"end_byte":14702,"end_column":46,"end_line":371,"start_byte":14661,"start_column":5,"start_line":371}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]:
    """Borrow and lock the live connection. Reject closed/malformed handles and an
already active lease. Transactions are supported for Sqlite, DuckDb, PostgreSql,
MySql, Odbc and Adbc, matching adapter_descriptors; other kinds return Failed
as an explicit unsupported capability, not a pretend active transaction.
Start a real transaction on the existing SDK driver: SQLite/DuckDB execute
BEGIN, PostgreSQL executes BEGIN (READ ONLY when requested), and MySQL uses
begin(). ODBC/ADBC are already in manual-commit mode; their physical transaction
may start lazily with the first statement. Do not open, close or roll back a
new connection as a substitute. Install a fresh TransactionLease object as the
session's active transaction and return Transaction(connection=connection,
lease=that lease, active=true). If starting fails, return Failed and leave no
active lease. The caller retains ownership of the connection."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/begin_transaction.py", "079a6feb209f743205632d433ab7e98ac0c39044e36f518199a00572132b8d5c", "begin_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.begin_transaction")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.begin_transaction"
        if _error.span is None:
            _error.span = {"end_byte":16064,"end_column":1,"end_line":400,"start_byte":14792,"start_column":1,"start_line":377}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.begin_transaction", phase="implementation-call", span={"end_byte":16064,"end_column":1,"end_line":400,"start_byte":14792,"start_column":1,"start_line":377}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.begin_transaction", phase="implementation-call", span={"end_byte":16064,"end_column":1,"end_line":400,"start_byte":14792,"start_column":1,"start_line":377}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.begin_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.begin_transaction", phase="error", span={"end_byte":16064,"end_column":1,"end_line":400,"start_byte":14792,"start_column":1,"start_line":377}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.begin_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.begin_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.begin_transaction", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            transaction = _cott_match_value.value
            return (_cott_contract_condition((((transaction).connection == connection)), "real.harlequin.core.begin_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.begin_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.begin_transaction", clause="ensures:1", phase="ensures", span={"end_byte":15932,"end_column":75,"end_line":393,"start_byte":15862,"start_column":5,"start_line":393}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            transaction = _cott_match_value.value
            return (_cott_contract_condition(((transaction).active), "real.harlequin.core.begin_transaction", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.begin_transaction", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.begin_transaction", clause="ensures:2", phase="ensures", span={"end_byte":15989,"end_column":57,"end_line":394,"start_byte":15937,"start_column":5,"start_line":394}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    """Borrow transaction.connection and acquire its session lock. Require active=true,
an open matching SessionHandle, and exact lease object identity with its active
transaction. Reject a stale, already-finished, disconnected or wrong-owner
lease as Failed without touching a different session.
Call the actual existing SDK driver's commit. Never reconnect by id/endpoint.
On success clear the active lease and return the same connection and lease
with active=false. On a driver failure, clear the lease, mark the session closed,
attempt rollback and every registered cleanup callback, and return Failed with
a fixed nonsecret message; do not leave an ambiguously reusable transaction."""
    transaction = _cott_validate_abi(transaction, Transaction, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/commit_transaction.py", "3798b3e176358e1136c8080450a07cc1dfb774d2afc0f0a809dba8f9eb8bfdc7", "commit_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.commit_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":17097,"end_column":1,"end_line":420,"start_byte":16064,"start_column":1,"start_line":400}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.commit_transaction", phase="implementation-call", span={"end_byte":17097,"end_column":1,"end_line":420,"start_byte":16064,"start_column":1,"start_line":400}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.commit_transaction", phase="implementation-call", span={"end_byte":17097,"end_column":1,"end_line":420,"start_byte":16064,"start_column":1,"start_line":400}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.commit_transaction", phase="error", span={"end_byte":17097,"end_column":1,"end_line":420,"start_byte":16064,"start_column":1,"start_line":400}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.commit_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.commit_transaction", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).connection == (transaction).connection)), "real.harlequin.core.commit_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.commit_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.commit_transaction", clause="ensures:1", phase="ensures", span={"end_byte":16969,"end_column":79,"end_line":413,"start_byte":16895,"start_column":5,"start_line":413}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((not (updated).active)), "real.harlequin.core.commit_transaction", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.commit_transaction", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.commit_transaction", clause="ensures:2", phase="ensures", span={"end_byte":17022,"end_column":53,"end_line":414,"start_byte":16974,"start_column":5,"start_line":414}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def rollback_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    """Apply the same ownership and live-lease requirements as commit_transaction,
but call the existing SDK driver's rollback. Success clears the active lease
and returns the same connection and lease with active=false. Double completion,
stale leases and disconnected sessions are Failed, never successful no-ops.
A driver failure clears the lease, marks the session closed, attempts all
cleanup callbacks and returns Failed with a fixed nonsecret message."""
    transaction = _cott_validate_abi(transaction, Transaction, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/rollback_transaction.py", "d056b86db94a2caf329c04ed089701943988b1d52d71171a1c066ff045b1b4bb", "rollback_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.rollback_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":17891,"end_column":1,"end_line":437,"start_byte":17097,"start_column":1,"start_line":420}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.rollback_transaction", phase="implementation-call", span={"end_byte":17891,"end_column":1,"end_line":437,"start_byte":17097,"start_column":1,"start_line":420}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.rollback_transaction", phase="implementation-call", span={"end_byte":17891,"end_column":1,"end_line":437,"start_byte":17097,"start_column":1,"start_line":420}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.rollback_transaction", phase="error", span={"end_byte":17891,"end_column":1,"end_line":437,"start_byte":17097,"start_column":1,"start_line":420}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.rollback_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.rollback_transaction", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).connection == (transaction).connection)), "real.harlequin.core.rollback_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.rollback_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.rollback_transaction", clause="ensures:1", phase="ensures", span={"end_byte":17763,"end_column":79,"end_line":430,"start_byte":17689,"start_column":5,"start_line":430}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((not (updated).active)), "real.harlequin.core.rollback_transaction", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.rollback_transaction", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.rollback_transaction", clause="ensures:2", phase="ensures", span={"end_byte":17816,"end_column":53,"end_line":431,"start_byte":17768,"start_column":5,"start_line":431}, expected="true", actual="false")
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
            _error.span = {"end_byte":17972,"end_column":1,"end_line":440,"start_byte":17891,"start_column":1,"start_line":437}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.open_query_tab", phase="implementation-call", span={"end_byte":17972,"end_column":1,"end_line":440,"start_byte":17891,"start_column":1,"start_line":437}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.open_query_tab", phase="implementation-call", span={"end_byte":17972,"end_column":1,"end_line":440,"start_byte":17891,"start_column":1,"start_line":437}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryTab, path="$.return")
    _result = _cott_wrap_async_protocol(_result, QueryTab, path="$.return", validator=_cott_validate_abi)
    return _result

def edit_query_tab(tab: QueryTab, source: str, cursor: U64) -> QueryTab:
    tab = _cott_validate_abi(tab, QueryTab, path="$.tab")
    source = _cott_validate_abi(source, str, path="$.source")
    cursor = _cott_validate_abi(cursor, U64, path="$.cursor")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/edit_query_tab.py", "e5b62daa5f95a8e47462ccc1f8c0903bcd7e0ebbb70faa8c6cb9e09b986f834c", "edit_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.edit_query_tab")
        _result = _implementation(tab, source, cursor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.edit_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":18108,"end_column":1,"end_line":445,"start_byte":17972,"start_column":1,"start_line":440}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.edit_query_tab", phase="implementation-call", span={"end_byte":18108,"end_column":1,"end_line":445,"start_byte":17972,"start_column":1,"start_line":440}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.edit_query_tab", phase="implementation-call", span={"end_byte":18108,"end_column":1,"end_line":445,"start_byte":17972,"start_column":1,"start_line":440}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryTab, path="$.return")
    if not (_cott_contract_condition((((_result).cursor <= len((_result).source))), "real.harlequin.core.edit_query_tab", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":18090,"end_column":47,"end_line":441,"start_byte":18048,"start_column":5,"start_line":441}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryTab, path="$.return", validator=_cott_validate_abi)
    return _result

def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory:
    history = _cott_validate_abi(history, QueryHistory, path="$.history")
    entry = _cott_validate_abi(entry, QueryHistoryEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/append_query_history.py", "9b501ae81b9a2185532501e537bb5f63f7242ffba990f105245c066f32fbcd1f", "append_query_history", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.append_query_history")
        _result = _implementation(history, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.append_query_history"
        if _error.span is None:
            _error.span = {"end_byte":18266,"end_column":1,"end_line":450,"start_byte":18108,"start_column":1,"start_line":445}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.append_query_history", phase="implementation-call", span={"end_byte":18266,"end_column":1,"end_line":450,"start_byte":18108,"start_column":1,"start_line":445}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.append_query_history", phase="implementation-call", span={"end_byte":18266,"end_column":1,"end_line":450,"start_byte":18108,"start_column":1,"start_line":445}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryHistory, path="$.return")
    if not (_cott_contract_condition(((len((_result).entries) <= (history).capacity)), "real.harlequin.core.append_query_history", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.append_query_history", clause="ensures:0", phase="ensures", span={"end_byte":18248,"end_column":51,"end_line":446,"start_byte":18202,"start_column":5,"start_line":446}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryHistory, path="$.return", validator=_cott_validate_abi)
    return _result

def start_session(connection: Connection, history_capacity: U64) -> IdeSession:
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    history_capacity = _cott_validate_abi(history_capacity, U64, path="$.history_capacity")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/start_session.py", "57f0486a3aebee757606607e5c9e92d782cb886722176b8c806d29be87d120e7", "start_session", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.start_session")
        _result = _implementation(connection, history_capacity)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.start_session"
        if _error.span is None:
            _error.span = {"end_byte":18539,"end_column":1,"end_line":458,"start_byte":18266,"start_column":1,"start_line":450}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.start_session", phase="implementation-call", span={"end_byte":18539,"end_column":1,"end_line":458,"start_byte":18266,"start_column":1,"start_line":450}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.start_session", phase="implementation-call", span={"end_byte":18539,"end_column":1,"end_line":458,"start_byte":18266,"start_column":1,"start_line":450}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, IdeSession, path="$.return")
    if not (_cott_contract_condition((((_result).connection == connection)), "real.harlequin.core.start_session", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:0", phase="ensures", span={"end_byte":18388,"end_column":44,"end_line":451,"start_byte":18349,"start_column":5,"start_line":451}, expected="true", actual="false")
    if not (_cott_contract_condition(((len((_result).tabs) == 0)), "real.harlequin.core.start_session", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:1", phase="ensures", span={"end_byte":18421,"end_column":33,"end_line":452,"start_byte":18393,"start_column":5,"start_line":452}, expected="true", actual="false")
    if not (_cott_contract_condition(((len(((_result).history).entries) == 0)), "real.harlequin.core.start_session", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:2", phase="ensures", span={"end_byte":18465,"end_column":44,"end_line":453,"start_byte":18426,"start_column":5,"start_line":453}, expected="true", actual="false")
    if not (_cott_contract_condition(((((_result).history).capacity == history_capacity)), "real.harlequin.core.start_session", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:3", phase="ensures", span={"end_byte":18521,"end_column":56,"end_line":454,"start_byte":18470,"start_column":5,"start_line":454}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=_cott_validate_abi)
    return _result

def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession:
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab = _cott_validate_abi(tab, QueryTab, path="$.tab")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/add_query_tab.py", "a5b6489a27ef38506938e2c3365fd985766c5bdbd7632fad7fb00a08d084d431", "add_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.add_query_tab")
        _result = _implementation(session, tab)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.add_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":18676,"end_column":1,"end_line":463,"start_byte":18539,"start_column":1,"start_line":458}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.add_query_tab", phase="implementation-call", span={"end_byte":18676,"end_column":1,"end_line":463,"start_byte":18539,"start_column":1,"start_line":458}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.add_query_tab", phase="implementation-call", span={"end_byte":18676,"end_column":1,"end_line":463,"start_byte":18539,"start_column":1,"start_line":458}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, IdeSession, path="$.return")
    if not (_cott_contract_condition(((len((_result).tabs) == (len((session).tabs) + 1))), "real.harlequin.core.add_query_tab", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.add_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":18658,"end_column":52,"end_line":459,"start_byte":18611,"start_column":5,"start_line":459}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=_cott_validate_abi)
    return _result

def activate_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab_id = _cott_validate_abi(tab_id, str, path="$.tab_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/activate_query_tab.py", "01a6ff5a821e885fb32b61f0985eaa88628b9eb96b5aad973769c33d73aab181", "activate_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.activate_query_tab")
        _result = _implementation(session, tab_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.activate_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":18892,"end_column":1,"end_line":470,"start_byte":18676,"start_column":1,"start_line":463}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.activate_query_tab", phase="implementation-call", span={"end_byte":18892,"end_column":1,"end_line":470,"start_byte":18676,"start_column":1,"start_line":463}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.activate_query_tab", phase="implementation-call", span={"end_byte":18892,"end_column":1,"end_line":470,"start_byte":18676,"start_column":1,"start_line":463}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IdeSession, SessionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.activate_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SessionError_TabMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.activate_query_tab", phase="error", span={"end_byte":18892,"end_column":1,"end_line":470,"start_byte":18676,"start_column":1,"start_line":463}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.activate_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.activate_query_tab", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SessionError_TabMissing:
        _cott_contract_condition(True, "real.harlequin.core.activate_query_tab", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((len((updated).tabs) == len((session).tabs))), "real.harlequin.core.activate_query_tab", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.core.activate_query_tab", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.activate_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":18839,"end_column":71,"end_line":464,"start_byte":18773,"start_column":5,"start_line":464}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/harlequin/core/close_query_tab.py", "883c9fa69f1e9541aac1e4c43c1dff8a7d6f8ec40f62435a96b06f623791252d", "close_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.close_query_tab")
        _result = _implementation(session, tab_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.close_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":19182,"end_column":1,"end_line":481,"start_byte":18892,"start_column":1,"start_line":470}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.close_query_tab", phase="implementation-call", span={"end_byte":19182,"end_column":1,"end_line":481,"start_byte":18892,"start_column":1,"start_line":470}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.close_query_tab", phase="implementation-call", span={"end_byte":19182,"end_column":1,"end_line":481,"start_byte":18892,"start_column":1,"start_line":470}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IdeSession, SessionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.close_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SessionError_TabMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.close_query_tab", phase="error", span={"end_byte":19182,"end_column":1,"end_line":481,"start_byte":18892,"start_column":1,"start_line":470}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.close_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.close_query_tab", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SessionError_TabMissing:
        _cott_contract_condition(True, "real.harlequin.core.close_query_tab", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((len((updated).tabs) < len((session).tabs))), "real.harlequin.core.close_query_tab", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.close_query_tab", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.close_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":19129,"end_column":70,"end_line":475,"start_byte":19064,"start_column":5,"start_line":475}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[IdeSession, SessionError], path="$.return", validator=_cott_validate_abi)
    return _result

def split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/split_statements.py", "a93b6fffee03db128966953ee46dfd6fb01f27ab2013eedade45ad3978a34d7c", "split_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.split_statements")
        _result = _implementation(sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.split_statements"
        if _error.span is None:
            _error.span = {"end_byte":19399,"end_column":1,"end_line":489,"start_byte":19182,"start_column":1,"start_line":481}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":19399,"end_column":1,"end_line":489,"start_byte":19182,"start_column":1,"start_line":481}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":19399,"end_column":1,"end_line":489,"start_byte":19182,"start_column":1,"start_line":481}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.split_statements", phase="error", span={"end_byte":19399,"end_column":1,"end_line":489,"start_byte":19182,"start_column":1,"start_line":481}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.split_statements", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_EmptySql:
        _cott_contract_condition(True, "real.harlequin.core.split_statements", "error:1")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnterminatedSql:
        _cott_contract_condition(True, "real.harlequin.core.split_statements", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            statements = _cott_match_value.value
            return (_cott_contract_condition(((len(statements) > 0)), "real.harlequin.core.split_statements", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.core.split_statements", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.split_statements", clause="ensures:0", phase="ensures", span={"end_byte":19305,"end_column":56,"end_line":482,"start_byte":19254,"start_column":5,"start_line":482}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_sql.py", "5d308063cd2a2940c11231ec260829e48438fb62ac86ec553b43a9f8abaa3979", "execute_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_sql")
        _result = _implementation(database, sql, read_only)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_sql"
        if _error.span is None:
            _error.span = {"end_byte":19824,"end_column":1,"end_line":504,"start_byte":19399,"start_column":1,"start_line":489}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":19824,"end_column":1,"end_line":504,"start_byte":19399,"start_column":1,"start_line":489}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":19824,"end_column":1,"end_line":504,"start_byte":19399,"start_column":1,"start_line":489}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[QueryResult], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_sql", phase="error", span={"end_byte":19824,"end_column":1,"end_line":504,"start_byte":19399,"start_column":1,"start_line":489}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_EmptySql:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:1")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnterminatedSql:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:2")
    if type(_result) is Err and type(_result.error) is SqlClientError_ReadOnlyViolation:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:3")
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:4")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnsupportedValue:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:5")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            results = _cott_match_value.value
            return (_cott_contract_condition(((len(results) > 0)), "real.harlequin.core.execute_sql", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.core.execute_sql", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_sql", clause="ensures:0", phase="ensures", span={"end_byte":19577,"end_column":50,"end_line":494,"start_byte":19532,"start_column":5,"start_line":494}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[QueryResult], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]:
    """Split SQL with real.harlequin.core.split_statements and propagate its errors.
Validate and lock connection.session, then execute every statement through its
actual retained SDK driver. Never reconnect using endpoint or a string id.
Closed/malformed sessions return ExecutionFailed with a fixed nonsecret message.
Reject raw BEGIN/START TRANSACTION/COMMIT/ROLLBACK/SAVEPOINT/RELEASE commands as
ExecutionFailed: transaction ownership belongs to the explicit lease API.
read_only rejects write-intent statements as ReadOnlyViolation before execution;
retain the driver's read-only controls too. Use concrete SDK methods, not
reflection or invented host adapters. Return one QueryResult per split statement.
Column names and rows remain in driver order. QueryBatch.statements preserves
the exact split strings. Fetch at most maximum_rows+1 rows; overflow returns
ResultLimitExceeded(limit=maximum_rows), not a truncated success.
Convert null to Cell.Null, bool to Integer(0/1), signed-I64 integers to Integer,
finite floats to Real, strings to Text and binary buffers to Blob. Decimal/date/
time/UUID scalar values become their exact string representation in Text;
unsupported nested/opaque values and out-of-range numbers are UnsupportedValue.
Use DBAPI cursors for the SQL adapters, BigQuery query(...).result(), Cassandra
Session.execute, and NebulaGraph Session.execute/as_primitive with checked
success status. Close cursors/results, but never the borrowed session.
With an active lease do not commit or roll back automatically; the explicit
transaction owner decides. Without a lease, commit each successful statement
for transactional SDKs and roll back its failed statement; previous successful
statements are already committed. SDK failures are ExecutionFailed; an actual
cancellation is Cancelled. Error messages never contain connection credentials."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    maximum_rows = _cott_validate_abi(maximum_rows, U32, path="$.maximum_rows")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_statements.py", "299c91464f35c17782278adedece8d60e45263fdcaad3c7f5a8560007e712ea2", "execute_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_statements")
        _result = _implementation(connection, sql, maximum_rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_statements"
        if _error.span is None:
            _error.span = {"end_byte":22339,"end_column":1,"end_line":548,"start_byte":19824,"start_column":1,"start_line":504}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_statements", phase="implementation-call", span={"end_byte":22339,"end_column":1,"end_line":548,"start_byte":19824,"start_column":1,"start_line":504}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_statements", phase="implementation-call", span={"end_byte":22339,"end_column":1,"end_line":548,"start_byte":19824,"start_column":1,"start_line":504}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryBatch, SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_ExecutionFailed, SqlClientError_ResultLimitExceeded, SqlClientError_Cancelled, SqlClientError_UnsupportedValue,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_statements", phase="error", span={"end_byte":22339,"end_column":1,"end_line":548,"start_byte":19824,"start_column":1,"start_line":504}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_EmptySql:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:2")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnterminatedSql:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:3")
    if type(_result) is Err and type(_result.error) is SqlClientError_ReadOnlyViolation:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:4")
    if type(_result) is Err and type(_result.error) is SqlClientError_ExecutionFailed:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:5")
    if type(_result) is Err and type(_result.error) is SqlClientError_ResultLimitExceeded:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:6")
    if type(_result) is Err and type(_result.error) is SqlClientError_Cancelled:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:7")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnsupportedValue:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            batch = _cott_match_value.value
            return (_cott_contract_condition(((len((batch).statements) == len((batch).results))), "real.harlequin.core.execute_statements", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.execute_statements", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_statements", clause="ensures:1", phase="ensures", span={"end_byte":22001,"end_column":74,"end_line":536,"start_byte":21932,"start_column":5,"start_line":536}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryBatch, SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]:
    """Set sdk: Any = boto3; client: Any = sdk.client("s3"); decode Body to source: str."""
    reference = _cott_validate_abi(reference, FileReference, path="$.reference")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/load_query_file.py", "bc15d9e5fe688d12d3fbdafab4452734a9b83b17a9e29cb8835fbec143f27e43", "load_query_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.load_query_file")
        _result = _implementation(reference)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.load_query_file"
        if _error.span is None:
            _error.span = {"end_byte":22761,"end_column":1,"end_line":562,"start_byte":22339,"start_column":1,"start_line":548}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.load_query_file", phase="implementation-call", span={"end_byte":22761,"end_column":1,"end_line":562,"start_byte":22339,"start_column":1,"start_line":548}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.load_query_file", phase="implementation-call", span={"end_byte":22761,"end_column":1,"end_line":562,"start_byte":22339,"start_column":1,"start_line":548}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LoadedFile, FileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.load_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileError_NotFound, FileError_PermissionDenied, FileError_InvalidEncoding, FileError_TransferFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.load_query_file", phase="error", span={"end_byte":22761,"end_column":1,"end_line":562,"start_byte":22339,"start_column":1,"start_line":548}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.load_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is FileError_NotFound:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:2")
    if type(_result) is Err and type(_result.error) is FileError_PermissionDenied:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:3")
    if type(_result) is Err and type(_result.error) is FileError_InvalidEncoding:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:4")
    if type(_result) is Err and type(_result.error) is FileError_TransferFailed:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (_cott_contract_condition((((loaded).reference == reference)), "real.harlequin.core.load_query_file", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.load_query_file", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:1", phase="ensures", span={"end_byte":22587,"end_column":63,"end_line":553,"start_byte":22529,"start_column":5,"start_line":553}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LoadedFile, FileError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]:
    reference = _cott_validate_abi(reference, FileReference, path="$.reference")
    source = _cott_validate_abi(source, str, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/save_query_file.py", "b1b7556380e249523c34c400f7d173a18e2659fb6f5b17636bcfbe5a16f78e39", "save_query_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.save_query_file")
        _result = _implementation(reference, source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.save_query_file"
        if _error.span is None:
            _error.span = {"end_byte":23022,"end_column":1,"end_line":570,"start_byte":22761,"start_column":1,"start_line":562}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.save_query_file", phase="implementation-call", span={"end_byte":23022,"end_column":1,"end_line":570,"start_byte":22761,"start_column":1,"start_line":562}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.save_query_file", phase="implementation-call", span={"end_byte":23022,"end_column":1,"end_line":570,"start_byte":22761,"start_column":1,"start_line":562}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[SavedFile, FileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.save_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileError_PermissionDenied, FileError_TransferFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.save_query_file", phase="error", span={"end_byte":23022,"end_column":1,"end_line":570,"start_byte":22761,"start_column":1,"start_line":562}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.save_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.save_query_file", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is FileError_PermissionDenied:
        _cott_contract_condition(True, "real.harlequin.core.save_query_file", "error:1")
    if type(_result) is Err and type(_result.error) is FileError_TransferFailed:
        _cott_contract_condition(True, "real.harlequin.core.save_query_file", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition((((saved).reference == reference)), "real.harlequin.core.save_query_file", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.core.save_query_file", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.save_query_file", clause="ensures:0", phase="ensures", span={"end_byte":22912,"end_column":61,"end_line":563,"start_byte":22856,"start_column":5,"start_line":563}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[SavedFile, FileError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """Parse/connect; read SQL at sql> until .quit/EOF; execute and print tab-separated results."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/run.py", "ceabcebb7eca441b6c0103aa32beb9bf9a7e7f00ec530ba1bec88287d208ca8b", "run", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.run"
        if _error.span is None:
            _error.span = {"end_byte":23352,"end_column":1,"end_line":585,"start_byte":23022,"start_column":1,"start_line":570}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.run", phase="implementation-call", span={"end_byte":23352,"end_column":1,"end_line":585,"start_byte":23022,"start_column":1,"start_line":570}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.harlequin.core.run", phase="return", span={"end_byte":23352,"end_column":1,"end_line":585,"start_byte":23022,"start_column":1,"start_line":570}, expected="Never", actual=repr(_result))

__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_HistoryCapacityInvalid", "SessionError_TabMissing", "SessionHandle", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TransactionLease", "TypedRow", "activate_query_tab", "adapter_descriptors", "add_query_tab", "append_query_history", "begin_transaction", "close_query_tab", "commit_transaction", "connect", "disconnect", "edit_query_tab", "execute_sql", "execute_statements", "load_configuration", "load_query_file", "open_query_tab", "parse_cli", "resolve_profile", "rollback_transaction", "run", "save_query_file", "split_statements", "start_session"]
