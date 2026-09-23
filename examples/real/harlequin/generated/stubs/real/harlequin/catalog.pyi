from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.catalog_types import CatalogColumn as CatalogColumn, CatalogError as CatalogError, CatalogError_ConnectionMissing as CatalogError_ConnectionMissing, CatalogError_Failed as CatalogError_Failed, CatalogError_LimitExceeded as CatalogError_LimitExceeded, CatalogError_NamespaceMissing as CatalogError_NamespaceMissing, CatalogMatch as CatalogMatch, CatalogMatchKind as CatalogMatchKind, CatalogMatchKind_Column as CatalogMatchKind_Column, CatalogMatchKind_Relation as CatalogMatchKind_Relation, CatalogRelation as CatalogRelation, CatalogScope as CatalogScope, CatalogSnapshot as CatalogSnapshot, CompletionRequest as CompletionRequest, CompletionResult as CompletionResult, RelationKind as RelationKind, RelationKind_Table as RelationKind_Table, RelationKind_View as RelationKind_View
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError
def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]: ...

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]: ...

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]: ...

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
ISO-8601 with six fractional digits and a trailing Z. No empty/stub timestamp."""
def refresh_catalog(connection: Connection, scope: CatalogScope) -> Result[CatalogSnapshot, CatalogError]: ...

def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult: ...

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
def find_catalog(snapshot: CatalogSnapshot, term: str, maximum_matches: U64) -> Result[CottList[CatalogMatch], CatalogError]: ...

__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "complete_sql", "find_catalog", "refresh_catalog", "search_catalog"]
