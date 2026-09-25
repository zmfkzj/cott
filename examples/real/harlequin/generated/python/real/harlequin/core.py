from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_any_blank_by, _cott_unique_by

from real.harlequin.core_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, CliError, CliError_ConflictingConnectionInputs, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, CliOptions, Configuration, ConfigurationError, ConfigurationError_Invalid, ConfigurationError_Missing, ConfigurationError_ProfileDuplicate, ConfigurationError_ProfileMissing, Connection, ConnectionError, ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed, ConnectionError_Failed, ConnectionError_InvalidEndpoint, ConnectionError_LeaseRejected, ConnectionError_TransactionsUnsupported, ConnectionProfile, ConnectionRequest, DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, FileError, FileError_InvalidEncoding, FileError_NotFound, FileError_PermissionDenied, FileError_TransferFailed, FileLocation, FileLocation_Local, FileLocation_S3, FileReference, IdeSession, LoadedFile, QueryBatch, QueryHistory, QueryHistoryEntry, QueryResult, QueryTab, SavedFile, SessionError, SessionError_TabMissing, SessionHandle, Setting, SqlClientError, SqlClientError_Cancelled, SqlClientError_EmptySql, SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql, Transaction, TransactionLease, TransactionStatus, TransactionStatus_Active, TransactionStatus_Committed, TransactionStatus_RolledBack, TypedRow

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
            _error.span = {"end_byte":10388,"end_column":1,"end_line":299,"start_byte":9220,"start_column":1,"start_line":275}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.adapter_descriptors", phase="implementation-call", span={"end_byte":10388,"end_column":1,"end_line":299,"start_byte":9220,"start_column":1,"start_line":275}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.adapter_descriptors", phase="implementation-call", span={"end_byte":10388,"end_column":1,"end_line":299,"start_byte":9220,"start_column":1,"start_line":275}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[AdapterDescriptor], path="$.return")
    if not (_cott_contract_condition(((len(_result) == 11)), "real.harlequin.core.adapter_descriptors", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.adapter_descriptors", clause="ensures:1", phase="ensures", span={"end_byte":10370,"end_column":29,"end_line":295,"start_byte":10346,"start_column":5,"start_line":295}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[AdapterDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]:
    """Parse process arguments (without the program name) from left to right.
Value options: --profile NAME or -P NAME, --adapter NAME or -a NAME, and
--query-file PATH or -f PATH. Switches: --read-only or -r, and --no-config.
A long value option also accepts --option=VALUE; otherwise its value is the next
argument verbatim, even when that argument starts with "-". A repeated value
option keeps its last value; a repeated switch is harmless. "--" ends option
parsing and every later argument is positional. Before "--", "-" alone is
positional and any other argument starting with "-" must be one of the options
above. The single positional argument is the connection string.
An adapter NAME is one of the uri_schemes labels of adapter_descriptors (duckdb,
sqlite, postgres, postgresql, mysql, odbc, bigquery, trino, databricks, adbc,
cassandra, nebula), compared ignoring ASCII case.
The first offending argument decides the error: UnknownOption carries the whole
argument as given (a switch written with "=VALUE" is unknown); MissingOptionValue
names the long option ("--profile") whose value is missing at the end;
InvalidAdapter carries NAME as given; a second positional argument is
ConflictingConnectionInputs. After the scan, --profile together with --no-config
is ConflictingConnectionInputs. Absent options are Nothing and absent switches
false."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/parse_cli.py", "69649b472513fd72f2f8150cf272920c04111e415f48e26f7b794d868eded802", "parse_cli", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.parse_cli")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.parse_cli"
        if _error.span is None:
            _error.span = {"end_byte":12180,"end_column":1,"end_line":331,"start_byte":10388,"start_column":1,"start_line":299}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.parse_cli", phase="implementation-call", span={"end_byte":12180,"end_column":1,"end_line":331,"start_byte":10388,"start_column":1,"start_line":299}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.parse_cli", phase="implementation-call", span={"end_byte":12180,"end_column":1,"end_line":331,"start_byte":10388,"start_column":1,"start_line":299}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CliOptions, CliError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.parse_cli", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CliError_UnknownOption, CliError_MissingOptionValue, CliError_InvalidAdapter, CliError_ConflictingConnectionInputs,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.parse_cli", phase="error", span={"end_byte":12180,"end_column":1,"end_line":331,"start_byte":10388,"start_column":1,"start_line":299}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.parse_cli", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is CliError_UnknownOption:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:2")
    if type(_result) is Err and type(_result.error) is CliError_MissingOptionValue:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:3")
    if type(_result) is Err and type(_result.error) is CliError_InvalidAdapter:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:4")
    if type(_result) is Err and type(_result.error) is CliError_ConflictingConnectionInputs:
        _cott_contract_condition(True, "real.harlequin.core.parse_cli", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            options = _cott_match_value.value
            return (_cott_contract_condition((((not (len(arguments) == 0)) or ((not (options).read_only) and (not (options).no_config)))), "real.harlequin.core.parse_cli", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.parse_cli", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.parse_cli", clause="ensures:1", phase="ensures", span={"end_byte":12009,"end_column":106,"end_line":322,"start_byte":11908,"start_column":5,"start_line":322}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CliOptions, CliError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_configuration(path: Path) -> Result[Configuration, ConfigurationError]:
    """Read the UTF-8 TOML file at path. Top-level keys, all optional: default_profile
(string), theme (string, default "harlequin"), keymap (string, default
"default") and profiles, an array of tables. Each profile table has required
name (string), adapter (a parse_cli adapter label, compared ignoring ASCII case)
and connection (string, the endpoint), optional read_only (boolean, default
false) and optional settings, a table of string values that become Setting
entries in file order. Profiles keep file order. default_profile is not
resolved here.
A path that does not exist is Missing(path). An unreadable file, invalid UTF-8
or TOML, an unknown key, a missing required key or a value of the wrong type is
Invalid(path, message); message names the offending key (or says "invalid
TOML") and never repeats a configured value. Top-level keys are checked first,
then profiles in file order; a profile is validated before its name is compared,
and a name equal to an earlier profile's is ProfileDuplicate(name). A file that
exists but cannot be read, including an access refusal, is Invalid(path, message).
The path is read from the file system the program runs against: the fs fixture
root while a Cott scenario with an fs fixture is active, otherwise the host file
system. While such a fixture is active the host file system is never used, even
when the fixture read fails."""
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/load_configuration.py", "ba48fd7f1befd6c669bf7f731f0955264c2aa1d3ba073b70277a070087cd9013", "load_configuration", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.load_configuration")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.load_configuration"
        if _error.span is None:
            _error.span = {"end_byte":14135,"end_column":1,"end_line":364,"start_byte":12180,"start_column":1,"start_line":331}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.load_configuration", phase="implementation-call", span={"end_byte":14135,"end_column":1,"end_line":364,"start_byte":12180,"start_column":1,"start_line":331}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.load_configuration", phase="implementation-call", span={"end_byte":14135,"end_column":1,"end_line":364,"start_byte":12180,"start_column":1,"start_line":331}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Configuration, ConfigurationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.load_configuration", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigurationError_Missing, ConfigurationError_Invalid, ConfigurationError_ProfileDuplicate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.load_configuration", phase="error", span={"end_byte":14135,"end_column":1,"end_line":364,"start_byte":12180,"start_column":1,"start_line":331}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.load_configuration", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigurationError_Missing:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", "error:4")
    if type(_result) is Err and type(_result.error) is ConfigurationError_Invalid:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", "error:5")
    if type(_result) is Err and type(_result.error) is ConfigurationError_ProfileDuplicate:
        _cott_contract_condition(True, "real.harlequin.core.load_configuration", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            configuration = _cott_match_value.value
            return (_cott_contract_condition((_cott_unique_by((configuration).profiles, "name")), "real.harlequin.core.load_configuration", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.load_configuration", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_configuration", clause="ensures:1", phase="ensures", span={"end_byte":13826,"end_column":98,"end_line":354,"start_byte":13733,"start_column":5,"start_line":354}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is ConfigurationError_Missing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == path)), "real.harlequin.core.load_configuration", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.load_configuration", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_configuration", clause="ensures:2", phase="ensures", span={"end_byte":13905,"end_column":79,"end_line":355,"start_byte":13831,"start_column":5,"start_line":355}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is ConfigurationError_Invalid and True and True:
            invalid = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((invalid == path)), "real.harlequin.core.load_configuration", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.load_configuration", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_configuration", clause="ensures:3", phase="ensures", span={"end_byte":13987,"end_column":82,"end_line":356,"start_byte":13910,"start_column":5,"start_line":356}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Configuration, ConfigurationError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]:
    """Plan the connection request without I/O. With options.no_config the
configuration is ignored, as if it had no profiles and no default_profile.
The selected profile name is options.profile, else configuration.default_profile,
else none. A selected name without a profile of exactly that name is
ProfileMissing(name). With no selected name the base request is DuckDb, endpoint
":memory:", no settings and read_only false; otherwise it is the profile's
adapter, endpoint, settings and read_only. Then options.adapter replaces the
adapter, options.connection replaces the endpoint, and options.read_only true
makes the request read-only. Settings always come from the profile."""
    configuration = _cott_validate_abi(configuration, Configuration, path="$.configuration")
    options = _cott_validate_abi(options, CliOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_2() -> bool:
        _cott_match_value = (options).profile
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((((options).no_config or (len((configuration).profiles) == 0))), "real.harlequin.core.resolve_profile", "error:2:condition"))
        _cott_contract_condition((False), "real.harlequin.core.resolve_profile", "error:2:applicable")
        return False
    if _expected_error is None and (_cott_match_error_2()):
        _expected_error = ConfigurationError_ProfileMissing
        _expected_error_span = {"end_byte":15219,"end_column":148,"end_line":382,"start_byte":15076,"start_column":5,"start_line":382}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/resolve_profile.py", "a49f1260b8a388869501302d9be8cdd7094f93d9d637d30656fd94df14a15384", "resolve_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.resolve_profile")
        _result = _implementation(configuration, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.resolve_profile"
        if _error.span is None:
            _error.span = {"end_byte":15281,"end_column":1,"end_line":387,"start_byte":14135,"start_column":1,"start_line":364}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.resolve_profile", phase="implementation-call", span={"end_byte":15281,"end_column":1,"end_line":387,"start_byte":14135,"start_column":1,"start_line":364}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.resolve_profile", phase="implementation-call", span={"end_byte":15281,"end_column":1,"end_line":387,"start_byte":14135,"start_column":1,"start_line":364}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionRequest, ConfigurationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigurationError_ProfileMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.resolve_profile", phase="error", span={"end_byte":15281,"end_column":1,"end_line":387,"start_byte":14135,"start_column":1,"start_line":364}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.resolve_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.resolve_profile", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigurationError_ProfileMissing:
        _cott_contract_condition(True, "real.harlequin.core.resolve_profile", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((not (options).read_only) or (request).read_only)), "real.harlequin.core.resolve_profile", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.resolve_profile", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.resolve_profile", clause="ensures:1", phase="ensures", span={"end_byte":15070,"end_column":75,"end_line":380,"start_byte":15000,"start_column":5,"start_line":380}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionRequest, ConfigurationError], path="$.return", validator=_cott_validate_abi)
    return _result

def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    """Open and retain a real SDK session using AdapterKind's endpoint formats.
Return a fresh random UUID as 32 lowercase hexadecimal digits for id and a
SessionHandle with the exact documented payload. The returned driver stays
open; no probe-and-close success is allowed. Register actual resource cleanup
callbacks with ExitStack as resources are acquired, and transfer that stack into
the session only on complete success. A failed construction closes every
acquired resource before returning an error. Do not use SDK connection context
managers that implicitly commit on exit.

Settings are validated before any driver is loaded: a blank or repeated setting
name is InvalidEndpoint. For JSON endpoint adapters, settings override known
top-level fields: string fields use literal text, integers use decimal, booleans
use true/false, and object/list fields use JSON. Validate the resulting object
against AdapterKind's fields and retain its canonical JSON as endpoint.
PostgreSQL settings are libpq string parameters merged with make_conninfo.
ODBC settings are connection-string keyword/value overrides: keyword names
contain only ASCII letters/digits/underscore/space; brace-quote values and
double embedded closing braces, never concatenate unescaped input.
SQLite settings permit only timeout (positive finite seconds); DuckDB settings
permit only threads and memory_limit as documented driver config strings.
Unknown/invalid settings are InvalidEndpoint, not silently ignored.

SQLite uses sqlite3.Connection, isolation_level=None and check_same_thread=False;
its session lock serializes operations. :memory: remains alive in this
connection. A file endpoint opens an existing file URI with mode=ro or mode=rw
according to read_only, never silently creates a missing file. Apply query_only
when read_only is true. DuckDB retains DuckDBPyConnection; pass read_only for
files, and use an in-memory connection for :memory:.
PostgreSQL retains psycopg.Connection; MySQL retains pymysql.Connection;
ODBC retains pyodbc.Connection; ADBC retains adbc_driver_manager.dbapi.Connection.
These four use manual-commit mode for their lifetime. ADBC driver failure to
support manual commit is an error, not an ignored warning. connect reads no
catalog metadata.
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
Never retain a hidden owner of the driver."""
    request = _cott_validate_abi(request, ConnectionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((_cott_any_blank_by((request).settings, "name") or (not _cott_unique_by((request).settings, "name")))), "real.harlequin.core.connect", "error:5:condition")):
        _expected_error = ConnectionError_InvalidEndpoint
        _expected_error_span = {"end_byte":19006,"end_column":143,"end_line":441,"start_byte":18868,"start_column":5,"start_line":441}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/connect.py", "663bb7edbf5963af35bef3fd5213eab1114a6984904bfc2e53751c655be62886", "connect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.connect")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.connect"
        if _error.span is None:
            _error.span = {"end_byte":19248,"end_column":1,"end_line":449,"start_byte":15281,"start_column":1,"start_line":387}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.connect", phase="implementation-call", span={"end_byte":19248,"end_column":1,"end_line":449,"start_byte":15281,"start_column":1,"start_line":387}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.connect", phase="implementation-call", span={"end_byte":19248,"end_column":1,"end_line":449,"start_byte":15281,"start_column":1,"start_line":387}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Connection, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_AdapterUnavailable, ConnectionError_InvalidEndpoint, ConnectionError_AuthenticationFailed, ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.connect", phase="error", span={"end_byte":19248,"end_column":1,"end_line":449,"start_byte":15281,"start_column":1,"start_line":387}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.connect", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_AdapterUnavailable:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:6")
    if type(_result) is Err and type(_result.error) is ConnectionError_InvalidEndpoint:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:7")
    if type(_result) is Err and type(_result.error) is ConnectionError_AuthenticationFailed:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:8")
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.connect", "error:9")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (_cott_contract_condition((((connection).adapter == (request).adapter)), "real.harlequin.core.connect", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:1", phase="ensures", span={"end_byte":18644,"end_column":75,"end_line":436,"start_byte":18574,"start_column":5,"start_line":436}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (_cott_contract_condition((((connection).read_only == (request).read_only)), "real.harlequin.core.connect", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:2", phase="ensures", span={"end_byte":18723,"end_column":79,"end_line":437,"start_byte":18649,"start_column":5,"start_line":437}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            connection = _cott_match_value.value
            return (_cott_contract_condition(((len((connection).id) == 32)), "real.harlequin.core.connect", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:3", phase="ensures", span={"end_byte":18784,"end_column":61,"end_line":438,"start_byte":18728,"start_column":5,"start_line":438}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is ConnectionError_InvalidEndpoint and True:
            shown = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((shown == "")), "real.harlequin.core.connect", "ensures:4"))
        _cott_contract_condition((False), "real.harlequin.core.connect", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.connect", clause="ensures:4", phase="ensures", span={"end_byte":18862,"end_column":78,"end_line":439,"start_byte":18789,"start_column":5,"start_line":439}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/harlequin/core/disconnect.py", "33bec0e23957a9f62be40dcea1f43b149c8c259595a18bba155c73692598dd4d", "disconnect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.disconnect")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.disconnect"
        if _error.span is None:
            _error.span = {"end_byte":20585,"end_column":1,"end_line":477,"start_byte":19700,"start_column":1,"start_line":459}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.disconnect", phase="implementation-call", span={"end_byte":20585,"end_column":1,"end_line":477,"start_byte":19700,"start_column":1,"start_line":459}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.disconnect", phase="implementation-call", span={"end_byte":20585,"end_column":1,"end_line":477,"start_byte":19700,"start_column":1,"start_line":459}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.disconnect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.disconnect", phase="error", span={"end_byte":20585,"end_column":1,"end_line":477,"start_byte":19700,"start_column":1,"start_line":459}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.disconnect", clause="ensures:1", phase="ensures", span={"end_byte":20495,"end_column":46,"end_line":471,"start_byte":20454,"start_column":5,"start_line":471}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]:
    """Transactions are supported for Sqlite, DuckDb, PostgreSql, MySql, Odbc and Adbc,
matching adapter_descriptors; every other kind is TransactionsUnsupported(adapter)
before the session is touched, never a pretend active transaction.
Otherwise borrow and lock the live connection; a closed or malformed handle or an
already active lease is Failed. Start a real transaction on the existing SDK
driver: SQLite/DuckDB execute BEGIN, PostgreSQL executes BEGIN (READ ONLY when
the connection is read-only), and MySQL uses begin(). ODBC/ADBC are already in
manual-commit mode; their physical transaction may start lazily with the first
statement. Do not open, close or roll back a new connection as a substitute.
Install a fresh TransactionLease object as the session's active transaction and
return Transaction(connection=connection, lease=that lease, status=Active). If
starting fails, return Failed and leave no active lease. The caller retains
ownership of the connection."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((((((connection).adapter == AdapterKind_BigQuery()) or ((connection).adapter == AdapterKind_Trino())) or ((connection).adapter == AdapterKind_Databricks())) or ((connection).adapter == AdapterKind_Cassandra())) or ((connection).adapter == AdapterKind_NebulaGraph()))), "real.harlequin.core.begin_transaction", "error:4:condition")):
        _expected_error = ConnectionError_TransactionsUnsupported
        _expected_error_span = {"end_byte":22557,"end_column":287,"end_line":505,"start_byte":22275,"start_column":5,"start_line":505}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/begin_transaction.py", "d6663158387588840296ebb1ce2ae9ddedbefe98f7efa0f8c8d2c397bbabf92c", "begin_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.begin_transaction")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.begin_transaction"
        if _error.span is None:
            _error.span = {"end_byte":22631,"end_column":1,"end_line":510,"start_byte":20883,"start_column":1,"start_line":484}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.begin_transaction", phase="implementation-call", span={"end_byte":22631,"end_column":1,"end_line":510,"start_byte":20883,"start_column":1,"start_line":484}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.begin_transaction", phase="implementation-call", span={"end_byte":22631,"end_column":1,"end_line":510,"start_byte":20883,"start_column":1,"start_line":484}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.begin_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.begin_transaction", phase="error", span={"end_byte":22631,"end_column":1,"end_line":510,"start_byte":20883,"start_column":1,"start_line":484}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.begin_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.begin_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.begin_transaction", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            transaction = _cott_match_value.value
            return (_cott_contract_condition((((transaction).connection == connection)), "real.harlequin.core.begin_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.begin_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.begin_transaction", clause="ensures:1", phase="ensures", span={"end_byte":22084,"end_column":75,"end_line":501,"start_byte":22014,"start_column":5,"start_line":501}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            transaction = _cott_match_value.value
            return (_cott_contract_condition((((transaction).status == TransactionStatus_Active())), "real.harlequin.core.begin_transaction", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.begin_transaction", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.begin_transaction", clause="ensures:2", phase="ensures", span={"end_byte":22169,"end_column":85,"end_line":502,"start_byte":22089,"start_column":5,"start_line":502}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is ConnectionError_TransactionsUnsupported and True:
            kind = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((kind == (connection).adapter)), "real.harlequin.core.begin_transaction", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.begin_transaction", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.begin_transaction", clause="ensures:3", phase="ensures", span={"end_byte":22269,"end_column":100,"end_line":503,"start_byte":22174,"start_column":5,"start_line":503}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    """A snapshot whose status is not Active is LeaseRejected without touching any
session. Otherwise borrow transaction.connection and acquire its session lock.
The lease has authority only when the session is open, matches the connection,
and its payload transaction is the lease's unwrapped object; a stale,
already-finished, disconnected or wrong-owner lease is LeaseRejected without
touching a different session.
Call the actual existing SDK driver's commit. Never reconnect by id/endpoint.
On success clear the active lease and return the same connection and lease
with status=Committed. On a driver failure, clear the lease, mark the session
closed, attempt rollback and every registered cleanup callback, and return Failed
with a fixed nonsecret message; do not leave an ambiguously reusable transaction."""
    transaction = _cott_validate_abi(transaction, Transaction, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((transaction).status != TransactionStatus_Active())), "real.harlequin.core.commit_transaction", "error:3:condition")):
        _expected_error = ConnectionError_LeaseRejected
        _expected_error_span = {"end_byte":24155,"end_column":92,"end_line":535,"start_byte":24068,"start_column":5,"start_line":535}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/commit_transaction.py", "7aacda033f665ce218f0909856abb0ca8e8d789c8c6ce7981c76bbf92c89c3e5", "commit_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.commit_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":24269,"end_column":1,"end_line":541,"start_byte":22944,"start_column":1,"start_line":517}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.commit_transaction", phase="implementation-call", span={"end_byte":24269,"end_column":1,"end_line":541,"start_byte":22944,"start_column":1,"start_line":517}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.commit_transaction", phase="implementation-call", span={"end_byte":24269,"end_column":1,"end_line":541,"start_byte":22944,"start_column":1,"start_line":517}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_LeaseRejected, ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.commit_transaction", phase="error", span={"end_byte":24269,"end_column":1,"end_line":541,"start_byte":22944,"start_column":1,"start_line":517}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.commit_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_LeaseRejected:
        _cott_contract_condition(True, "real.harlequin.core.commit_transaction", "error:4")
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.commit_transaction", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).connection == (transaction).connection)), "real.harlequin.core.commit_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.commit_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.commit_transaction", clause="ensures:1", phase="ensures", span={"end_byte":23982,"end_column":79,"end_line":532,"start_byte":23908,"start_column":5,"start_line":532}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).status == TransactionStatus_Committed())), "real.harlequin.core.commit_transaction", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.commit_transaction", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.commit_transaction", clause="ensures:2", phase="ensures", span={"end_byte":24062,"end_column":80,"end_line":533,"start_byte":23987,"start_column":5,"start_line":533}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Transaction, ConnectionError], path="$.return", validator=_cott_validate_abi)
    return _result

def rollback_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    """Apply the same status and lease-authority checks as commit_transaction, with the
same LeaseRejected results, but call the existing SDK driver's rollback. Success
clears the active lease and returns the same connection and lease with
status=RolledBack. Double completion, stale leases and disconnected sessions are
never successful no-ops. A driver failure clears the lease, marks the session
closed, attempts all cleanup callbacks and returns Failed with a fixed nonsecret
message."""
    transaction = _cott_validate_abi(transaction, Transaction, path="$.transaction")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((transaction).status != TransactionStatus_Active())), "real.harlequin.core.rollback_transaction", "error:3:condition")):
        _expected_error = ConnectionError_LeaseRejected
        _expected_error_span = {"end_byte":25423,"end_column":92,"end_line":562,"start_byte":25336,"start_column":5,"start_line":562}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/rollback_transaction.py", "ab2c1f62b04448677412420ec2e80b60a14c4f2f2ff1aa51cd5ede08c679bda0", "rollback_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.rollback_transaction")
        _result = _implementation(transaction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":25537,"end_column":1,"end_line":568,"start_byte":24549,"start_column":1,"start_line":548}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.rollback_transaction", phase="implementation-call", span={"end_byte":25537,"end_column":1,"end_line":568,"start_byte":24549,"start_column":1,"start_line":548}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.rollback_transaction", phase="implementation-call", span={"end_byte":25537,"end_column":1,"end_line":568,"start_byte":24549,"start_column":1,"start_line":548}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Transaction, ConnectionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectionError_LeaseRejected, ConnectionError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.rollback_transaction", phase="error", span={"end_byte":25537,"end_column":1,"end_line":568,"start_byte":24549,"start_column":1,"start_line":548}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.rollback_transaction", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectionError_LeaseRejected:
        _cott_contract_condition(True, "real.harlequin.core.rollback_transaction", "error:4")
    if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
        _cott_contract_condition(True, "real.harlequin.core.rollback_transaction", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).connection == (transaction).connection)), "real.harlequin.core.rollback_transaction", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.rollback_transaction", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.rollback_transaction", clause="ensures:1", phase="ensures", span={"end_byte":25249,"end_column":79,"end_line":559,"start_byte":25175,"start_column":5,"start_line":559}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).status == TransactionStatus_RolledBack())), "real.harlequin.core.rollback_transaction", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.rollback_transaction", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.rollback_transaction", clause="ensures:2", phase="ensures", span={"end_byte":25330,"end_column":81,"end_line":560,"start_byte":25254,"start_column":5,"start_line":560}, expected="true", actual="false")
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
            _error.span = {"end_byte":26013,"end_column":1,"end_line":583,"start_byte":25773,"start_column":1,"start_line":574}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.open_query_tab", phase="implementation-call", span={"end_byte":26013,"end_column":1,"end_line":583,"start_byte":25773,"start_column":1,"start_line":574}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.open_query_tab", phase="implementation-call", span={"end_byte":26013,"end_column":1,"end_line":583,"start_byte":25773,"start_column":1,"start_line":574}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryTab, path="$.return")
    if not (_cott_contract_condition((((_result).id == id)), "real.harlequin.core.open_query_tab", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.open_query_tab", clause="ensures:0", phase="ensures", span={"end_byte":25865,"end_column":28,"end_line":575,"start_byte":25842,"start_column":5,"start_line":575}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).title == title)), "real.harlequin.core.open_query_tab", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.open_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":25899,"end_column":34,"end_line":576,"start_byte":25870,"start_column":5,"start_line":576}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).source == source)), "real.harlequin.core.open_query_tab", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.open_query_tab", clause="ensures:2", phase="ensures", span={"end_byte":25935,"end_column":36,"end_line":577,"start_byte":25904,"start_column":5,"start_line":577}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).cursor == 0)), "real.harlequin.core.open_query_tab", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.open_query_tab", clause="ensures:3", phase="ensures", span={"end_byte":25966,"end_column":31,"end_line":578,"start_byte":25940,"start_column":5,"start_line":578}, expected="true", actual="false")
    if not (_cott_contract_condition(((not (_result).dirty)), "real.harlequin.core.open_query_tab", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.open_query_tab", clause="ensures:4", phase="ensures", span={"end_byte":25995,"end_column":29,"end_line":579,"start_byte":25971,"start_column":5,"start_line":579}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryTab, path="$.return", validator=_cott_validate_abi)
    return _result

def edit_query_tab(tab: QueryTab, source: str, cursor: U64) -> QueryTab:
    """Replace the tab's source and move its cursor, clamped to the end of source.
The tab becomes dirty when source differs from its previous source."""
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
            _error.span = {"end_byte":26569,"end_column":1,"end_line":597,"start_byte":26013,"start_column":1,"start_line":583}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.edit_query_tab", phase="implementation-call", span={"end_byte":26569,"end_column":1,"end_line":597,"start_byte":26013,"start_column":1,"start_line":583}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.edit_query_tab", phase="implementation-call", span={"end_byte":26569,"end_column":1,"end_line":597,"start_byte":26013,"start_column":1,"start_line":583}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryTab, path="$.return")
    if not (_cott_contract_condition((((_result).id == (tab).id)), "real.harlequin.core.edit_query_tab", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":26324,"end_column":67,"end_line":589,"start_byte":26262,"start_column":5,"start_line":589}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).title == (tab).title)), "real.harlequin.core.edit_query_tab", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:2", phase="ensures", span={"end_byte":26324,"end_column":67,"end_line":589,"start_byte":26262,"start_column":5,"start_line":589}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).source == source)), "real.harlequin.core.edit_query_tab", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:3", phase="ensures", span={"end_byte":26360,"end_column":36,"end_line":590,"start_byte":26329,"start_column":5,"start_line":590}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (cursor <= len(source))) or ((_result).cursor == cursor))), "real.harlequin.core.edit_query_tab", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:4", phase="ensures", span={"end_byte":26422,"end_column":62,"end_line":591,"start_byte":26365,"start_column":5,"start_line":591}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (cursor > len(source))) or ((_result).cursor == len(source)))), "real.harlequin.core.edit_query_tab", "ensures:5")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:5", phase="ensures", span={"end_byte":26487,"end_column":65,"end_line":592,"start_byte":26427,"start_column":5,"start_line":592}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).dirty == ((tab).dirty or (source != (tab).source)))), "real.harlequin.core.edit_query_tab", "ensures:6")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.edit_query_tab", clause="ensures:6", phase="ensures", span={"end_byte":26551,"end_column":64,"end_line":593,"start_byte":26492,"start_column":5,"start_line":593}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryTab, path="$.return", validator=_cott_validate_abi)
    return _result

