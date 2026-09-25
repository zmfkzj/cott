from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""Connection-layer failures. Every message payload is a fixed, nonsecret
category text: it never contains a password, connection-string text,
private-key contents or raw exception text."""
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

ConnectionError: TypeAlias = Union[ConnectionError_MissingDatabase, ConnectionError_InvalidPort, ConnectionError_InvalidDsn, ConnectionError_ProfileMissing, ConnectionError_SshInvalid, ConnectionError_CredentialUnavailable, ConnectionError_PromptDisabled, ConnectionError_ConnectionFailed]

"""Failures of the minimal settings-only query API. Messages never contain connection
parameters; QueryFailed carries the SQLSTATE and the server's primary message."""
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

"""Client failures. Message payloads are fixed, nonsecret category texts, except
that QueryFailed may carry the SQLSTATE and the server's primary message. No
payload contains a password, connection-string text or raw exception text.
TunnelUnsupported means a database operation received a plan with an SSH hop,
which only the connection probe supports."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_InvalidArguments:
    __hash__ = None
    message: str

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
class ClientError_ConnectionFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientError_TunnelUnsupported:
    pass

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

ClientError: TypeAlias = Union[ClientError_InvalidArguments, ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_ConnectionFailed, ClientError_TunnelUnsupported, ClientError_CatalogFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_ImportFailed, ClientError_ExportFailed, ClientError_HistoryFailed, ClientError_FavoriteFailed, ClientError_EditorFailed, ClientError_PagerFailed, ClientError_NotificationFailed, ClientError_TerminalFailed, ClientError_UnsupportedFormat]

"""Connection fields as the user gave them. "" means not specified. port is
decimal text."""
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

"""The values of PGHOST, PGPORT, PGUSER, PGPASSWORD and PGDATABASE, "" when unset."""
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

"""libpq sslmode request. Default sets no sslmode, leaving the connection string's
value or libpq's default (prefer). The others set sslmode to disable, allow,
prefer, require, verify-ca or verify-full."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_Default:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_Disable:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_Allow:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_Prefer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_Require:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_VerifyCa:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsMode_VerifyFull:
    pass

TlsMode: TypeAlias = Union[TlsMode_Default, TlsMode_Disable, TlsMode_Allow, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TlsMode_VerifyFull]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClientCertificate:
    __hash__ = None
    certificate: Path
    private_key: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "certificate", _cott_validate_abi(self.certificate, Path, path="$.certificate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "private_key", _cott_validate_abi(self.private_key, Path, path="$.private_key"))

"""root_certificate sets sslrootcert; client sets sslcert and sslkey together.
Nothing leaves the parameter unset."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TlsSettings:
    __hash__ = None
    mode: TlsMode
    root_certificate: Option[Path]
    client: Option[ClientCertificate]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, TlsMode, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "root_certificate", _cott_validate_abi(self.root_certificate, Option[Path], path="$.root_certificate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "client", _cott_validate_abi(self.client, Option[ClientCertificate], path="$.client"))

"""An OpenSSH jump host. private_key Some(path) selects that identity file;
Nothing uses the ssh client's configured identities."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SshSettings:
    __hash__ = None
    host: str
    port: U16
    user: str
    private_key: Option[Path]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, U16, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "private_key", _cott_validate_abi(self.private_key, Option[Path], path="$.private_key"))

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

"""A plan denotes one set of libpq connection parameters: start from dsn parsed as
a libpq connection string ("" gives none); nonempty settings host, port, user,
password and database replace host, port, user, password and dbname; apply
TlsSettings; always set connect_timeout=10. Parameters are connection data and
are never interpolated into SQL or shell text. TLS verification requested by the
plan or its connection string is never weakened. ssh Some(hop) means PostgreSQL is
reached through that jump host; only the connection probe supports such plans,
and every other database operation rejects them with TunnelUnsupported."""
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

