from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""AdapterKind selects the driver and the interpretation of Connection.endpoint.
Use the project's lock-selected SDKs, not a fabricated Cott adapter or raw wire
protocol. JSON endpoint forms below are ordinary JSON objects, without a prefix;
reject unknown keys and values of the wrong type. Credentials are connection data,
never SQL text, public identifiers, or diagnostic messages.

Sqlite: sqlite3; endpoint is a filesystem path, a native file: URI, or :memory:.
DuckDb: duckdb; endpoint is a filesystem path or :memory:.
PostgreSql: psycopg; endpoint is a native libpq connection string or postgresql:
URI, passed as connection data rather than parsed as SQL.
MySql: pymysql; endpoint is JSON with required host, user, database strings,
optional password string, port integer (default 3306), and optional unix_socket,
ssl_ca, ssl_cert, ssl_key strings. TLS verification uses ssl_verify_cert and
ssl_verify_identity booleans (both default true when TLS is configured).
ODBC: pyodbc; endpoint is a native ODBC connection string or DSN specification.
BigQuery: google.cloud.bigquery; endpoint is JSON with required project string,
optional dataset and location strings, and auth={"type":"adc"}. Use the SDK's
Application Default Credentials; no custom credential loader is implied.
Trino: trino.dbapi; endpoint is JSON with required host and user strings, optional
catalog and schema strings, scheme ("https" by default or "http"), and port
(default 443 for https, 80 for http). Optional auth is
{"type":"basic","password":string}; BasicAuthentication requires https.
Databricks: databricks.sql; endpoint is JSON with required server_hostname and
http_path strings, auth={"type":"pat","access_token":string}, and optional catalog
and schema strings. Use the normal SQL connector, not an unselected SDK extra.
Cassandra: cassandra.cluster; endpoint is JSON with required nonempty contact_points
list of {"host":string,"port":integer} objects, optional keyspace string, and
optional auth={"type":"plain","username":string,"password":string}.
NebulaGraph: nebula3; endpoint is JSON with required nonempty addresses list of
{"host":string,"port":integer} objects, username and password strings, and optional
space string. Use ConnectionPool with the SDK's Config, not an HTTP/SQL adapter.
Adbc: adbc_driver_manager; endpoint is JSON with required driver string naming a
trusted deployment-installed ADBC driver library or manifest. Optional uri and
entrypoint are strings; db and connection are string-to-string driver option maps;
catalog is an optional exact metadata catalog selector. The manager is not itself
a database driver. Driver options contain no application SQL to execute."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_DuckDb:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_Sqlite:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_PostgreSql:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_MySql:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_Odbc:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_BigQuery:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_Trino:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_Databricks:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_Adbc:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_Cassandra:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterKind_NebulaGraph:
    pass