def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory:
    """Append entry as the newest entry; when history is full, drop the oldest entries
so that at most capacity remain."""
    history = _cott_validate_abi(history, QueryHistory, path="$.history")
    entry = _cott_validate_abi(entry, QueryHistoryEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/append_query_history.py", "48096c8fe67f071e66ca57bae148b5a000fb9d33b352d9eaa7663dc22cda9908", "append_query_history", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.append_query_history")
        _result = _implementation(history, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.append_query_history"
        if _error.span is None:
            _error.span = {"end_byte":27064,"end_column":1,"end_line":609,"start_byte":26569,"start_column":1,"start_line":597}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.append_query_history", phase="implementation-call", span={"end_byte":27064,"end_column":1,"end_line":609,"start_byte":26569,"start_column":1,"start_line":597}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.append_query_history", phase="implementation-call", span={"end_byte":27064,"end_column":1,"end_line":609,"start_byte":26569,"start_column":1,"start_line":597}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, QueryHistory, path="$.return")
    if not (_cott_contract_condition((((_result).capacity == (history).capacity)), "real.harlequin.core.append_query_history", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.append_query_history", clause="ensures:1", phase="ensures", span={"end_byte":26848,"end_column":48,"end_line":603,"start_byte":26805,"start_column":5,"start_line":603}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len((history).entries) < (history).capacity)) or (len((_result).entries) == (len((history).entries) + 1)))), "real.harlequin.core.append_query_history", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.append_query_history", clause="ensures:2", phase="ensures", span={"end_byte":26950,"end_column":102,"end_line":604,"start_byte":26853,"start_column":5,"start_line":604}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len((history).entries) == (history).capacity)) or (len((_result).entries) == (history).capacity))), "real.harlequin.core.append_query_history", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.append_query_history", clause="ensures:3", phase="ensures", span={"end_byte":27046,"end_column":96,"end_line":605,"start_byte":26955,"start_column":5,"start_line":605}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, QueryHistory, path="$.return", validator=_cott_validate_abi)
    return _result

