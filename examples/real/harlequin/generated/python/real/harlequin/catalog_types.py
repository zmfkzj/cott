from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RelationKind_Table:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RelationKind_View:
    pass

RelationKind: TypeAlias = Union[RelationKind_Table, RelationKind_View]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogMatchKind_Relation:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogMatchKind_Column:
    pass

CatalogMatchKind: TypeAlias = Union[CatalogMatchKind_Relation, CatalogMatchKind_Column]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogRelation:
    __hash__ = None
    name: str
    kind: RelationKind
    sql: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, RelationKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, Option[str], path="$.sql"))

"""One column of a relation. ordinal is the 1-based column position; declared_type is
the declared type text ("" when none); default_sql is the default expression text;
primary_key_position is the 1-based position within the primary key, 0 when the
column is not part of it."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogColumn:
    __hash__ = None
    relation: str
    ordinal: U32
    name: str
    declared_type: str
    not_null: bool
    default_sql: Option[str]
    primary_key_position: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "relation", _cott_validate_abi(self.relation, str, path="$.relation"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ordinal", _cott_validate_abi(self.ordinal, U32, path="$.ordinal"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "declared_type", _cott_validate_abi(self.declared_type, str, path="$.declared_type"))
        if not _cott_validated_construction():
            object.__setattr__(self, "not_null", _cott_validate_abi(self.not_null, bool, path="$.not_null"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default_sql", _cott_validate_abi(self.default_sql, Option[str], path="$.default_sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "primary_key_position", _cott_validate_abi(self.primary_key_position, U32, path="$.primary_key_position"))

"""A search hit. A Relation match has relation and name equal to the relation name and
ordinal 0; a Column match names its relation, the column name and the column's
1-based ordinal."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogMatch:
    __hash__ = None
    kind: CatalogMatchKind
    relation: str
    name: str
    ordinal: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, CatalogMatchKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "relation", _cott_validate_abi(self.relation, str, path="$.relation"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ordinal", _cott_validate_abi(self.ordinal, U32, path="$.ordinal"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogScope:
    __hash__ = None
    connection_id: str
    namespace: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection_id", _cott_validate_abi(self.connection_id, str, path="$.connection_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "namespace", _cott_validate_abi(self.namespace, Option[str], path="$.namespace"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogSnapshot:
    __hash__ = None
    scope: CatalogScope
    relations: CottList[CatalogRelation]
    refreshed_at: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "scope", _cott_validate_abi(self.scope, CatalogScope, path="$.scope"))
        if not _cott_validated_construction():
            object.__setattr__(self, "relations", _cott_validate_abi(self.relations, CottList[CatalogRelation], path="$.relations"))
        if not _cott_validated_construction():
            object.__setattr__(self, "refreshed_at", _cott_validate_abi(self.refreshed_at, str, path="$.refreshed_at"))

"""cursor counts Unicode scalar values into source."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionRequest:
    __hash__ = None
    source: str
    cursor: U64
    scope: CatalogScope
    maximum_candidates: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scope", _cott_validate_abi(self.scope, CatalogScope, path="$.scope"))
        if not _cott_validated_construction():
            object.__setattr__(self, "maximum_candidates", _cott_validate_abi(self.maximum_candidates, U64, path="$.maximum_candidates"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionResult:
    __hash__ = None
    candidates: CottList[str]
    replace_start: U64
    replace_end: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "candidates", _cott_validate_abi(self.candidates, CottList[str], path="$.candidates"))
        if not _cott_validated_construction():
            object.__setattr__(self, "replace_start", _cott_validate_abi(self.replace_start, U64, path="$.replace_start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "replace_end", _cott_validate_abi(self.replace_end, U64, path="$.replace_end"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_ConnectionMissing:
    __hash__ = None
    connection_id: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_NamespaceMissing:
    __hash__ = None
    namespace: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_Failed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_LimitExceeded:
    __hash__ = None
    limit: U32

CatalogError: TypeAlias = Union[CatalogError_ConnectionMissing, CatalogError_NamespaceMissing, CatalogError_Failed, CatalogError_LimitExceeded]

"""List the tables and views of a standalone SQLite database's main schema with
sqlite3, independent of any live connection. Memory is a fresh empty in-memory
database for this call, so it lists nothing; File(path) opens that existing file
with mode=ro and never creates it. Rows come from sqlite_schema entries of type
table or view whose name does not start with "sqlite_", ordered by name in
Python string order. sql is the stored CREATE text, Nothing when it is SQL NULL.
Any SQLite failure, including a missing file, is SqliteFailure with SQLite's
message."""
"""Describe one relation of the same standalone main schema from PRAGMA table_info,
in declaration order. Every column's relation is the requested name; not_null
reflects NOT NULL and default_sql is Nothing when there is no default. A
relation that does not exist, which includes every relation of a Memory
database, is SqliteFailure("no such relation"). Other SQLite failures are
SqliteFailure with SQLite's message."""
"""Search the same standalone main schema for relations and columns whose name
contains term after Unicode case folding (Python str.casefold); an empty term
matches everything. Relations are visited in catalog_relations order; each
relation contributes its own match first and then its matching columns in
column order. The result stops after the first 1000 matches without error.
SQLite failures are SqliteFailure with SQLite's message."""
"""Refresh one namespace through a real temporary driver client, using the
endpoint formats documented by AdapterKind. This is an independent metadata
connection, not a lookup of a hidden live-connection registry or a view of
another connection's uncommitted transaction.
Before any I/O, an empty connection.id or a scope.connection_id different from
connection.id returns ConnectionMissing(connection_id=scope.connection_id).
Preserve scope exactly in the successful snapshot.
Validate the SessionHandle payload and its matching metadata, then hold its
lock for this call. A closed or malformed owning session returns Failed before
opening the independent metadata client. Never close the owner or complete its
active transaction. A fresh :memory: metadata client still sees its own empty
database; this API intentionally reports an independent committed snapshot,
whereas execute_statements is the operation on the retained live session.

A supplied namespace selects one exact visible namespace. Return
NamespaceMissing(namespace=the supplied value) only after successful metadata
discovery establishes its absence. Without a supplied namespace, use the
backend default described below; a missing or ambiguous default is Failed.
Read tables and views only, order by the original name using Python string
ordering (Table before View for equal names), and never merge namespaces.
Probe for a 100001st relation and return LimitExceeded(limit=100000) rather
than silently truncating. Empty success is valid only after a real successful
query of an existing empty namespace.

SQLite: open files with URI mode=ro, never create a missing database, and enable
query_only. :memory: opens a fresh database for this call. The default is main;
discover available namespaces with PRAGMA database_list. Quote a discovered
schema identifier by doubling double quotes. Read its sqlite_schema rows of
type table or view, excluding names whose literal prefix is sqlite_.
Preserve nonnull stored SQL as Some; SQL NULL becomes Nothing.
DuckDB: open an existing file read_only=True (:memory: uses a fresh in-memory
connection). Use current_database() and default schema main; discover with
duckdb_schemas(). Query duckdb_tables() and duckdb_views(), restricted to that
database/schema and internal=false, retaining stored SQL when available.
PostgreSQL: use psycopg and information_schema.schemata/tables with bound schema
values; default to current_schema(). BASE TABLE maps to Table and VIEW to View.
MySQL: use pymysql and INFORMATION_SCHEMA.SCHEMATA/TABLES with bound schema
values; default to DATABASE(). BASE TABLE maps to Table and VIEW to View.
Both return Nothing for SQL text rather than inventing CREATE statements.
ODBC: use SQLTables namespace enumeration before listing relations, so an
existing empty schema is distinguishable from an absent schema:
cursor.tables(catalog="", schema="%", table="") lists schema names;
cursor.tables(catalog="%", schema="", table="") lists catalogs.
A driver without schema support (SQL_SCHEMA_USAGE == 0) uses the empty schema.
Restrict to getinfo(SQL_DATABASE_NAME) when reported; otherwise require one
unambiguous catalog. None namespace selects the unique visible schema.
List cursor.tables(tableType="TABLE,VIEW") and exact-filter catalog/schema
fields, treating SQL NULL names as empty strings (API filters may be patterns).
Multiple possible defaults or unsupported discovery are Failed, not an empty
success. TABLE/VIEW map directly; SQL is Nothing.
ADBC: use adbc_driver_manager.dbapi.connect with driver/uri/entrypoint and
db_kwargs/conn_kwargs from the documented endpoint. Call its public
adbc_get_objects(depth="db_schemas") for namespace discovery and
adbc_get_objects(depth="tables") for relations. Select endpoint.catalog when
supplied, then an exact supplied schema or the unique visible catalog/schema
pair. Null catalog/schema metadata names are represented as empty strings.
The lock-selected pyarrow dependency supplies the returned RecordBatchReader.
Feed that reader to a temporary in-memory duckdb connection's from_arrow,
then SQL UNNEST catalog_db_schemas and db_schema_tables with bound filters and
LIMIT 100001 before fetching flat rows. Keep the ADBC connection alive until
its reader is consumed; close the DuckDB bridge and reader before ADBC.
Use these public metadata APIs, never interpreter heap-introspection methods.
Normalize driver table-type spelling case-insensitively: TABLE and BASE TABLE
mean Table, VIEW means View; other kinds are outside this catalog. SQL is Nothing.

BigQuery: construct google.cloud.bigquery.Client using project/location and
ADC. A namespace is a dataset id within endpoint.project; default to
endpoint.dataset. Use get_dataset to establish existence and list_tables with
max_results=100001 to enumerate. VIEW/MATERIALIZED_VIEW map to View;
TABLE/EXTERNAL/SNAPSHOT/CLONE map to Table. SQL is Nothing.
Trino: use trino.dbapi and optional BasicAuthentication. A namespace is exactly
catalog.schema (one dot, two nonempty components); otherwise use endpoint
catalog/schema. Use SHOW CATALOGS and SHOW SCHEMAS FROM a safely double-quoted
catalog to establish existence. Query that catalog's information_schema.tables,
binding the schema value and limiting to 100001 rows. BASE TABLE maps to Table;
VIEW/MATERIALIZED VIEW map to View. SQL is Nothing.
Databricks: use databricks.sql.connect with the PAT, hostname and HTTP path.
Namespace has the same catalog.schema form, defaulting to endpoint fields.
Use cursor.catalogs() and cursor.schemas() with exact matching, then stream
cursor.tables() results, exact-filtered to the selected catalog/schema. Stop
after the 100001st matching supported relation; do not invent metadata paging.
VIEW/MATERIALIZED_VIEW/METRIC_VIEW map to View; TABLE/BASE TABLE/MANAGED/EXTERNAL/
FOREIGN/STREAMING_TABLE/MANAGED_SHALLOW_CLONE/EXTERNAL_SHALLOW_CLONE map to Table.
SQL is Nothing.
Cassandra: use Cluster and optional PlainTextAuthProvider; connect to establish
real metadata, then read cluster.metadata.keyspaces. Namespace is the keyspace,
defaulting to endpoint.keyspace. Its tables map to Table and materialized views
to View; count both maps before materializing the bounded output. CQL is not
SQL, so sql is Nothing. Always shutdown the cluster.
NebulaGraph: initialize ConnectionPool, acquire a session, and execute
SHOW SPACES. Namespace is the exact space name, defaulting to endpoint.space.
After discovery, issue USE with a backtick-quoted name. Names containing a
backtick, backslash or control character are Failed rather than interpolated.
Execute SHOW TAGS and SHOW EDGES and check each ResultSet.is_succeeded().
Consume actual as_primitive() rows: tags become Table named "tag:" plus the
original tag name; edges become Table named "edge:" plus the original edge type.
These SHOW APIs are unpaged: check their combined real result count before
creating relations. nGQL is not SQL, so sql is Nothing. Release the session
before closing the pool.
Ignore backend object kinds outside the explicitly listed table/view kinds.
A required endpoint namespace default that is absent is Failed. For an explicit
requested namespace, a definitive not-found response is NamespaceMissing; do
not reinterpret authentication, permission or transport failures as absence.

Issue metadata reads only, regardless of connection.read_only; do not execute
application SQL, initialize schemas, create files, or enable extensions.
Close every cursor, stream, session and client on success and on all errors.
Malformed endpoint data, missing drivers, authentication, transport, permission
and metadata API failures return Failed with a fixed nonsecret category message.
Never include endpoint values, credentials, or raw driver exception text.
On success read the real clock after enumeration and set refreshed_at to UTC
ISO-8601 in the form YYYY-MM-DDTHH:MM:SS.ffffffZ (six fractional digits)."""
"""Offer completions for the identifier being typed at request.cursor. The typed
prefix is the longest run of ASCII letters, ASCII digits and "_" ending at the
cursor; replace_start is where it begins and replace_end is the cursor. An empty
prefix offers no candidates. A candidate matches when it starts with the prefix
ignoring ASCII case. Relation names come first, in snapshot order, and only when
request.scope equals snapshot.scope; then these keywords in this order: SELECT,
FROM, WHERE, GROUP, BY, ORDER, HAVING, LIMIT, JOIN, LEFT, INNER, ON, AS, AND, OR,
NOT, NULL, INSERT, INTO, VALUES, UPDATE, SET, DELETE, CREATE, TABLE, VIEW, DROP,
WITH, DISTINCT, UNION. A candidate equal to an earlier one is skipped, spelling is
kept, and at most maximum_candidates are returned."""
"""Search only relation names already present in snapshot; this pure function does
not query a database or infer columns from SQL. Preserve snapshot order and
duplicates. A name matches when term.casefold() is a substring of its
casefolded name; an empty term matches every relation.
Each match has kind Relation, relation and name equal to the original relation
name, and ordinal zero (not a ranking or column position).
maximum_matches greater than 1000 returns LimitExceeded(limit=1000), including
values above U32's range; do not narrow or clamp the caller's U64 value.
Otherwise return the first maximum_matches matches, truncating without error.
A zero limit returns an empty success. Column matches are never produced
because CatalogSnapshot contains no column metadata."""
__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View"]
