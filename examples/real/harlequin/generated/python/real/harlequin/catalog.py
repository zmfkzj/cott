from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with, _cott_unique_by

from real.harlequin.catalog_types import CatalogColumn, CatalogError, CatalogError_ConnectionMissing, CatalogError_Failed, CatalogError_LimitExceeded, CatalogError_NamespaceMissing, CatalogMatch, CatalogMatchKind, CatalogMatchKind_Column, CatalogMatchKind_Relation, CatalogRelation, CatalogScope, CatalogSnapshot, CompletionRequest, CompletionResult, RelationKind, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError

def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    """List the tables and views of a standalone SQLite database's main schema with
sqlite3, independent of any live connection. Memory is a fresh empty in-memory
database for this call, so it lists nothing; File(path) opens that existing file
with mode=ro and never creates it. Rows come from sqlite_schema entries of type
table or view whose name does not start with "sqlite_", ordered by name in
Python string order. sql is the stored CREATE text, Nothing when it is SQL NULL.
Any SQLite failure, including a missing file, is SqliteFailure with SQLite's
message."""
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_relations.py", "e6e32fca774692887f0e3f5e924b25e0c7c8eed2590be6e26828b5d0ad326d3f", "catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_relations")
        _result = _implementation(database)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":2478,"end_column":1,"end_line":91,"start_byte":1620,"start_column":1,"start_line":73}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":2478,"end_column":1,"end_line":91,"start_byte":1620,"start_column":1,"start_line":73}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":2478,"end_column":1,"end_line":91,"start_byte":1620,"start_column":1,"start_line":73}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_relations", phase="error", span={"end_byte":2478,"end_column":1,"end_line":91,"start_byte":1620,"start_column":1,"start_line":73}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_relations", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_relations", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            relations = _cott_match_value.value
            return (_cott_contract_condition((_cott_unique_by(relations, "name")), "real.harlequin.catalog.catalog_relations", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.catalog.catalog_relations", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_relations", clause="ensures:1", phase="ensures", span={"end_byte":2407,"end_column":79,"end_line":85,"start_byte":2333,"start_column":5,"start_line":85}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    """Describe one relation of the same standalone main schema from PRAGMA table_info,
in declaration order. Every column's relation is the requested name; not_null
reflects NOT NULL and default_sql is Nothing when there is no default. A
relation that does not exist, which includes every relation of a Memory
database, is SqliteFailure("no such relation"). Other SQLite failures are
SqliteFailure with SQLite's message."""
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    relation = _cott_validate_abi(relation, str, path="$.relation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_columns.py", "3f09c3785f389c452a184fe9796ebdfa3b82136a7ab3cdd719d70153e10b225a", "catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_columns")
        _result = _implementation(database, relation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":3400,"end_column":1,"end_line":113,"start_byte":2655,"start_column":1,"start_line":94}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":3400,"end_column":1,"end_line":113,"start_byte":2655,"start_column":1,"start_line":94}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":3400,"end_column":1,"end_line":113,"start_byte":2655,"start_column":1,"start_line":94}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_columns", phase="error", span={"end_byte":3400,"end_column":1,"end_line":113,"start_byte":2655,"start_column":1,"start_line":94}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_columns", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_columns", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            columns = _cott_match_value.value
            return (_cott_contract_condition((((len(columns) > 0) and _cott_unique_by(columns, "ordinal"))), "real.harlequin.catalog.catalog_columns", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.catalog.catalog_columns", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_columns", clause="ensures:1", phase="ensures", span={"end_byte":3329,"end_column":96,"end_line":107,"start_byte":3238,"start_column":5,"start_line":107}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    """Search the same standalone main schema for relations and columns whose name
contains term after Unicode case folding (Python str.casefold); an empty term
matches everything. Relations are visited in catalog_relations order; each
relation contributes its own match first and then its matching columns in
column order. The result stops after the first 1000 matches without error.
SQLite failures are SqliteFailure with SQLite's message."""
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    term = _cott_validate_abi(term, str, path="$.term")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/search_catalog.py", "c411beb3fcc34e8f2d35d0df8c4bb8330d99e3473891464e0dbd82306ce9aa4b", "search_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.search_catalog")
        _result = _implementation(database, term)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.search_catalog"
        if _error.span is None:
            _error.span = {"end_byte":4291,"end_column":1,"end_line":135,"start_byte":3558,"start_column":1,"start_line":116}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":4291,"end_column":1,"end_line":135,"start_byte":3558,"start_column":1,"start_line":116}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":4291,"end_column":1,"end_line":135,"start_byte":3558,"start_column":1,"start_line":116}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.search_catalog", phase="error", span={"end_byte":4291,"end_column":1,"end_line":135,"start_byte":3558,"start_column":1,"start_line":116}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.search_catalog", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.catalog.search_catalog", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog_matches = _cott_match_value.value
            return (_cott_contract_condition(((len(catalog_matches) <= 1000)), "real.harlequin.catalog.search_catalog", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.catalog.search_catalog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.search_catalog", clause="ensures:1", phase="ensures", span={"end_byte":4220,"end_column":70,"end_line":129,"start_byte":4155,"start_column":5,"start_line":129}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def refresh_catalog(connection: Connection, scope: CatalogScope) -> Result[CatalogSnapshot, CatalogError]:
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
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    scope = _cott_validate_abi(scope, CatalogScope, path="$.scope")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((connection).id == "") or ((scope).connection_id != (connection).id))), "real.harlequin.catalog.refresh_catalog", "error:5:condition")):
        _expected_error = CatalogError_ConnectionMissing
        _expected_error_span = {"end_byte":13451,"end_column":108,"end_line":262,"start_byte":13348,"start_column":5,"start_line":262}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/refresh_catalog.py", "3acd0c87612dadd5c79e38f65b9f913fb2a1c2785ac1bfc89e76143de7413e16", "refresh_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.refresh_catalog")
        _result = _implementation(connection, scope)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.refresh_catalog"
        if _error.span is None:
            _error.span = {"end_byte":13605,"end_column":1,"end_line":269,"start_byte":4467,"start_column":1,"start_line":138}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.refresh_catalog", phase="implementation-call", span={"end_byte":13605,"end_column":1,"end_line":269,"start_byte":4467,"start_column":1,"start_line":138}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.refresh_catalog", phase="implementation-call", span={"end_byte":13605,"end_column":1,"end_line":269,"start_byte":4467,"start_column":1,"start_line":138}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CatalogSnapshot, CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CatalogError_NamespaceMissing, CatalogError_Failed, CatalogError_LimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.refresh_catalog", phase="error", span={"end_byte":13605,"end_column":1,"end_line":269,"start_byte":4467,"start_column":1,"start_line":138}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is CatalogError_NamespaceMissing:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", "error:6")
    if type(_result) is Err and type(_result.error) is CatalogError_Failed:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", "error:7")
    if type(_result) is Err and type(_result.error) is CatalogError_LimitExceeded:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return (_cott_contract_condition(((((snapshot).scope == scope) and (len((snapshot).relations) <= 100000))), "real.harlequin.catalog.refresh_catalog", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:1", phase="ensures", span={"end_byte":13056,"end_column":96,"end_line":257,"start_byte":12965,"start_column":5,"start_line":257}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return (_cott_contract_condition((((len((snapshot).refreshed_at) == 27) and _cott_ends_with((snapshot).refreshed_at, "Z"))), "real.harlequin.catalog.refresh_catalog", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:2", phase="ensures", span={"end_byte":13167,"end_column":111,"end_line":258,"start_byte":13061,"start_column":5,"start_line":258}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is CatalogError_ConnectionMissing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == (scope).connection_id)), "real.harlequin.catalog.refresh_catalog", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:3", phase="ensures", span={"end_byte":13265,"end_column":98,"end_line":259,"start_byte":13172,"start_column":5,"start_line":259}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is CatalogError_LimitExceeded and True:
            limit = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((limit == 100000)), "real.harlequin.catalog.refresh_catalog", "ensures:4"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:4", phase="ensures", span={"end_byte":13342,"end_column":77,"end_line":260,"start_byte":13270,"start_column":5,"start_line":260}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CatalogSnapshot, CatalogError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult:
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
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    snapshot = _cott_validate_abi(snapshot, CatalogSnapshot, path="$.snapshot")
    if not (_cott_contract_condition((((request).cursor <= len((request).source))), "real.harlequin.catalog.complete_sql", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="real.harlequin.catalog.complete_sql", clause="requires:1", phase="requires", span={"end_byte":15293,"end_column":50,"end_line":299,"start_byte":15248,"start_column":5,"start_line":299}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/complete_sql.py", "c0f2476c3a2618ea62f7f5bb9ca6f89c0092a076f61a295c96846f8032e87ed9", "complete_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.complete_sql")
        _result = _implementation(request, snapshot)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":15480,"end_column":1,"end_line":307,"start_byte":14315,"start_column":1,"start_line":285}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.complete_sql", phase="implementation-call", span={"end_byte":15480,"end_column":1,"end_line":307,"start_byte":14315,"start_column":1,"start_line":285}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.complete_sql", phase="implementation-call", span={"end_byte":15480,"end_column":1,"end_line":307,"start_byte":14315,"start_column":1,"start_line":285}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not (_cott_contract_condition((((_result).replace_end == (request).cursor)), "real.harlequin.catalog.complete_sql", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.complete_sql", clause="ensures:2", phase="ensures", span={"end_byte":15343,"end_column":49,"end_line":301,"start_byte":15299,"start_column":5,"start_line":301}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).replace_start <= (_result).replace_end)), "real.harlequin.catalog.complete_sql", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.complete_sql", clause="ensures:3", phase="ensures", span={"end_byte":15398,"end_column":55,"end_line":302,"start_byte":15348,"start_column":5,"start_line":302}, expected="true", actual="false")
    if not (_cott_contract_condition(((len((_result).candidates) <= (request).maximum_candidates)), "real.harlequin.catalog.complete_sql", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.complete_sql", clause="ensures:4", phase="ensures", span={"end_byte":15462,"end_column":64,"end_line":303,"start_byte":15403,"start_column":5,"start_line":303}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CompletionResult, path="$.return", validator=_cott_validate_abi)
    return _result

def find_catalog(snapshot: CatalogSnapshot, term: str, maximum_matches: U64) -> Result[CottList[CatalogMatch], CatalogError]:
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
    snapshot = _cott_validate_abi(snapshot, CatalogSnapshot, path="$.snapshot")
    term = _cott_validate_abi(term, str, path="$.term")
    maximum_matches = _cott_validate_abi(maximum_matches, U64, path="$.maximum_matches")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((maximum_matches > 1000)), "real.harlequin.catalog.find_catalog", "error:4:condition")):
        _expected_error = CatalogError_LimitExceeded
        _expected_error_span = {"end_byte":16677,"end_column":65,"end_line":330,"start_byte":16617,"start_column":5,"start_line":330}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/find_catalog.py", "4b102ec351d20fc4fc67366a10ecc754dc86d39f772043d1625940c2d2d9ae08", "find_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.find_catalog")
        _result = _implementation(snapshot, term, maximum_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.find_catalog"
        if _error.span is None:
            _error.span = {"end_byte":16695,"end_column":1,"end_line":334,"start_byte":15480,"start_column":1,"start_line":307}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.find_catalog", phase="implementation-call", span={"end_byte":16695,"end_column":1,"end_line":334,"start_byte":15480,"start_column":1,"start_line":307}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.find_catalog", phase="implementation-call", span={"end_byte":16695,"end_column":1,"end_line":334,"start_byte":15480,"start_column":1,"start_line":307}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.find_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.find_catalog", phase="error", span={"end_byte":16695,"end_column":1,"end_line":334,"start_byte":15480,"start_column":1,"start_line":307}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.find_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.find_catalog", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            found = _cott_match_value.value
            return (_cott_contract_condition(((len(found) <= maximum_matches)), "real.harlequin.catalog.find_catalog", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.catalog.find_catalog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.find_catalog", clause="ensures:1", phase="ensures", span={"end_byte":16516,"end_column":61,"end_line":326,"start_byte":16460,"start_column":5,"start_line":326}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is CatalogError_LimitExceeded and True:
            limit = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((limit == 1000)), "real.harlequin.catalog.find_catalog", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.catalog.find_catalog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.find_catalog", clause="ensures:2", phase="ensures", span={"end_byte":16591,"end_column":75,"end_line":327,"start_byte":16521,"start_column":5,"start_line":327}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogMatch], CatalogError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "complete_sql", "find_catalog", "refresh_catalog", "search_catalog"]