def start_session(connection: Connection, history_capacity: U64) -> IdeSession:
    """Start editor state for connection: no tabs, no active tab, empty history with
history_capacity."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    history_capacity = _cott_validate_abi(history_capacity, U64, path="$.history_capacity")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/start_session.py", "cde6b74bcc1c7f9c12ad93acd6319fb378f589b80a9757b655e9bed402161068", "start_session", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.start_session")
        _result = _implementation(connection, history_capacity)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.start_session"
        if _error.span is None:
            _error.span = {"end_byte":27468,"end_column":1,"end_line":622,"start_byte":27064,"start_column":1,"start_line":609}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.start_session", phase="implementation-call", span={"end_byte":27468,"end_column":1,"end_line":622,"start_byte":27064,"start_column":1,"start_line":609}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.start_session", phase="implementation-call", span={"end_byte":27468,"end_column":1,"end_line":622,"start_byte":27064,"start_column":1,"start_line":609}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, IdeSession, path="$.return")
    if not (_cott_contract_condition((((_result).connection_id == (connection).id)), "real.harlequin.core.start_session", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:1", phase="ensures", span={"end_byte":27317,"end_column":50,"end_line":615,"start_byte":27272,"start_column":5,"start_line":615}, expected="true", actual="false")
    if not (_cott_contract_condition(((len((_result).tabs) == 0)), "real.harlequin.core.start_session", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:2", phase="ensures", span={"end_byte":27350,"end_column":33,"end_line":616,"start_byte":27322,"start_column":5,"start_line":616}, expected="true", actual="false")
    if not (_cott_contract_condition(((len(((_result).history).entries) == 0)), "real.harlequin.core.start_session", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:3", phase="ensures", span={"end_byte":27394,"end_column":44,"end_line":617,"start_byte":27355,"start_column":5,"start_line":617}, expected="true", actual="false")
    if not (_cott_contract_condition(((((_result).history).capacity == history_capacity)), "real.harlequin.core.start_session", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.start_session", clause="ensures:4", phase="ensures", span={"end_byte":27450,"end_column":56,"end_line":618,"start_byte":27399,"start_column":5,"start_line":618}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=_cott_validate_abi)
    return _result

def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession:
    """A tab with the same id is replaced in place; otherwise tab is appended.
