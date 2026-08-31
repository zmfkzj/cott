from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_MissingDatabase:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_InvalidPort:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_InvalidDsn:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_ProfileMissing:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_TlsInvalid:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_SshInvalid:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_CredentialUnavailable:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_PromptDisabled:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_ConnectionFailed:
    __hash__ = None
    message: str

ConnectionError: TypeAlias = Union[ConnectionError_MissingDatabase, ConnectionError_InvalidPort, ConnectionError_InvalidDsn, ConnectionError_ProfileMissing, ConnectionError_TlsInvalid, ConnectionError_SshInvalid, ConnectionError_CredentialUnavailable, ConnectionError_PromptDisabled, ConnectionError_ConnectionFailed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseError_ConnectionFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseError_QueryFailed:
    __hash__ = None
    message: str

DatabaseError: TypeAlias = Union[DatabaseError_ConnectionFailed, DatabaseError_QueryFailed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_InvalidCommand:
    __hash__ = None
    source: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_InvalidSql:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_CatalogFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_QueryFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_TransactionFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_ImportFailed:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_ExportFailed:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_HistoryFailed:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_FavoriteFailed:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_EditorFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_PagerFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_NotificationFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_TerminalFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_UnsupportedFormat:
    __hash__ = None
    value: str

ClientError: TypeAlias = Union[ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_ImportFailed, ClientError_ExportFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_NotificationFailed, ClientError_TerminalFailed, ClientError_UnsupportedFormat]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionInputs:
    __hash__ = None
    host: str
    port: str
    user: str
    password: str
    database: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentInputs:
    __hash__ = None
    host: str
    port: str
    user: str
    password: str
    database: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSettings:
    __hash__ = None
    host: str
    port: str
    user: str
    password: str
    database: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsSettings:
    __hash__ = None
    mode: str
    root_certificate: Path
    certificate: Path
    private_key: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, str, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "root_certificate", _cott_validate_abi(self.root_certificate, Path, path="$.root_certificate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "certificate", _cott_validate_abi(self.certificate, Path, path="$.certificate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "private_key", _cott_validate_abi(self.private_key, Path, path="$.private_key"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SshSettings:
    __hash__ = None
    host: str
    port: U16
    user: str
    private_key: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, U16, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "private_key", _cott_validate_abi(self.private_key, Path, path="$.private_key"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionProfile:
    __hash__ = None
    name: str
    dsn: str
    inputs: ConnectionInputs
    tls: TlsSettings
    ssh: Option[SshSettings]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn", _cott_validate_abi(self.dsn, str, path="$.dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "inputs", _cott_validate_abi(self.inputs, ConnectionInputs, path="$.inputs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tls", _cott_validate_abi(self.tls, TlsSettings, path="$.tls"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh", _cott_validate_abi(self.ssh, Option[SshSettings], path="$.ssh"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionRequest:
    __hash__ = None
    dsn: str
    profile: str
    inputs: ConnectionInputs
    environment: EnvironmentInputs
    tls: TlsSettings
    ssh: Option[SshSettings]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn", _cott_validate_abi(self.dsn, str, path="$.dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "profile", _cott_validate_abi(self.profile, str, path="$.profile"))
        if not _cott_validated_construction():
            object.__setattr__(self, "inputs", _cott_validate_abi(self.inputs, ConnectionInputs, path="$.inputs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "environment", _cott_validate_abi(self.environment, EnvironmentInputs, path="$.environment"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tls", _cott_validate_abi(self.tls, TlsSettings, path="$.tls"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh", _cott_validate_abi(self.ssh, Option[SshSettings], path="$.ssh"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionPlan:
    __hash__ = None
    settings: ConnectionSettings
    dsn: str
    tls: TlsSettings
    ssh: Option[SshSettings]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "settings", _cott_validate_abi(self.settings, ConnectionSettings, path="$.settings"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn", _cott_validate_abi(self.dsn, str, path="$.dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tls", _cott_validate_abi(self.tls, TlsSettings, path="$.tls"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh", _cott_validate_abi(self.ssh, Option[SshSettings], path="$.ssh"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordSource_Supplied:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordSource_Environment:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordSource_Keyring:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordSource_Prompt:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordSource_None:
    pass

PasswordSource: TypeAlias = Union[PasswordSource_Supplied, PasswordSource_Environment, PasswordSource_Keyring, PasswordSource_Prompt, PasswordSource_None]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PromptAction_UsePassword:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PromptAction_PromptPassword:
    pass

PromptAction: TypeAlias = Union[PromptAction_UsePassword, PromptAction_PromptPassword]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CredentialRequest:
    __hash__ = None
    service: str
    user: str
    supplied_password: str
    environment_password: str
    no_prompt: bool
    use_keyring: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "service", _cott_validate_abi(self.service, str, path="$.service"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "supplied_password", _cott_validate_abi(self.supplied_password, str, path="$.supplied_password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "environment_password", _cott_validate_abi(self.environment_password, str, path="$.environment_password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "no_prompt", _cott_validate_abi(self.no_prompt, bool, path="$.no_prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "use_keyring", _cott_validate_abi(self.use_keyring, bool, path="$.use_keyring"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CredentialResolution:
    __hash__ = None
    password: str
    source: PasswordSource

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, PasswordSource, path="$.source"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ColumnCatalog:
    __hash__ = None
    name: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableCatalog:
    __hash__ = None
    schema: str
    name: str
    columns: CottList[ColumnCatalog]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "schema", _cott_validate_abi(self.schema, str, path="$.schema"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[ColumnCatalog], path="$.columns"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RelationCatalog:
    __hash__ = None
    schema: str
    name: str
    kind: str
    columns: CottList[ColumnCatalog]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "schema", _cott_validate_abi(self.schema, str, path="$.schema"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, str, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[ColumnCatalog], path="$.columns"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoutineCatalog:
    __hash__ = None
    schema: str
    name: str
    arguments: str
    result_type: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "schema", _cott_validate_abi(self.schema, str, path="$.schema"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "arguments", _cott_validate_abi(self.arguments, str, path="$.arguments"))
        if not _cott_validated_construction():
            object.__setattr__(self, "result_type", _cott_validate_abi(self.result_type, str, path="$.result_type"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Catalog:
    __hash__ = None
    databases: CottList[str]
    schemas: CottList[str]
    relations: CottList[RelationCatalog]
    routines: CottList[RoutineCatalog]
    roles: CottList[str]
    extensions: CottList[str]
    publications: CottList[str]
    subscriptions: CottList[str]
    refreshed_at_ms: U64
    limit: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "databases", _cott_validate_abi(self.databases, CottList[str], path="$.databases"))
        if not _cott_validated_construction():
            object.__setattr__(self, "schemas", _cott_validate_abi(self.schemas, CottList[str], path="$.schemas"))
        if not _cott_validated_construction():
            object.__setattr__(self, "relations", _cott_validate_abi(self.relations, CottList[RelationCatalog], path="$.relations"))
        if not _cott_validated_construction():
            object.__setattr__(self, "routines", _cott_validate_abi(self.routines, CottList[RoutineCatalog], path="$.routines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "roles", _cott_validate_abi(self.roles, CottList[str], path="$.roles"))
        if not _cott_validated_construction():
            object.__setattr__(self, "extensions", _cott_validate_abi(self.extensions, CottList[str], path="$.extensions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "publications", _cott_validate_abi(self.publications, CottList[str], path="$.publications"))
        if not _cott_validated_construction():
            object.__setattr__(self, "subscriptions", _cott_validate_abi(self.subscriptions, CottList[str], path="$.subscriptions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "refreshed_at_ms", _cott_validate_abi(self.refreshed_at_ms, U64, path="$.refreshed_at_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "limit", _cott_validate_abi(self.limit, U64, path="$.limit"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogRefreshRequest:
    __hash__ = None
    connection: ConnectionPlan
    include_system: bool
    limit: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, ConnectionPlan, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "include_system", _cott_validate_abi(self.include_system, bool, path="$.include_system"))
        if not _cott_validated_construction():
            object.__setattr__(self, "limit", _cott_validate_abi(self.limit, U64, path="$.limit"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionRequest:
    __hash__ = None
    source: str
    cursor: U64
    catalog: CottList[TableCatalog]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "catalog", _cott_validate_abi(self.catalog, CottList[TableCatalog], path="$.catalog"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionPolicy:
    __hash__ = None
    max_candidates: U64
    include_keywords: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "max_candidates", _cott_validate_abi(self.max_candidates, U64, path="$.max_candidates"))
        if not _cott_validated_construction():
            object.__setattr__(self, "include_keywords", _cott_validate_abi(self.include_keywords, bool, path="$.include_keywords"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionResult:
    __hash__ = None
    candidates: CottList[str]
    replace_start: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "candidates", _cott_validate_abi(self.candidates, CottList[str], path="$.candidates"))
        if not _cott_validated_construction():
            object.__setattr__(self, "replace_start", _cott_validate_abi(self.replace_start, U64, path="$.replace_start"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HighlightRequest:
    __hash__ = None
    source: str
    color: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "color", _cott_validate_abi(self.color, bool, path="$.color"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HighlightedSql:
    __hash__ = None
    text: str
    contains_error: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "contains_error", _cott_validate_abi(self.contains_error, bool, path="$.contains_error"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Horizontal:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Vertical:
    pass

RenderLayout: TypeAlias = Union[RenderLayout_Horizontal, RenderLayout_Vertical]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Aligned:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Csv:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Tsv:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Json:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_JsonLines:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Html:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Latex:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Markdown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableFormat_Vertical:
    pass

TableFormat: TypeAlias = Union[TableFormat_Aligned, TableFormat_Csv, TableFormat_Tsv, TableFormat_Json, TableFormat_JsonLines, TableFormat_Html, TableFormat_Latex, TableFormat_Markdown, TableFormat_Vertical]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderRequest:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[CottList[str]]
    terminal_width: U16
    vertical: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[CottList[str]], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_width", _cott_validate_abi(self.terminal_width, U16, path="$.terminal_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "vertical", _cott_validate_abi(self.vertical, bool, path="$.vertical"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatRequest:
    __hash__ = None
    query: QueryResult
    format: TableFormat
    terminal_width: U16
    max_column_width: U16
    max_rows: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, QueryResult, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, TableFormat, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_width", _cott_validate_abi(self.terminal_width, U16, path="$.terminal_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_column_width", _cott_validate_abi(self.max_column_width, U16, path="$.max_column_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_rows", _cott_validate_abi(self.max_rows, U64, path="$.max_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedQuery:
    __hash__ = None
    text: str
    layout: RenderLayout
    width: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "layout", _cott_validate_abi(self.layout, RenderLayout, path="$.layout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "width", _cott_validate_abi(self.width, U16, path="$.width"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormattedQuery:
    __hash__ = None
    rendered: RenderedQuery
    truncated_rows: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "rendered", _cott_validate_abi(self.rendered, RenderedQuery, path="$.rendered"))
        if not _cott_validated_construction():
            object.__setattr__(self, "truncated_rows", _cott_validate_abi(self.truncated_rows, U64, path="$.truncated_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryResult:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[CottList[str]]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[CottList[str]], path="$.rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutedQuery:
    __hash__ = None
    result: QueryResult
    status: str
    affected_rows: U64
    elapsed_ms: U64
    notices: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "result", _cott_validate_abi(self.result, QueryResult, path="$.result"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, str, path="$.status"))
        if not _cott_validated_construction():
            object.__setattr__(self, "affected_rows", _cott_validate_abi(self.affected_rows, U64, path="$.affected_rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "elapsed_ms", _cott_validate_abi(self.elapsed_ms, U64, path="$.elapsed_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "notices", _cott_validate_abi(self.notices, CottList[str], path="$.notices"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryRequest:
    __hash__ = None
    connection: ConnectionPlan
    sql: str
    max_rows: U64
    transaction: TransactionMode
    timing: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, ConnectionPlan, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, str, path="$.sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_rows", _cott_validate_abi(self.max_rows, U64, path="$.max_rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "transaction", _cott_validate_abi(self.transaction, TransactionMode, path="$.transaction"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timing", _cott_validate_abi(self.timing, bool, path="$.timing"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryPlan:
    __hash__ = None
    sql: str
    statement_count: U64
    requires_terminator: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, str, path="$.sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "statement_count", _cott_validate_abi(self.statement_count, U64, path="$.statement_count"))
        if not _cott_validated_construction():
            object.__setattr__(self, "requires_terminator", _cott_validate_abi(self.requires_terminator, bool, path="$.requires_terminator"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputBuffer:
    __hash__ = None
    text: str
    cursor: U64
    multiline: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multiline", _cott_validate_abi(self.multiline, bool, path="$.multiline"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EditorRequest:
    __hash__ = None
    buffer: InputBuffer
    editor: str
    temporary_path: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "buffer", _cott_validate_abi(self.buffer, InputBuffer, path="$.buffer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "editor", _cott_validate_abi(self.editor, str, path="$.editor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "temporary_path", _cott_validate_abi(self.temporary_path, Path, path="$.temporary_path"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PagerRequest:
    __hash__ = None
    text: str
    pager: str
    enabled: bool
    terminal_height: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pager", _cott_validate_abi(self.pager, str, path="$.pager"))
        if not _cott_validated_construction():
            object.__setattr__(self, "enabled", _cott_validate_abi(self.enabled, bool, path="$.enabled"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_height", _cott_validate_abi(self.terminal_height, U16, path="$.terminal_height"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryEntry:
    __hash__ = None
    sql: str
    executed_at_ms: U64
    database: str
    success: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, str, path="$.sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "executed_at_ms", _cott_validate_abi(self.executed_at_ms, U64, path="$.executed_at_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))
        if not _cott_validated_construction():
            object.__setattr__(self, "success", _cott_validate_abi(self.success, bool, path="$.success"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryPolicy:
    __hash__ = None
    path: Path
    max_entries: U64
    unique: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_entries", _cott_validate_abi(self.max_entries, U64, path="$.max_entries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "unique", _cott_validate_abi(self.unique, bool, path="$.unique"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Favorite:
    __hash__ = None
    name: str
    sql: str
    tags: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, str, path="$.sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tags", _cott_validate_abi(self.tags, CottList[str], path="$.tags"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FavoriteStore:
    __hash__ = None
    path: Path
    max_entries: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_entries", _cott_validate_abi(self.max_entries, U64, path="$.max_entries"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRequest:
    __hash__ = None
    sql: str
    target: Path
    format: TableFormat
    delimiter: str
    header: bool
    max_rows: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, str, path="$.sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "target", _cott_validate_abi(self.target, Path, path="$.target"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, TableFormat, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "delimiter", _cott_validate_abi(self.delimiter, str, path="$.delimiter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "header", _cott_validate_abi(self.header, bool, path="$.header"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_rows", _cott_validate_abi(self.max_rows, U64, path="$.max_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ImportRequest:
    __hash__ = None
    table: str
    source: Path
    delimiter: str
    header: bool
    null_text: str
    max_rows: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "table", _cott_validate_abi(self.table, str, path="$.table"))
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, Path, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "delimiter", _cott_validate_abi(self.delimiter, str, path="$.delimiter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "header", _cott_validate_abi(self.header, bool, path="$.header"))
        if not _cott_validated_construction():
            object.__setattr__(self, "null_text", _cott_validate_abi(self.null_text, str, path="$.null_text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_rows", _cott_validate_abi(self.max_rows, U64, path="$.max_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransferResult:
    __hash__ = None
    rows: U64
    path: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, U64, path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Notification:
    __hash__ = None
    channel: str
    payload: str
    pid: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "channel", _cott_validate_abi(self.channel, str, path="$.channel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "payload", _cott_validate_abi(self.payload, str, path="$.payload"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pid", _cott_validate_abi(self.pid, U32, path="$.pid"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NotificationRequest:
    __hash__ = None
    connection: ConnectionPlan
    channels: CottList[str]
    timeout_ms: U32
    max_notifications: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, ConnectionPlan, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "channels", _cott_validate_abi(self.channels, CottList[str], path="$.channels"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timeout_ms", _cott_validate_abi(self.timeout_ms, U32, path="$.timeout_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_notifications", _cott_validate_abi(self.max_notifications, U64, path="$.max_notifications"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WatchRequest:
    __hash__ = None
    query: QueryRequest
    interval_ms: U32
    max_iterations: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, QueryRequest, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "interval_ms", _cott_validate_abi(self.interval_ms, U32, path="$.interval_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_iterations", _cott_validate_abi(self.max_iterations, U64, path="$.max_iterations"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WatchResult:
    __hash__ = None
    executions: U64
    last_result: ExecutedQuery

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "executions", _cott_validate_abi(self.executions, U64, path="$.executions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "last_result", _cott_validate_abi(self.last_result, ExecutedQuery, path="$.last_result"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionMode_AutoCommit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionMode_Manual:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionMode_ReadOnly:
    pass

TransactionMode: TypeAlias = Union[TransactionMode_AutoCommit, TransactionMode_Manual, TransactionMode_ReadOnly]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionState:
    __hash__ = None
    mode: TransactionMode
    active: bool
    failed: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, TransactionMode, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "active", _cott_validate_abi(self.active, bool, path="$.active"))
        if not _cott_validated_construction():
            object.__setattr__(self, "failed", _cott_validate_abi(self.failed, bool, path="$.failed"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Tables:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Describe:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Unknown:
    pass

BackslashCommand: TypeAlias = Union[BackslashCommand_Quit, BackslashCommand_Help, BackslashCommand_Tables, BackslashCommand_Describe, BackslashCommand_Unknown]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Shell:
    __hash__ = None
    command: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_RefreshCatalog:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SqlHelp:
    __hash__ = None
    topic: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SetFormat:
    __hash__ = None
    format: TableFormat

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Connect:
    __hash__ = None
    database: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ConnectionInfo:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Copy:
    __hash__ = None
    table: str
    path: Path
    from_file: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Describe:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListDomains:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListForeignTables:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListTextSearchConfigurations:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListDataTypes:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListTablespaces:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListDefaultPrivileges:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListFunctions:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListIndexes:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListMaterializedViews:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListSchemas:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListPrivileges:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListSequences:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListTables:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListRoles:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListViews:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListExtensions:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListDatabases:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ShowFunction:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_EditBuffer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Echo:
    __hash__ = None
    text: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ReadFile:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ReadRelativeFile:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_NamedQuery:
    __hash__ = None
    name: str
    arguments: CottList[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SetLogFile:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_DeleteNamedQuery:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_PrintNamedQuery:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SaveNamedQuery:
    __hash__ = None
    name: str
    sql: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SetOutput:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ClearOutput:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SetPager:
    __hash__ = None
    enabled: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_SetOptions:
    __hash__ = None
    key: str
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_QueryOutputEcho:
    __hash__ = None
    text: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Timing:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_VerboseErrors:
    __hash__ = None
    enabled: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Watch:
    __hash__ = None
    interval_ms: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Expanded:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ExecuteBuffer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ExecuteExpanded:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_PrintBuffer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ResetBuffer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_WriteBuffer:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_History:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Favorite:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListFavorites:
    __hash__ = None
    pattern: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_DeleteFavorite:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Password:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_ListNotifications:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand_Unknown:
    __hash__ = None
    source: str

MetaCommand: TypeAlias = Union[MetaCommand_Quit, MetaCommand_Shell, MetaCommand_RefreshCatalog, MetaCommand_Help, MetaCommand_SqlHelp, MetaCommand_SetFormat, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_Describe, MetaCommand_ListDomains, MetaCommand_ListForeignTables, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListDataTypes, MetaCommand_ListTablespaces, MetaCommand_ListDefaultPrivileges, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListSchemas, MetaCommand_ListPrivileges, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListRoles, MetaCommand_ListViews, MetaCommand_ListExtensions, MetaCommand_ListDatabases, MetaCommand_ShowFunction, MetaCommand_EditBuffer, MetaCommand_Echo, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_NamedQuery, MetaCommand_SetLogFile, MetaCommand_DeleteNamedQuery, MetaCommand_PrintNamedQuery, MetaCommand_SaveNamedQuery, MetaCommand_SetOutput, MetaCommand_ClearOutput, MetaCommand_SetPager, MetaCommand_SetOptions, MetaCommand_QueryOutputEcho, MetaCommand_Timing, MetaCommand_VerboseErrors, MetaCommand_Watch, MetaCommand_Expanded, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_PrintBuffer, MetaCommand_ResetBuffer, MetaCommand_WriteBuffer, MetaCommand_History, MetaCommand_Favorite, MetaCommand_ListFavorites, MetaCommand_DeleteFavorite, MetaCommand_Password, MetaCommand_ListNotifications, MetaCommand_Unknown]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandInvocation:
    __hash__ = None
    command: MetaCommand
    buffer: InputBuffer

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "command", _cott_validate_abi(self.command, MetaCommand, path="$.command"))
        if not _cott_validated_construction():
            object.__setattr__(self, "buffer", _cott_validate_abi(self.buffer, InputBuffer, path="$.buffer"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionOptions:
    __hash__ = None
    connection: ConnectionPlan
    catalog_limit: U64
    completion_limit: U64
    history: HistoryPolicy
    favorites: FavoriteStore
    format: TableFormat
    timing: bool
    pager: bool
    multiline: bool
    transaction: TransactionMode

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, ConnectionPlan, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "catalog_limit", _cott_validate_abi(self.catalog_limit, U64, path="$.catalog_limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "completion_limit", _cott_validate_abi(self.completion_limit, U64, path="$.completion_limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "history", _cott_validate_abi(self.history, HistoryPolicy, path="$.history"))
        if not _cott_validated_construction():
            object.__setattr__(self, "favorites", _cott_validate_abi(self.favorites, FavoriteStore, path="$.favorites"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, TableFormat, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timing", _cott_validate_abi(self.timing, bool, path="$.timing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pager", _cott_validate_abi(self.pager, bool, path="$.pager"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multiline", _cott_validate_abi(self.multiline, bool, path="$.multiline"))
        if not _cott_validated_construction():
            object.__setattr__(self, "transaction", _cott_validate_abi(self.transaction, TransactionMode, path="$.transaction"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
    __hash__ = None
    buffer: InputBuffer
    output: str
    quit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "buffer", _cott_validate_abi(self.buffer, InputBuffer, path="$.buffer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output", _cott_validate_abi(self.output, str, path="$.output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quit", _cott_validate_abi(self.quit, bool, path="$.quit"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InteractiveRequest:
    __hash__ = None
    options: SessionOptions
    initial_sql: str
    execute_once: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, SessionOptions, path="$.options"))
        if not _cott_validated_construction():
            object.__setattr__(self, "initial_sql", _cott_validate_abi(self.initial_sql, str, path="$.initial_sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "execute_once", _cott_validate_abi(self.execute_once, bool, path="$.execute_once"))

"""Run an interactive PostgreSQL session and print client errors before exiting."""
__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "ClientError", "ClientError_CatalogFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionError_TlsInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_ClearOutput", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListNotifications", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_Password", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetLogFile", "MetaCommand_SetOptions", "MetaCommand_SetOutput", "MetaCommand_SetPager", "MetaCommand_Shell", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_VerboseErrors", "MetaCommand_Watch", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SessionOptions", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransferResult", "WatchRequest", "WatchResult"]