"""What the server confirmed for a successful probe: current_database(),
current_user and the server_version setting."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionReceipt:
    __hash__ = None
    database: str
    user: str
    server_version: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "server_version", _cott_validate_abi(self.server_version, str, path="$.server_version"))

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

"""A snapshot of server metadata. A relation kind is one of "table",
"partitioned table", "view", "materialized view", "sequence" or
"foreign table"; its columns are the live attributes in attribute order.
A routine's arguments is its identity argument list text and result_type its
result type text. Schema-scoped lists are ordered by schema then name, the other
lists by name, and each list holds the first limit entries of that order.
refreshed_at_ms is wall-clock Unix milliseconds when the snapshot completed and
limit is the requested limit."""
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

"""include_system false omits objects in pg_catalog, information_schema and schemas
whose names start with pg_toast or pg_temp, and template databases."""
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

SQL_KEYWORDS: Final[str] = "SELECT FROM WHERE JOIN LEFT RIGHT INNER OUTER FULL CROSS ON USING GROUP BY ORDER HAVING LIMIT OFFSET INSERT INTO VALUES UPDATE SET DELETE RETURNING AND OR NOT NULL IS IN LIKE ILIKE BETWEEN AS DISTINCT CASE WHEN THEN ELSE END CREATE ALTER DROP TABLE VIEW INDEX BEGIN COMMIT ROLLBACK WITH UNION ALL EXISTS ASC DESC TRUE FALSE"

"""cursor counts Unicode code points of source."""
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
        if not (_cott_contract_condition((((self).cursor <= len((self).source))), "real.pgcli.CompletionRequest", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.pgcli.CompletionRequest", clause="invariant:0", phase="invariant", span={"end_byte":6647,"end_column":45,"end_line":241,"start_byte":6607,"start_column":5,"start_line":241}, expected="true", actual="false")

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

"""Output formats. Their \\T names are aligned, csv, tsv, json, jsonl, html, latex,
markdown and vertical."""
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

"""Tabular text. A cell is the text of one value: SQL NULL is "<null>", bytea is
"\\x" followed by lowercase hexadecimal, and any other value is the text of the
driver-decoded value (str in Python)."""
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
class RenderRequest:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[CottList[str]]
    terminal_width: U16
    layout: RenderLayout

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[CottList[str]], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_width", _cott_validate_abi(self.terminal_width, U16, path="$.terminal_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "layout", _cott_validate_abi(self.layout, RenderLayout, path="$.layout"))

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

"""width is the length in code points of the longest line of text, at most 65535."""
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

"""AutoCommit commits each statement; Manual runs one submission in one transaction;
ReadOnly runs one submission in a READ ONLY transaction that is rolled back."""
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

"""The client's view of one explicit transaction: none open, open, or failed after
an error so that only rollback is possible."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Idle:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Active:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Failed:
    pass

TransactionStatus: TypeAlias = Union[TransactionStatus_Idle, TransactionStatus_Active, TransactionStatus_Failed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionState:
    __hash__ = None
    mode: TransactionMode
    status: TransactionStatus

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, TransactionMode, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, TransactionStatus, path="$.status"))

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