The added tab becomes active."""
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab = _cott_validate_abi(tab, QueryTab, path="$.tab")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/add_query_tab.py", "6bfff490e6ce6727eec921678f9756932c70c0b36d811abfa917e228b3bbe610", "add_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.add_query_tab")
        _result = _implementation(session, tab)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.add_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":27788,"end_column":1,"end_line":633,"start_byte":27468,"start_column":1,"start_line":622}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.add_query_tab", phase="implementation-call", span={"end_byte":27788,"end_column":1,"end_line":633,"start_byte":27468,"start_column":1,"start_line":622}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.add_query_tab", phase="implementation-call", span={"end_byte":27788,"end_column":1,"end_line":633,"start_byte":27468,"start_column":1,"start_line":622}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, IdeSession, path="$.return")
    if not (_cott_contract_condition((((_result).connection_id == (session).connection_id)), "real.harlequin.core.add_query_tab", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.add_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":27724,"end_column":58,"end_line":628,"start_byte":27671,"start_column":5,"start_line":628}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).history == (session).history)), "real.harlequin.core.add_query_tab", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.add_query_tab", clause="ensures:2", phase="ensures", span={"end_byte":27770,"end_column":46,"end_line":629,"start_byte":27729,"start_column":5,"start_line":629}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=_cott_validate_abi)
    return _result

def activate_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    """Make the tab with tab_id active. An unknown id is TabMissing(tab_id)."""
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab_id = _cott_validate_abi(tab_id, str, path="$.tab_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/activate_query_tab.py", "4ef3d424e2116c7741bd2b18b0275be97cf7c632d9364f6b72417d2fb584f389", "activate_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.activate_query_tab")
        _result = _implementation(session, tab_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.activate_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":28291,"end_column":1,"end_line":646,"start_byte":27788,"start_column":1,"start_line":633}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.activate_query_tab", phase="implementation-call", span={"end_byte":28291,"end_column":1,"end_line":646,"start_byte":27788,"start_column":1,"start_line":633}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.activate_query_tab", phase="implementation-call", span={"end_byte":28291,"end_column":1,"end_line":646,"start_byte":27788,"start_column":1,"start_line":633}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IdeSession, SessionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.activate_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SessionError_TabMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.activate_query_tab", phase="error", span={"end_byte":28291,"end_column":1,"end_line":646,"start_byte":27788,"start_column":1,"start_line":633}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.activate_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.activate_query_tab", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SessionError_TabMissing:
        _cott_contract_condition(True, "real.harlequin.core.activate_query_tab", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((updated).tabs == (session).tabs)), "real.harlequin.core.activate_query_tab", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.activate_query_tab", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.activate_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":28038,"end_column":63,"end_line":638,"start_byte":27980,"start_column":5,"start_line":638}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((((updated).connection_id == (session).connection_id) and ((updated).history == (session).history))), "real.harlequin.core.activate_query_tab", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.activate_query_tab", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.activate_query_tab", clause="ensures:2", phase="ensures", span={"end_byte":28160,"end_column":122,"end_line":639,"start_byte":28043,"start_column":5,"start_line":639}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is SessionError_TabMissing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == tab_id)), "real.harlequin.core.activate_query_tab", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.activate_query_tab", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.activate_query_tab", clause="ensures:3", phase="ensures", span={"end_byte":28238,"end_column":78,"end_line":640,"start_byte":28165,"start_column":5,"start_line":640}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[IdeSession, SessionError], path="$.return", validator=_cott_validate_abi)
    return _result

def close_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    """Remove the tab with tab_id, keeping the order of the others. When it was active,
the tab that followed it becomes active, else the tab that preceded it, else
none; otherwise the active tab is unchanged. An unknown id is TabMissing(tab_id)."""
    session = _cott_validate_abi(session, IdeSession, path="$.session")
    tab_id = _cott_validate_abi(tab_id, str, path="$.tab_id")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/close_query_tab.py", "773c8c9bfa24d4136e5d13fbd810e64d940d8e86c750009896de753277375b03", "close_query_tab", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.close_query_tab")
        _result = _implementation(session, tab_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.close_query_tab"
        if _error.span is None:
            _error.span = {"end_byte":28981,"end_column":1,"end_line":661,"start_byte":28291,"start_column":1,"start_line":646}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.close_query_tab", phase="implementation-call", span={"end_byte":28981,"end_column":1,"end_line":661,"start_byte":28291,"start_column":1,"start_line":646}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.close_query_tab", phase="implementation-call", span={"end_byte":28981,"end_column":1,"end_line":661,"start_byte":28291,"start_column":1,"start_line":646}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IdeSession, SessionError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.close_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SessionError_TabMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.close_query_tab", phase="error", span={"end_byte":28981,"end_column":1,"end_line":661,"start_byte":28291,"start_column":1,"start_line":646}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.close_query_tab", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.close_query_tab", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SessionError_TabMissing:
        _cott_contract_condition(True, "real.harlequin.core.close_query_tab", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition((((len((updated).tabs) + 1) == len((session).tabs))), "real.harlequin.core.close_query_tab", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.close_query_tab", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.close_query_tab", clause="ensures:1", phase="ensures", span={"end_byte":28728,"end_column":75,"end_line":653,"start_byte":28658,"start_column":5,"start_line":653}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((((updated).connection_id == (session).connection_id) and ((updated).history == (session).history))), "real.harlequin.core.close_query_tab", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.close_query_tab", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.close_query_tab", clause="ensures:2", phase="ensures", span={"end_byte":28850,"end_column":122,"end_line":654,"start_byte":28733,"start_column":5,"start_line":654}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is SessionError_TabMissing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == tab_id)), "real.harlequin.core.close_query_tab", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.close_query_tab", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.close_query_tab", clause="ensures:3", phase="ensures", span={"end_byte":28928,"end_column":78,"end_line":655,"start_byte":28855,"start_column":5,"start_line":655}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[IdeSession, SessionError], path="$.return", validator=_cott_validate_abi)
    return _result

def split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    """Split SQL text at semicolons outside quoted text and comments. Quoted text is
'...' (string), "..." or `...` (identifiers); a doubled quote character inside
continues it. Comments are -- to the end of the line and /* ... */ (not nested).
Each statement is its source text between separators with surrounding ASCII
whitespace (space, TAB, LF, VT, FF, CR) removed; comments inside it are kept.
A piece containing only whitespace and comments is dropped. No other quoting
(dollar quotes, backslash escapes) is recognized.
An unclosed quote is UnterminatedSql with that quote character as delimiter; an
unclosed block comment is UnterminatedSql("*/"). Text without any statement is
EmptySql. Scanning reports UnterminatedSql before EmptySql."""
    sql = _cott_validate_abi(sql, str, path="$.sql")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/split_statements.py", "dfa1f3524cbb5f0eaa8c5e8d40ae5a4b60772e6e01d1267b95fc60b427fce74f", "split_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.split_statements")
        _result = _implementation(sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.split_statements"
        if _error.span is None:
            _error.span = {"end_byte":29997,"end_column":1,"end_line":682,"start_byte":28981,"start_column":1,"start_line":661}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":29997,"end_column":1,"end_line":682,"start_byte":28981,"start_column":1,"start_line":661}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.split_statements", phase="implementation-call", span={"end_byte":29997,"end_column":1,"end_line":682,"start_byte":28981,"start_column":1,"start_line":661}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.split_statements", phase="error", span={"end_byte":29997,"end_column":1,"end_line":682,"start_byte":28981,"start_column":1,"start_line":661}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.split_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.split_statements", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_EmptySql:
        _cott_contract_condition(True, "real.harlequin.core.split_statements", "error:2")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnterminatedSql:
        _cott_contract_condition(True, "real.harlequin.core.split_statements", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            statements = _cott_match_value.value
            return (_cott_contract_condition(((len(statements) > 0)), "real.harlequin.core.split_statements", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.split_statements", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.split_statements", clause="ensures:1", phase="ensures", span={"end_byte":29903,"end_column":56,"end_line":675,"start_byte":29852,"start_column":5,"start_line":675}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]:
    """Run SQL on a standalone SQLite database with sqlite3, independent of any live
