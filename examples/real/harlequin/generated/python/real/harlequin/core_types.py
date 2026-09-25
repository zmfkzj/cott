from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""AdapterKind selects the driver and the interpretation of a connection endpoint.
Each adapter uses the named lock-selected SDK; no raw wire protocol or invented
adapter layer replaces it. JSON endpoint forms below are ordinary JSON objects,
without a prefix; unknown keys and values of the wrong type are invalid.
Credentials are connection data, never SQL text, public identifiers, or diagnostic
messages.

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
catalog is an optional exact catalog selector used only by catalog refresh. The
manager is not itself a database driver. Driver options contain no application SQL
to execute."""
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

"""Parsed command line. connection is the positional connection string (endpoint
text); query_file is the --query-file path. read_only and no_config are the
--read-only and --no-config switches."""
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
closed is initially false; transaction is None or the unwrapped object of the
currently active TransactionLease. No other mutable registry or module-global
session exists. The dictionary and lock are shared by all copies of this handle,
not cloned. Check the tag, complete shape, metadata equality and concrete SDK driver
type before using it. Acquire lock before testing closed/transaction or touching
the driver. Malformed, metadata-mismatched, closed or stale handles cause the
operation's declared error, never a new connection opened from endpoint. Opaque is
a typed host-handle carrier, not a cryptographic seal or a way to serialize a
session."""
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

"""An editor tab. cursor counts Unicode scalar values into source; dirty means the
source was edited since the tab was opened."""
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

"""Executed queries, oldest first, holding at most capacity entries. Capacity zero
keeps no history."""
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
        if not (_cott_contract_condition(((len((self).entries) <= (self).capacity)), "real.harlequin.core.QueryHistory", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.harlequin.core.QueryHistory", clause="invariant:0", phase="invariant", span={"end_byte":6120,"end_column":48,"end_line":156,"start_byte":6077,"start_column":5,"start_line":156}, expected="true", actual="false")

"""Editor state for one connection, identified by that connection's id. Tab ids are
unique; active_tab_id names one of the tabs or is Nothing."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class IdeSession:
    __hash__ = None
    connection_id: str
    tabs: CottList[QueryTab]
    active_tab_id: Option[str]
    history: QueryHistory

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection_id", _cott_validate_abi(self.connection_id, str, path="$.connection_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tabs", _cott_validate_abi(self.tabs, CottList[QueryTab], path="$.tabs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "active_tab_id", _cott_validate_abi(self.active_tab_id, Option[str], path="$.active_tab_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "history", _cott_validate_abi(self.history, QueryHistory, path="$.history"))
        if not (_cott_contract_condition((_cott_unique_by((self).tabs, "id")), "real.harlequin.core.IdeSession", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.harlequin.core.IdeSession", clause="invariant:0", phase="invariant", span={"end_byte":6446,"end_column":48,"end_line":168,"start_byte":6403,"start_column":5,"start_line":168}, expected="true", actual="false")

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

"""Lease identity for one transaction on one SessionHandle. Its opaque value is a fresh
unique object that begin_transaction also stores, unwrapped, as the session payload
transaction. A lease has authority exactly while that payload entry is the same
object (identity, `is`) as the lease's unwrapped value; the Opaque wrapper itself is
not the identity and may be rebuilt at facade boundaries. No lookup by connection
id and no driver reconnection is permitted."""
TransactionLease: TypeAlias = Opaque[Literal["harlequin.transaction"]]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Active:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Committed:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_RolledBack:
    pass

TransactionStatus: TypeAlias = Union[TransactionStatus_Active, TransactionStatus_Committed, TransactionStatus_RolledBack]

"""An immutable snapshot of one lease and its actual owning connection. status is
Active in the snapshot begin_transaction returns and Committed or RolledBack in the
snapshot returned by the completing call. A snapshot is not authority: even an old
Active copy cannot commit or roll back after its lease has completed or its
connection closed."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Transaction:
    __hash__ = None
    connection: Connection
    lease: Opaque[Literal["harlequin.transaction"]]
    status: TransactionStatus

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, Connection, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "lease", _cott_validate_abi(self.lease, Opaque[Literal["harlequin.transaction"]], path="$.lease"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, TransactionStatus, path="$.status"))

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
class ConnectionError_TransactionsUnsupported:
    __hash__ = None
    adapter: AdapterKind

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_LeaseRejected:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_Failed:
    __hash__ = None
    message: str

ConnectionError: TypeAlias = Union[ConnectionError_AdapterUnavailable, ConnectionError_InvalidEndpoint, ConnectionError_AuthenticationFailed, ConnectionError_TransactionsUnsupported, ConnectionError_LeaseRejected, ConnectionError_Failed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionError_TabMissing:
    __hash__ = None
    tab_id: str

SessionError: TypeAlias = Union[SessionError_TabMissing]

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
"""Plan the connection request without I/O. With options.no_config the
configuration is ignored, as if it had no profiles and no default_profile.
The selected profile name is options.profile, else configuration.default_profile,
else none. A selected name without a profile of exactly that name is
ProfileMissing(name). With no selected name the base request is DuckDb, endpoint
":memory:", no settings and read_only false; otherwise it is the profile's
adapter, endpoint, settings and read_only. Then options.adapter replaces the
adapter, options.connection replaces the endpoint, and options.read_only true
makes the request read-only. Settings always come from the profile."""
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
"""Validate SessionHandle and lock it. If already closed, return Unit successfully.
Otherwise invalidate the active lease and mark closed before cleanup, so no
stale handle can regain authority even if the SDK reports a close failure.
Roll back an outstanding supported transaction on this same driver, then close
the ExitStack so every registered callback is attempted. Do not commit or
reopen any connection. Cleanup failure returns Failed with a fixed message;
success returns Unit. No resource is transferred to a hidden registry."""
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
"""Apply the same status and lease-authority checks as commit_transaction, with the
same LeaseRejected results, but call the existing SDK driver's rollback. Success
clears the active lease and returns the same connection and lease with
status=RolledBack. Double completion, stale leases and disconnected sessions are
never successful no-ops. A driver failure clears the lease, marks the session
closed, attempts all cleanup callbacks and returns Failed with a fixed nonsecret
message."""
"""Replace the tab's source and move its cursor, clamped to the end of source.
The tab becomes dirty when source differs from its previous source."""
"""Append entry as the newest entry; when history is full, drop the oldest entries
so that at most capacity remain."""
"""Start editor state for connection: no tabs, no active tab, empty history with
history_capacity."""
"""A tab with the same id is replaced in place; otherwise tab is appended.
The added tab becomes active."""
"""Make the tab with tab_id active. An unknown id is TabMissing(tab_id)."""
"""Remove the tab with tab_id, keeping the order of the others. When it was active,
the tab that followed it becomes active, else the tab that preceded it, else
none; otherwise the active tab is unchanged. An unknown id is TabMissing(tab_id)."""
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
__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionError_LeaseRejected", "ConnectionError_TransactionsUnsupported", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_TabMissing", "SessionHandle", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TransactionLease", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Committed", "TransactionStatus_RolledBack", "TypedRow"]