"""Pending input. cursor counts Unicode code points of text."""
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
        if not (_cott_contract_condition((((self).cursor <= len((self).text))), "real.pgcli.InputBuffer", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.pgcli.InputBuffer", clause="invariant:0", phase="invariant", span={"end_byte":9020,"end_column":43,"end_line":361,"start_byte":8982,"start_column":5,"start_line":361}, expected="true", actual="false")

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

"""History persistence is UTF-8 JSON: one array in oldest-to-newest stored order,
with exact object fields sql (string), executed_at_ms (integer 0..2^64-1, never
boolean), database (string), success (boolean). This is this Cott client's format,
not upstream pgcli's query-text-only history. No timestamp is inferred or rewritten."""
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

"""HistoryPolicy normalization preserves stored order, removes all but the last
occurrence of each exact (database, sql) pair when unique is true, then keeps the
last max_entries entries in their relative order. A zero capacity produces an
empty list. It never sorts by executed_at_ms."""
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

"""Favorites persistence is UTF-8 JSON: one array in authored order, with exact object
fields name (string), sql (string), tags (array of strings). No unknown/missing
fields or coercions. Names are unique by exact case-sensitive spelling and not
blank (blank as any_blank_by defines: empty or only the 25 Unicode White_Space
code points); tags may repeat and keep their order. This is this Cott client's
format, not an upstream pgcli configuration section."""
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
class MetaCommand_SetPager:
    __hash__ = None
    enabled: bool

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
class MetaCommand_Unknown:
    __hash__ = None
    source: str

MetaCommand: TypeAlias = Union[MetaCommand_Quit, MetaCommand_RefreshCatalog, MetaCommand_Help, MetaCommand_SqlHelp, MetaCommand_SetFormat, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_Describe, MetaCommand_ListDomains, MetaCommand_ListForeignTables, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListDataTypes, MetaCommand_ListTablespaces, MetaCommand_ListDefaultPrivileges, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListSchemas, MetaCommand_ListPrivileges, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListRoles, MetaCommand_ListViews, MetaCommand_ListExtensions, MetaCommand_ListDatabases, MetaCommand_ShowFunction, MetaCommand_EditBuffer, MetaCommand_Echo, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_NamedQuery, MetaCommand_DeleteNamedQuery, MetaCommand_PrintNamedQuery, MetaCommand_SaveNamedQuery, MetaCommand_SetPager, MetaCommand_QueryOutputEcho, MetaCommand_Timing, MetaCommand_Expanded, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_PrintBuffer, MetaCommand_ResetBuffer, MetaCommand_WriteBuffer, MetaCommand_History, MetaCommand_Favorite, MetaCommand_ListFavorites, MetaCommand_DeleteFavorite, MetaCommand_Unknown]

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

"""Session settings. history Nothing disables history persistence and favorites
Nothing disables favorites. max_rows bounds the rows fetched and shown per
statement; catalog_limit bounds each catalog list."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionOptions:
    __hash__ = None
    connection: ConnectionPlan
    catalog_limit: U64
    max_rows: U64
    history: Option[HistoryPolicy]
    favorites: Option[FavoriteStore]
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
            object.__setattr__(self, "max_rows", _cott_validate_abi(self.max_rows, U64, path="$.max_rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "history", _cott_validate_abi(self.history, Option[HistoryPolicy], path="$.history"))
        if not _cott_validated_construction():
            object.__setattr__(self, "favorites", _cott_validate_abi(self.favorites, Option[FavoriteStore], path="$.favorites"))
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
    options: SessionOptions
    catalog: Catalog
    output: str
    quit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "buffer", _cott_validate_abi(self.buffer, InputBuffer, path="$.buffer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, SessionOptions, path="$.options"))
        if not _cott_validated_construction():
            object.__setattr__(self, "catalog", _cott_validate_abi(self.catalog, Catalog, path="$.catalog"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output", _cott_validate_abi(self.output, str, path="$.output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quit", _cott_validate_abi(self.quit, bool, path="$.quit"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionMode_Interactive:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionMode_ExecuteOnce:
    pass

SessionMode: TypeAlias = Union[SessionMode_Interactive, SessionMode_ExecuteOnce]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InteractiveRequest:
    __hash__ = None
    options: SessionOptions
    initial_sql: str
    mode: SessionMode

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, SessionOptions, path="$.options"))
        if not _cott_validated_construction():
            object.__setattr__(self, "initial_sql", _cott_validate_abi(self.initial_sql, str, path="$.initial_sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, SessionMode, path="$.mode"))

"""submissions counts every submitted SQL text or backslash command; failures counts
those that ended in a ClientError."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionReport:
    __hash__ = None
    submissions: U64
    failures: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "submissions", _cott_validate_abi(self.submissions, U64, path="$.submissions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "failures", _cott_validate_abi(self.failures, U64, path="$.failures"))
        if not (_cott_contract_condition((((self).failures <= (self).submissions)), "real.pgcli.SessionReport", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.pgcli.SessionReport", clause="invariant:0", phase="invariant", span={"end_byte":13791,"end_column":48,"end_line":557,"start_byte":13748,"start_column":5,"start_line":557}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliCommand_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliCommand_Session:
    __hash__ = None
    connection: ConnectionRequest
    mode: SessionMode
    initial_sql: str

CliCommand: TypeAlias = Union[CliCommand_Help, CliCommand_Session]

"""Parse value as one libpq connection string: a postgresql:// or postgres://
URI (percent-decoded) or whitespace-separated key=value pairs. Return its
host, port, user, password and dbname parameters verbatim; an absent
parameter is "". A string libpq cannot parse, and one that names no
database, is InvalidDsn whose value is a fixed category message that never
contains any part of the input, which may include a password."""
"""Return the first profile in list order whose name equals name exactly
(case-sensitive, no trimming); when none does, return ProfileMissing(name: name)."""
"""Merge explicit inputs over environment values field by field. The merged
database must be nonempty. A nonempty merged port must consist of ASCII
digits denoting 1..65535, otherwise return InvalidPort(value: the merged
port); an empty port stays empty and means libpq's default."""
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
"""Decide how to obtain a password: a nonempty password is used as is; an empty
one is prompted for unless prompting is disabled."""
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
"""Open an explicit transaction in the client's transaction model."""
"""Commit the open transaction. Committing when no transaction is open, or after
it failed (PostgreSQL rolls a failed transaction back instead), is
TransactionFailed."""
"""Roll back an open or failed transaction. Rolling back when no transaction is
open is TransactionFailed."""
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
"""Complete with the default interactive policy: the result is exactly
complete_catalog_sql(request, CompletionPolicy(max_candidates: 50,
include_keywords: true))."""
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
"""Insert input into buffer.text at buffer.cursor and move the cursor to the end
of the inserted text."""
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
"""Classify source through parse_meta_command(source): Quit -> Quit, Help -> Help,
ListTables -> Tables, Describe -> Describe, every other command -> Unknown."""
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
"""Append entry to entries, then apply HistoryPolicy normalization. This is a
pure list transformation with no clock or filesystem access."""
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
"""Run sql once on a new autocommit connection built only from the nonempty
fields of connection (host, port, user, password, dbname; libpq defaults
otherwise; no connection string, TLS settings or SSH hop), then close it.
Return the columns and all rows of the last statement that produced rows, in
server order, with QueryResult cell text; no columns and no rows when no
statement produced rows. Failing to open the connection or authenticate is
ConnectionFailed; a statement error is QueryFailed."""
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
"""Execute request.query max_iterations times through execute_planned_query,
waiting interval_ms milliseconds between consecutive executions and not
after the last. The first failing execution stops the watch and its error is
returned unchanged. last_result is the final execution's result."""
"""Read a Catalog snapshot through one read-only connection with the
ConnectionPlan parameters using fixed, parameterized catalog queries, then
close the connection. Connection and query failures are CatalogFailed."""
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
"""LISTEN on every channel, each quoted as an SQL identifier, over one
autocommit connection with the ConnectionPlan parameters. Collect
notifications in arrival order until max_notifications have arrived or
timeout_ms monotonic milliseconds have passed since listening began,
whichever comes first; each carries its channel, payload and sender pid.
UNLISTEN and close the connection on every path. Connection and listening
failures are NotificationFailed."""
"""Write buffer.text as UTF-8 to temporary_path, start the editor on it and wait
for it to exit, then read the file back. editor is split into words at
whitespace (no shell) and temporary_path is appended as the last argument; the
editor inherits the terminal. A zero exit status returns the file's text
without one trailing line feed, with the cursor at its end and
buffer.multiline kept. temporary_path is removed on every path. A missing
editor executable, a nonzero exit or signal, and I/O or decoding failures
are EditorFailed with a fixed category message."""
"""Show text on the terminal. When enabled is false, or text has at most
terminal_height lines, write text and one line feed to standard output.
Otherwise start the pager command, split into words at whitespace (no shell),
with text and one line feed on its standard input, and wait for it to exit;
a pager that exits with status 0 after closing its input early succeeds.
A pager that cannot start or exits nonzero, and a failed write to standard
output, are PagerFailed with a fixed category message."""
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
__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "CliCommand", "CliCommand_Help", "CliCommand_Session", "ClientCertificate", "ClientError", "ClientError_CatalogFailed", "ClientError_ConnectionFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidArguments", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_TunnelUnsupported", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionReceipt", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetPager", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SQL_KEYWORDS", "SessionMode", "SessionMode_ExecuteOnce", "SessionMode_Interactive", "SessionOptions", "SessionReport", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsMode", "TlsMode_Allow", "TlsMode_Default", "TlsMode_Disable", "TlsMode_Prefer", "TlsMode_Require", "TlsMode_VerifyCa", "TlsMode_VerifyFull", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Failed", "TransactionStatus_Idle", "TransferResult", "WatchRequest", "WatchResult"]