connection. Memory opens a fresh empty in-memory database that exists only for
this call; File(path) opens that existing file, never creating it, with mode=ro
when read_only. Split sql with real.harlequin.core.split_statements and propagate
its errors. A statement whose first keyword, ignoring comments and ASCII case, is
BEGIN, START, COMMIT, ROLLBACK, SAVEPOINT, RELEASE or END is SqliteFailure before
anything runs. With read_only, PRAGMA query_only is enabled, and a statement that
SQLite refuses as a write (SQLITE_READONLY) is ReadOnlyViolation(statement).
All statements execute in one transaction that is committed only after every
statement succeeds; any failure rolls back the whole batch.
Return one QueryResult per statement, in order: column names from the cursor
description (none for statements without a result set), every row, and
affected_rows equal to the cursor rowcount (-1 when SQLite reports none).
NULL, INTEGER, REAL, TEXT and BLOB values become Null, Integer, Real, Text and
Blob; a non-finite REAL is UnsupportedValue("REAL"). Other SQLite errors are
SqliteFailure with SQLite's message."""
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    read_only = _cott_validate_abi(read_only, bool, path="$.read_only")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_sql.py", "0a9b55b6e6494fdd5e038d5b849aa077d5cd47a73dfe99a9aea58d00fbc1df95", "execute_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_sql")
        _result = _implementation(database, sql, read_only)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_sql"
        if _error.span is None:
            _error.span = {"end_byte":31701,"end_column":1,"end_line":716,"start_byte":29997,"start_column":1,"start_line":682}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":31701,"end_column":1,"end_line":716,"start_byte":29997,"start_column":1,"start_line":682}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_sql", phase="implementation-call", span={"end_byte":31701,"end_column":1,"end_line":716,"start_byte":29997,"start_column":1,"start_line":682}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[QueryResult], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_sql", phase="error", span={"end_byte":31701,"end_column":1,"end_line":716,"start_byte":29997,"start_column":1,"start_line":682}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_EmptySql:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:2")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnterminatedSql:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:3")
    if type(_result) is Err and type(_result.error) is SqlClientError_ReadOnlyViolation:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:4")
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:5")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnsupportedValue:
        _cott_contract_condition(True, "real.harlequin.core.execute_sql", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            results = _cott_match_value.value
            return (_cott_contract_condition(((len(results) > 0)), "real.harlequin.core.execute_sql", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.execute_sql", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_sql", clause="ensures:1", phase="ensures", span={"end_byte":31454,"end_column":50,"end_line":706,"start_byte":31409,"start_column":5,"start_line":706}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[QueryResult], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]:
    """Run SQL on the connection's retained live session. Split sql with
real.harlequin.core.split_statements and propagate its errors unchanged. Then
validate and lock connection.session; a closed or malformed session is
ExecutionFailed for the first statement with a fixed message. Never reconnect
using endpoint or a string id.
Before running anything, check the statements in order. A statement whose first
keyword, ignoring comments and ASCII case, is BEGIN, START, COMMIT, ROLLBACK,
SAVEPOINT, RELEASE, END or ABORT is ExecutionFailed with a fixed message:
transaction ownership belongs to the explicit lease API. On a read-only
connection a statement whose first keyword is not SELECT, WITH, VALUES, SHOW,
DESCRIBE, DESC, EXPLAIN, MATCH, GO, FETCH or LOOKUP is ReadOnlyViolation(statement);
the driver's own read-only controls stay active as well.
Then execute the statements in order through the retained driver itself, in the
session's current transaction, stopping at the first failure. With an active
lease nothing is committed or rolled back here: later statements and calls see
the effects, and rollback_transaction undoes them. Without a lease, PostgreSQL,
MySQL, ODBC and ADBC commit each successful statement and roll back a failed one,
so earlier statements stay committed; SQLite and DuckDB use autocommit mode.
Fetch at most maximum_rows+1 rows per statement; more than maximum_rows rows is
ResultLimitExceeded(limit=maximum_rows), not a truncated success. Column names
and rows keep driver order; affected_rows is the driver's nonnegative row count
or -1. QueryBatch holds the exact split strings and one QueryResult per statement.
Convert null to Cell.Null, bool to Integer(0/1), signed-I64 integers to Integer,
finite floats to Real, strings to Text and bytes, bytearray or memoryview to
Blob. Decimal, date, time, datetime, timedelta and UUID values become Text of
their str() form; other values, out-of-range integers and non-finite floats are
UnsupportedValue(type name).
Use DBAPI cursors for the SQL adapters, BigQuery query(...).result(), Cassandra
Session.execute, and NebulaGraph Session.execute/as_primitive with checked
success status. Close cursors/results, but never the borrowed session.
Driver failures are ExecutionFailed(statement, fixed message); an actual
cancellation is Cancelled."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    sql = _cott_validate_abi(sql, str, path="$.sql")
    maximum_rows = _cott_validate_abi(maximum_rows, U32, path="$.maximum_rows")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/execute_statements.py", "c8d9185ae7ed5c908d022f9f84e83fc4ecb35573d83e4c604679fc2a958c7bc7", "execute_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.execute_statements")
        _result = _implementation(connection, sql, maximum_rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.execute_statements"
        if _error.span is None:
            _error.span = {"end_byte":35107,"end_column":1,"end_line":776,"start_byte":31985,"start_column":1,"start_line":723}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.execute_statements", phase="implementation-call", span={"end_byte":35107,"end_column":1,"end_line":776,"start_byte":31985,"start_column":1,"start_line":723}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.execute_statements", phase="implementation-call", span={"end_byte":35107,"end_column":1,"end_line":776,"start_byte":31985,"start_column":1,"start_line":723}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[QueryBatch, SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.execute_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_ExecutionFailed, SqlClientError_ResultLimitExceeded, SqlClientError_Cancelled, SqlClientError_UnsupportedValue,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.execute_statements", phase="error", span={"end_byte":35107,"end_column":1,"end_line":776,"start_byte":31985,"start_column":1,"start_line":723}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.execute_statements", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_EmptySql:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:3")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnterminatedSql:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:4")
    if type(_result) is Err and type(_result.error) is SqlClientError_ReadOnlyViolation:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:5")
    if type(_result) is Err and type(_result.error) is SqlClientError_ExecutionFailed:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:6")
    if type(_result) is Err and type(_result.error) is SqlClientError_ResultLimitExceeded:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:7")
    if type(_result) is Err and type(_result.error) is SqlClientError_Cancelled:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:8")
    if type(_result) is Err and type(_result.error) is SqlClientError_UnsupportedValue:
        _cott_contract_condition(True, "real.harlequin.core.execute_statements", "error:9")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            batch = _cott_match_value.value
            return (_cott_contract_condition((((len((batch).statements) == len((batch).results)) and (len((batch).results) > 0))), "real.harlequin.core.execute_statements", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.execute_statements", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_statements", clause="ensures:1", phase="ensures", span={"end_byte":34678,"end_column":100,"end_line":763,"start_byte":34583,"start_column":5,"start_line":763}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is SqlClientError_ResultLimitExceeded and True:
            limit = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((limit == maximum_rows)), "real.harlequin.core.execute_statements", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.execute_statements", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.execute_statements", clause="ensures:2", phase="ensures", span={"end_byte":34769,"end_column":91,"end_line":764,"start_byte":34683,"start_column":5,"start_line":764}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[QueryBatch, SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]:
    """Read a query file as UTF-8 text and return its complete decoded source. Local
reads the file at path. S3 gets the object key from bucket with boto3 and its
default credential and region configuration.
A missing file, bucket or key is NotFound(reference); an access refusal is
PermissionDenied(reference); bytes that are not UTF-8 are
InvalidEncoding(reference); any other I/O, transport or service failure is
TransferFailed(reference, message) with a fixed message that contains no
credential or service response text.
The local path is read from the file system the program runs against: the fs
fixture root while a Cott scenario with an fs fixture is active, otherwise the
host file system. While such a fixture is active the host file system is never
used, even when the fixture read fails."""
    reference = _cott_validate_abi(reference, FileReference, path="$.reference")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/load_query_file.py", "39c1fc4828e2f7735b207abae214b140a2f2d243eebd06b3e49aa9f94be9a4d2", "load_query_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.load_query_file")
        _result = _implementation(reference)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.load_query_file"
        if _error.span is None:
            _error.span = {"end_byte":37391,"end_column":1,"end_line":821,"start_byte":35881,"start_column":1,"start_line":792}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.load_query_file", phase="implementation-call", span={"end_byte":37391,"end_column":1,"end_line":821,"start_byte":35881,"start_column":1,"start_line":792}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.load_query_file", phase="implementation-call", span={"end_byte":37391,"end_column":1,"end_line":821,"start_byte":35881,"start_column":1,"start_line":792}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LoadedFile, FileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.load_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileError_NotFound, FileError_PermissionDenied, FileError_InvalidEncoding, FileError_TransferFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.load_query_file", phase="error", span={"end_byte":37391,"end_column":1,"end_line":821,"start_byte":35881,"start_column":1,"start_line":792}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.load_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is FileError_NotFound:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:6")
    if type(_result) is Err and type(_result.error) is FileError_PermissionDenied:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:7")
    if type(_result) is Err and type(_result.error) is FileError_InvalidEncoding:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:8")
    if type(_result) is Err and type(_result.error) is FileError_TransferFailed:
        _cott_contract_condition(True, "real.harlequin.core.load_query_file", "error:9")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (_cott_contract_condition((((loaded).reference == reference)), "real.harlequin.core.load_query_file", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.load_query_file", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:1", phase="ensures", span={"end_byte":36885,"end_column":63,"end_line":808,"start_byte":36827,"start_column":5,"start_line":808}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_NotFound and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == reference)), "real.harlequin.core.load_query_file", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.load_query_file", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:2", phase="ensures", span={"end_byte":36961,"end_column":76,"end_line":809,"start_byte":36890,"start_column":5,"start_line":809}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_PermissionDenied and True:
            denied = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((denied == reference)), "real.harlequin.core.load_query_file", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.load_query_file", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:3", phase="ensures", span={"end_byte":37043,"end_column":82,"end_line":810,"start_byte":36966,"start_column":5,"start_line":810}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_InvalidEncoding and True:
            undecodable = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((undecodable == reference)), "real.harlequin.core.load_query_file", "ensures:4"))
        _cott_contract_condition((False), "real.harlequin.core.load_query_file", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:4", phase="ensures", span={"end_byte":37134,"end_column":91,"end_line":811,"start_byte":37048,"start_column":5,"start_line":811}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_TransferFailed and True and True:
            failed = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((failed == reference)), "real.harlequin.core.load_query_file", "ensures:5"))
        _cott_contract_condition((False), "real.harlequin.core.load_query_file", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.load_query_file", clause="ensures:5", phase="ensures", span={"end_byte":37217,"end_column":83,"end_line":812,"start_byte":37139,"start_column":5,"start_line":812}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LoadedFile, FileError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]:
    """Write source as UTF-8 text. A reference that is not writable is
PermissionDenied(reference) before any I/O. Local writes a temporary file in the
same directory and atomically replaces path with it, creating or replacing the
file; a failed write leaves any previous file unchanged and removes the
temporary file. S3 puts the object key into bucket with boto3.
bytes_written is the UTF-8 byte length of source. An access refusal is
PermissionDenied(reference); any other failure, including a missing directory,
is TransferFailed(reference, message) with a fixed message that contains no
credential or service response text.
The local path is replaced in the file system the program runs against: the fs
fixture root while a Cott scenario with an fs fixture is active, otherwise the
host file system; the replacement is atomic in both. While such a fixture is
active the host file system is never used, even when the fixture write fails."""
    reference = _cott_validate_abi(reference, FileReference, path="$.reference")
    source = _cott_validate_abi(source, str, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((not (reference).writable)), "real.harlequin.core.save_query_file", "error:4:condition")):
        _expected_error = FileError_PermissionDenied
        _expected_error_span = {"end_byte":38819,"end_column":65,"end_line":842,"start_byte":38759,"start_column":5,"start_line":842}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/save_query_file.py", "4741b786b52706caf2d57f0dea169117f9f93bd62643485e739a435126060fc7", "save_query_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.save_query_file")
        _result = _implementation(reference, source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.save_query_file"
        if _error.span is None:
            _error.span = {"end_byte":38928,"end_column":1,"end_line":848,"start_byte":37391,"start_column":1,"start_line":821}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.core.save_query_file", phase="implementation-call", span={"end_byte":38928,"end_column":1,"end_line":848,"start_byte":37391,"start_column":1,"start_line":821}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.save_query_file", phase="implementation-call", span={"end_byte":38928,"end_column":1,"end_line":848,"start_byte":37391,"start_column":1,"start_line":821}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[SavedFile, FileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.core.save_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileError_PermissionDenied, FileError_TransferFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.core.save_query_file", phase="error", span={"end_byte":38928,"end_column":1,"end_line":848,"start_byte":37391,"start_column":1,"start_line":821}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.core.save_query_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.core.save_query_file", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is FileError_PermissionDenied:
        _cott_contract_condition(True, "real.harlequin.core.save_query_file", "error:5")
    if type(_result) is Err and type(_result.error) is FileError_TransferFailed:
        _cott_contract_condition(True, "real.harlequin.core.save_query_file", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition(((((saved).reference == reference) and ((saved).bytes_written >= len(source)))), "real.harlequin.core.save_query_file", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.core.save_query_file", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.save_query_file", clause="ensures:1", phase="ensures", span={"end_byte":38588,"end_column":99,"end_line":838,"start_byte":38494,"start_column":5,"start_line":838}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_PermissionDenied and True:
            denied = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((denied == reference)), "real.harlequin.core.save_query_file", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.core.save_query_file", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.save_query_file", clause="ensures:2", phase="ensures", span={"end_byte":38670,"end_column":82,"end_line":839,"start_byte":38593,"start_column":5,"start_line":839}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_TransferFailed and True and True:
            failed = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((failed == reference)), "real.harlequin.core.save_query_file", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.core.save_query_file", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.core.save_query_file", clause="ensures:3", phase="ensures", span={"end_byte":38753,"end_column":83,"end_line":840,"start_byte":38675,"start_column":5,"start_line":840}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[SavedFile, FileError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """The command-line composition root: parse, compose the facades below, print, exit.
1. real.harlequin.core.parse_cli(arguments); an error exits with status 2.
2. With options.no_config the configuration is empty (no profiles, no
default_profile, theme "harlequin", keymap "default") and no file is read.
Otherwise real.harlequin.core.load_configuration(Path(".harlequin.toml")) in the
current directory; Missing means the empty configuration, any other error exits
with status 2.
3. real.harlequin.core.resolve_profile(configuration, options); an error exits
with status 2.
4. real.harlequin.core.connect(request); an error exits with status 1. After a
successful connect, real.harlequin.core.disconnect runs exactly once before exit
on every path; its failure makes a zero exit status 1.
5. Batch mode, when options.query_file is Some(path):
real.harlequin.core.load_query_file(FileReference(location=Local(path),
writable=false)), then one real.harlequin.core.execute_statements(connection,
source, 1000); print its results and exit 0, or exit 1 on a file or SQL error.
No prompt is shown and nothing is read from stdin.
6. Interactive mode otherwise: write "sql> " to stdout and read one stdin line;
stop at end of input or at a line equal to ".quit" after removing surrounding
whitespace; skip blank lines; run every other line with
real.harlequin.core.execute_statements(connection, line, 1000) and print its
results, or print its error and continue with the next line. Exit 0 at the end.
Printing a QueryResult: with columns, one line of column names and then one line
per row, fields separated by TAB; a cell prints as NULL, the decimal integer, the
float's Python repr, the text, or 0x followed by lowercase hexadecimal for a
blob; TAB, LF, CR and backslash in names and text print as \\t, \\n, \\r and \\\\.
Without columns it prints "OK" when affected_rows is negative, else
"OK, N rows affected".
Each error prints one stderr line "harlequin: " followed by a fixed description
of the error variant; only CliError, ConfigurationError and SqlClientError
payload text (arguments, option names, paths, profile names, statements,
delimiters, type names, limits) may follow. Endpoints, credentials, opaque
values and driver messages are never printed."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/core/run.py", "f63dd18a336d725b4951d5e2becbc6ea58034e4e803c7ac7db327fe8244540e6", "run", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.core.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.core.run"
        if _error.span is None:
            _error.span = {"end_byte":41643,"end_column":1,"end_line":891,"start_byte":39114,"start_column":1,"start_line":852}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.core.run", phase="implementation-call", span={"end_byte":41643,"end_column":1,"end_line":891,"start_byte":39114,"start_column":1,"start_line":852}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.harlequin.core.run", phase="return", span={"end_byte":41643,"end_column":1,"end_line":891,"start_byte":39114,"start_column":1,"start_line":852}, expected="Never", actual=repr(_result))

__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionError_LeaseRejected", "ConnectionError_TransactionsUnsupported", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_TabMissing", "SessionHandle", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TransactionLease", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Committed", "TransactionStatus_RolledBack", "TypedRow", "activate_query_tab", "adapter_descriptors", "add_query_tab", "append_query_history", "begin_transaction", "close_query_tab", "commit_transaction", "connect", "disconnect", "edit_query_tab", "execute_sql", "execute_statements", "load_configuration", "load_query_file", "open_query_tab", "parse_cli", "resolve_profile", "rollback_transaction", "run", "save_query_file", "split_statements", "start_session"]
