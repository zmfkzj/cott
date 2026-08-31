from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
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

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Connection:
    __hash__ = None
    id: str
    adapter: AdapterKind
    endpoint: str
    read_only: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, AdapterKind, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "endpoint", _cott_validate_abi(self.endpoint, str, path="$.endpoint"))
        if not _cott_validated_construction():
            object.__setattr__(self, "read_only", _cott_validate_abi(self.read_only, bool, path="$.read_only"))

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

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Transaction:
    __hash__ = None
    connection_id: str
    active: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection_id", _cott_validate_abi(self.connection_id, str, path="$.connection_id"))
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

"""Use tomllib; cast each dict/list to dict[str, object]/list[object] before use."""
"""Use isinstance, not match, for each Option; select the named or default profile."""
"""Use isinstance checks, not match, for active_tab_id."""
"""Set sdk: Any = boto3; client: Any = sdk.client("s3"); decode Body to source: str."""
"""Parse/connect; read SQL at sql> until .quit/EOF; execute and print tab-separated results."""
__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_HistoryCapacityInvalid", "SessionError_TabMissing", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TypedRow"]