AdapterKind: TypeAlias = Union[AdapterKind_DuckDb, AdapterKind_Sqlite, AdapterKind_PostgreSql, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_BigQuery, AdapterKind_Trino, AdapterKind_Databricks, AdapterKind_Adbc, AdapterKind_Cassandra, AdapterKind_NebulaGraph]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterDescriptor:
    __hash__ = None
    kind: AdapterKind
    display_name: str
    uri_schemes: CottList[str]
    supports_transactions: bool
    supports_catalog: bool
    supports_files: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, AdapterKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "display_name", _cott_validate_abi(self.display_name, str, path="$.display_name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "uri_schemes", _cott_validate_abi(self.uri_schemes, CottList[str], path="$.uri_schemes"))
        if not _cott_validated_construction():
            object.__setattr__(self, "supports_transactions", _cott_validate_abi(self.supports_transactions, bool, path="$.supports_transactions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "supports_catalog", _cott_validate_abi(self.supports_catalog, bool, path="$.supports_catalog"))
        if not _cott_validated_construction():
            object.__setattr__(self, "supports_files", _cott_validate_abi(self.supports_files, bool, path="$.supports_files"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Setting:
    __hash__ = None
    name: str
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionProfile:
    __hash__ = None
    name: str
    adapter: AdapterKind
    endpoint: str
    settings: CottList[Setting]
    read_only: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, AdapterKind, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "endpoint", _cott_validate_abi(self.endpoint, str, path="$.endpoint"))
        if not _cott_validated_construction():
            object.__setattr__(self, "settings", _cott_validate_abi(self.settings, CottList[Setting], path="$.settings"))
        if not _cott_validated_construction():
            object.__setattr__(self, "read_only", _cott_validate_abi(self.read_only, bool, path="$.read_only"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration:
    __hash__ = None
    profiles: CottList[ConnectionProfile]
    default_profile: Option[str]
    theme: str
    keymap: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "profiles", _cott_validate_abi(self.profiles, CottList[ConnectionProfile], path="$.profiles"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default_profile", _cott_validate_abi(self.default_profile, Option[str], path="$.default_profile"))
        if not _cott_validated_construction():
            object.__setattr__(self, "theme", _cott_validate_abi(self.theme, str, path="$.theme"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keymap", _cott_validate_abi(self.keymap, str, path="$.keymap"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliOptions:
    __hash__ = None
    profile: Option[str]
    adapter: Option[AdapterKind]
    connection: Option[str]
    query_file: Option[Path]
    read_only: bool
    no_config: bool
    source_argument_count: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "profile", _cott_validate_abi(self.profile, Option[str], path="$.profile"))
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, Option[AdapterKind], path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, Option[str], path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query_file", _cott_validate_abi(self.query_file, Option[Path], path="$.query_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "read_only", _cott_validate_abi(self.read_only, bool, path="$.read_only"))
        if not _cott_validated_construction():
            object.__setattr__(self, "no_config", _cott_validate_abi(self.no_config, bool, path="$.no_config"))
        if not _cott_validated_construction():
            object.__setattr__(self, "source_argument_count", _cott_validate_abi(self.source_argument_count, U64, path="$.source_argument_count"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionRequest:
    __hash__ = None
    adapter: AdapterKind
    endpoint: str
    settings: CottList[Setting]
    read_only: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, AdapterKind, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "endpoint", _cott_validate_abi(self.endpoint, str, path="$.endpoint"))
        if not _cott_validated_construction():
            object.__setattr__(self, "settings", _cott_validate_abi(self.settings, CottList[Setting], path="$.settings"))
        if not _cott_validated_construction():
            object.__setattr__(self, "read_only", _cott_validate_abi(self.read_only, bool, path="$.read_only"))

"""One process-local live session, created only by connect and explicitly closed by
disconnect. It is not a serialized identifier or a global-registry key. The opaque
payload is a shared dict[str, object] with exactly these keys: id, adapter, endpoint,
read_only, driver, cleanup, lock, closed, transaction. The first four equal the
Connection metadata; driver is the actual SDK connection/client/session; cleanup
is a contextlib.ExitStack of actual close/release callbacks; lock is threading.Lock;
closed is initially false; transaction is initially None or the currently active
lease's unique object. No other mutable registry or module-global session exists.
The dictionary and lock are shared by all copies of this handle, not cloned.
Check the tag, complete shape, metadata equality and concrete SDK driver type before
using it. Acquire lock before testing closed/transaction or touching the driver.
Malformed, metadata-mismatched, closed or stale handles cause the operation's
declared error, never a new connection opened from endpoint. Opaque is a typed
host-handle carrier, not a cryptographic seal or a way to serialize a session."""
SessionHandle: TypeAlias = Opaque[Literal["harlequin.session"]]

"""An explicit connection owner. Call disconnect exactly once when finished; repeated
disconnect is harmless. Other operations borrow this exact live session and never
transfer its ownership or close it. endpoint contains the effective connection
options after settings overrides. Do not log endpoint, opaque values or credentials."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Connection:
    __hash__ = None
    id: str
    adapter: AdapterKind
    endpoint: str
    read_only: bool
    session: Opaque[Literal["harlequin.session"]]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, AdapterKind, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "endpoint", _cott_validate_abi(self.endpoint, str, path="$.endpoint"))
        if not _cott_validated_construction():
            object.__setattr__(self, "read_only", _cott_validate_abi(self.read_only, bool, path="$.read_only"))
        if not _cott_validated_construction():
            object.__setattr__(self, "session", _cott_validate_abi(self.session, Opaque[Literal["harlequin.session"]], path="$.session"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryTab:
    __hash__ = None
    id: str
    title: str
    source: str
    cursor: U64
    dirty: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dirty", _cott_validate_abi(self.dirty, bool, path="$.dirty"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryHistoryEntry:
    __hash__ = None
    source: str
    executed_at: str
    succeeded: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "executed_at", _cott_validate_abi(self.executed_at, str, path="$.executed_at"))
        if not _cott_validated_construction():
            object.__setattr__(self, "succeeded", _cott_validate_abi(self.succeeded, bool, path="$.succeeded"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryHistory:
    __hash__ = None
    entries: CottList[QueryHistoryEntry]
    capacity: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "entries", _cott_validate_abi(self.entries, CottList[QueryHistoryEntry], path="$.entries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "capacity", _cott_validate_abi(self.capacity, U64, path="$.capacity"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class IdeSession:
    __hash__ = None
    connection: Connection
    tabs: CottList[QueryTab]
    active_tab_id: Option[str]
    history: QueryHistory

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, Connection, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tabs", _cott_validate_abi(self.tabs, CottList[QueryTab], path="$.tabs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "active_tab_id", _cott_validate_abi(self.active_tab_id, Option[str], path="$.active_tab_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "history", _cott_validate_abi(self.history, QueryHistory, path="$.history"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileReference:
    __hash__ = None
    location: FileLocation
    writable: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "location", _cott_validate_abi(self.location, FileLocation, path="$.location"))
        if not _cott_validated_construction():
            object.__setattr__(self, "writable", _cott_validate_abi(self.writable, bool, path="$.writable"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileLocation_Local:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileLocation_S3:
    __hash__ = None
    bucket: str
    key: str

FileLocation: TypeAlias = Union[FileLocation_Local, FileLocation_S3]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseTarget_Memory:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseTarget_File:
    __hash__ = None
    path: Path

DatabaseTarget: TypeAlias = Union[DatabaseTarget_Memory, DatabaseTarget_File]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Null:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Integer:
    __hash__ = None
    value: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Real:
    __hash__ = None
    value: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Text:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Blob:
    __hash__ = None
    value: bytes

Cell: TypeAlias = Union[Cell_Null, Cell_Integer, Cell_Real, Cell_Text, Cell_Blob]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypedRow:
    __hash__ = None
    values: CottList[Cell]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "values", _cott_validate_abi(self.values, CottList[Cell], path="$.values"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryResult:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[TypedRow]
    affected_rows: I64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[TypedRow], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "affected_rows", _cott_validate_abi(self.affected_rows, I64, path="$.affected_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryBatch:
    __hash__ = None
    statements: CottList[str]
    results: CottList[QueryResult]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "statements", _cott_validate_abi(self.statements, CottList[str], path="$.statements"))
        if not _cott_validated_construction():
            object.__setattr__(self, "results", _cott_validate_abi(self.results, CottList[QueryResult], path="$.results"))

"""Lease identity for one transaction on one SessionHandle. Its opaque value is a
fresh unique object, compared by identity against session payload transaction.
No lookup by connection id and no driver reconnection is permitted."""
TransactionLease: TypeAlias = Opaque[Literal["harlequin.transaction"]]

"""An immutable snapshot containing its actual owning connection and lease.
active is a result-state snapshot, not authority: even an old active=True copy
cannot commit or roll back after its lease has completed or its connection closed."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Transaction:
    __hash__ = None
    connection: Connection
    lease: Opaque[Literal["harlequin.transaction"]]
    active: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, Connection, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "lease", _cott_validate_abi(self.lease, Opaque[Literal["harlequin.transaction"]], path="$.lease"))
        if not _cott_validated_construction():
            object.__setattr__(self, "active", _cott_validate_abi(self.active, bool, path="$.active"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedFile:
    __hash__ = None
    reference: FileReference
    source: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "reference", _cott_validate_abi(self.reference, FileReference, path="$.reference"))
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SavedFile:
    __hash__ = None
    reference: FileReference
    bytes_written: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "reference", _cott_validate_abi(self.reference, FileReference, path="$.reference"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bytes_written", _cott_validate_abi(self.bytes_written, U64, path="$.bytes_written"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliError_UnknownOption:
    __hash__ = None
    argument: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliError_MissingOptionValue:
    __hash__ = None
    option: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliError_InvalidAdapter:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliError_ConflictingConnectionInputs:
    pass

CliError: TypeAlias = Union[CliError_UnknownOption, CliError_MissingOptionValue, CliError_InvalidAdapter, CliError_ConflictingConnectionInputs]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigurationError_Missing:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigurationError_Invalid:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigurationError_ProfileMissing:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigurationError_ProfileDuplicate:
    __hash__ = None
    name: str

ConfigurationError: TypeAlias = Union[ConfigurationError_Missing, ConfigurationError_Invalid, ConfigurationError_ProfileMissing, ConfigurationError_ProfileDuplicate]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_AdapterUnavailable:
    __hash__ = None
    adapter: AdapterKind

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_InvalidEndpoint:
    __hash__ = None
    endpoint: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_AuthenticationFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_Failed:
    __hash__ = None
    message: str

ConnectionError: TypeAlias = Union[ConnectionError_AdapterUnavailable, ConnectionError_InvalidEndpoint, ConnectionError_AuthenticationFailed, ConnectionError_Failed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionError_TabMissing:
    __hash__ = None
    tab_id: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionError_HistoryCapacityInvalid:
    pass

SessionError: TypeAlias = Union[SessionError_TabMissing, SessionError_HistoryCapacityInvalid]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_NotFound:
    __hash__ = None
    reference: FileReference

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_PermissionDenied:
    __hash__ = None
    reference: FileReference

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_InvalidEncoding:
    __hash__ = None
    reference: FileReference

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_TransferFailed:
    __hash__ = None
    reference: FileReference
    message: str

FileError: TypeAlias = Union[FileError_NotFound, FileError_PermissionDenied, FileError_InvalidEncoding, FileError_TransferFailed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_EmptySql:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_UnterminatedSql:
    __hash__ = None
    delimiter: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_ReadOnlyViolation:
    __hash__ = None
    statement: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_SqliteFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_UnsupportedValue:
    __hash__ = None
    type_name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_ExecutionFailed:
    __hash__ = None
    statement: str
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_ResultLimitExceeded:
    __hash__ = None
    limit: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_Cancelled:
    pass

SqlClientError: TypeAlias = Union[SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_ExecutionFailed, SqlClientError_ResultLimitExceeded, SqlClientError_Cancelled]

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
"""Use tomllib; cast each dict/list to dict[str, object]/list[object] before use."""
"""Use isinstance, not match, for each Option; select the named or default profile."""
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
"""Validate SessionHandle and lock it. If already closed, return Unit successfully.
Otherwise invalidate the active lease and mark closed before cleanup, so no
stale handle can regain authority even if the SDK reports a close failure.
Roll back an outstanding supported transaction on this same driver, then close
the ExitStack so every registered callback is attempted. Do not commit or
reopen any connection. Cleanup failure returns Failed with a fixed message;
success returns Unit. No resource is transferred to a hidden registry."""
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
"""Borrow transaction.connection and acquire its session lock. Require active=true,
an open matching SessionHandle, and exact lease object identity with its active
transaction. Reject a stale, already-finished, disconnected or wrong-owner
lease as Failed without touching a different session.
Call the actual existing SDK driver's commit. Never reconnect by id/endpoint.
On success clear the active lease and return the same connection and lease
with active=false. On a driver failure, clear the lease, mark the session closed,
attempt rollback and every registered cleanup callback, and return Failed with
a fixed nonsecret message; do not leave an ambiguously reusable transaction."""
"""Apply the same ownership and live-lease requirements as commit_transaction,
but call the existing SDK driver's rollback. Success clears the active lease
and returns the same connection and lease with active=false. Double completion,
stale leases and disconnected sessions are Failed, never successful no-ops.
A driver failure clears the lease, marks the session closed, attempts all
cleanup callbacks and returns Failed with a fixed nonsecret message."""
"""Use isinstance checks, not match, for active_tab_id."""
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
"""Set sdk: Any = boto3; client: Any = sdk.client("s3"); decode Body to source: str."""
"""Parse/connect; read SQL at sql> until .quit/EOF; execute and print tab-separated results."""
__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_HistoryCapacityInvalid", "SessionError_TabMissing", "SessionHandle", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TransactionLease", "TypedRow"]
