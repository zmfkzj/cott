from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.catalog_types import CatalogColumn, CatalogError, CatalogError_ConnectionMissing, CatalogError_Failed, CatalogError_LimitExceeded, CatalogError_NamespaceMissing, CatalogMatch, CatalogMatchKind, CatalogMatchKind_Column, CatalogMatchKind_Relation, CatalogRelation, CatalogScope, CatalogSnapshot, CompletionRequest, CompletionResult, RelationKind, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError

def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_relations.py", "90b7f10239c14389d9b615f85c14891a749605b5ff005cbe0242efa9208e1519", "catalog_relations", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_relations")
        _result = _implementation(database)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_relations"
        if _error.span is None:
            _error.span = {"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_relations", phase="implementation-call", span={"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_relations", phase="error", span={"end_byte":1310,"end_column":1,"end_line":66,"start_byte":1083,"start_column":1,"start_line":59}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_relations", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_relations", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_relations", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            relations = _cott_match_value.value
            return (_cott_contract_condition(((len(relations) <= 100000)), "real.harlequin.catalog.catalog_relations", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.catalog.catalog_relations", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_relations", clause="ensures:0", phase="ensures", span={"end_byte":1239,"end_column":60,"end_line":60,"start_byte":1184,"start_column":5,"start_line":60}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogRelation], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    relation = _cott_validate_abi(relation, str, path="$.relation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_columns.py", "5589396eaffa7c7472e52c8eab8128ebfaaa235363dc3dcac3a9fccee8c36224", "catalog_columns", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_columns")
        _result = _implementation(database, relation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_columns"
        if _error.span is None:
            _error.span = {"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_columns", phase="implementation-call", span={"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.catalog_columns", phase="error", span={"end_byte":1554,"end_column":1,"end_line":76,"start_byte":1310,"start_column":1,"start_line":66}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.catalog_columns", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_columns", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.catalog.catalog_columns", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            columns = _cott_match_value.value
            return (_cott_contract_condition(((len(columns) <= 65535)), "real.harlequin.catalog.catalog_columns", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.catalog.catalog_columns", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_columns", clause="ensures:0", phase="ensures", span={"end_byte":1483,"end_column":55,"end_line":70,"start_byte":1433,"start_column":5,"start_line":70}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogColumn], SqlClientError], path="$.return", validator=_cott_validate_abi)
    return _result

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    database = _cott_validate_abi(database, DatabaseTarget, path="$.database")
    term = _cott_validate_abi(term, str, path="$.term")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/search_catalog.py", "6f53c42dbe2454afc7c3c20b17717b91682098a74941a12e250aed3a09e3ce51", "search_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.search_catalog")
        _result = _implementation(database, term)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.search_catalog"
        if _error.span is None:
            _error.span = {"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.search_catalog", phase="implementation-call", span={"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], SqlClientError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SqlClientError_SqliteFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.search_catalog", phase="error", span={"end_byte":1807,"end_column":1,"end_line":86,"start_byte":1554,"start_column":1,"start_line":76}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.search_catalog", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is SqlClientError_SqliteFailure:
        _cott_contract_condition(True, "real.harlequin.catalog.search_catalog", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            catalog_matches = _cott_match_value.value
            return (_cott_contract_condition(((len(catalog_matches) <= 1000)), "real.harlequin.catalog.search_catalog", "ensures:0"))
        _cott_contract_condition((False), "real.harlequin.catalog.search_catalog", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.search_catalog", clause="ensures:0", phase="ensures", span={"end_byte":1736,"end_column":70,"end_line":80,"start_byte":1671,"start_column":5,"start_line":80}, expected="true", actual="false")
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
ISO-8601 with six fractional digits and a trailing Z. No empty/stub timestamp."""
    connection = _cott_validate_abi(connection, Connection, path="$.connection")
    scope = _cott_validate_abi(scope, CatalogScope, path="$.scope")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((connection).id == "") or ((scope).connection_id != (connection).id))), "real.harlequin.catalog.refresh_catalog", "error:7:condition")):
        _expected_error = CatalogError_ConnectionMissing
        _expected_error_span = {"end_byte":10879,"end_column":108,"end_line":212,"start_byte":10776,"start_column":5,"start_line":212}
        _expected_error_clause = "error:7"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/refresh_catalog.py", "3acd0c87612dadd5c79e38f65b9f913fb2a1c2785ac1bfc89e76143de7413e16", "refresh_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.refresh_catalog")
        _result = _implementation(connection, scope)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.refresh_catalog"
        if _error.span is None:
            _error.span = {"end_byte":11033,"end_column":1,"end_line":219,"start_byte":1807,"start_column":1,"start_line":86}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.refresh_catalog", phase="implementation-call", span={"end_byte":11033,"end_column":1,"end_line":219,"start_byte":1807,"start_column":1,"start_line":86}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.refresh_catalog", phase="implementation-call", span={"end_byte":11033,"end_column":1,"end_line":219,"start_byte":1807,"start_column":1,"start_line":86}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CatalogSnapshot, CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CatalogError_NamespaceMissing, CatalogError_Failed, CatalogError_LimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.refresh_catalog", phase="error", span={"end_byte":11033,"end_column":1,"end_line":219,"start_byte":1807,"start_column":1,"start_line":86}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.refresh_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is CatalogError_NamespaceMissing:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", "error:8")
    if type(_result) is Err and type(_result.error) is CatalogError_Failed:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", "error:9")
    if type(_result) is Err and type(_result.error) is CatalogError_LimitExceeded:
        _cott_contract_condition(True, "real.harlequin.catalog.refresh_catalog", "error:10")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return (_cott_contract_condition(((len((snapshot).relations) <= 100000)), "real.harlequin.catalog.refresh_catalog", "ensures:1"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:1", phase="ensures", span={"end_byte":10373,"end_column":68,"end_line":205,"start_byte":10310,"start_column":5,"start_line":205}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return (_cott_contract_condition((((snapshot).scope == scope)), "real.harlequin.catalog.refresh_catalog", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:2", phase="ensures", span={"end_byte":10432,"end_column":59,"end_line":206,"start_byte":10378,"start_column":5,"start_line":206}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return (_cott_contract_condition(((len((snapshot).refreshed_at) > 0)), "real.harlequin.catalog.refresh_catalog", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:3", phase="ensures", span={"end_byte":10497,"end_column":65,"end_line":207,"start_byte":10437,"start_column":5,"start_line":207}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            snapshot = _cott_match_value.value
            return (_cott_contract_condition((((len((connection).id) > 0) and ((scope).connection_id == (connection).id))), "real.harlequin.catalog.refresh_catalog", "ensures:4"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:4", phase="ensures", span={"end_byte":10595,"end_column":98,"end_line":208,"start_byte":10502,"start_column":5,"start_line":208}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is CatalogError_ConnectionMissing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == (scope).connection_id)), "real.harlequin.catalog.refresh_catalog", "ensures:5"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:5", phase="ensures", span={"end_byte":10693,"end_column":98,"end_line":209,"start_byte":10600,"start_column":5,"start_line":209}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is CatalogError_LimitExceeded and True:
            limit = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((limit == 100000)), "real.harlequin.catalog.refresh_catalog", "ensures:6"))
        _cott_contract_condition((False), "real.harlequin.catalog.refresh_catalog", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.refresh_catalog", clause="ensures:6", phase="ensures", span={"end_byte":10770,"end_column":77,"end_line":210,"start_byte":10698,"start_column":5,"start_line":210}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CatalogSnapshot, CatalogError], path="$.return", validator=_cott_validate_abi)
    return _result

def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult:
    request = _cott_validate_abi(request, CompletionRequest, path="$.request")
    snapshot = _cott_validate_abi(snapshot, CatalogSnapshot, path="$.snapshot")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/complete_sql.py", "db485122aee380d8d90fb1b8cd58faf42e4f51c3f8299af86e069d48152524b4", "complete_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.complete_sql")
        _result = _implementation(request, snapshot)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.complete_sql"
        if _error.span is None:
            _error.span = {"end_byte":11206,"end_column":1,"end_line":224,"start_byte":11033,"start_column":1,"start_line":219}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.complete_sql", phase="implementation-call", span={"end_byte":11206,"end_column":1,"end_line":224,"start_byte":11033,"start_column":1,"start_line":219}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.complete_sql", phase="implementation-call", span={"end_byte":11206,"end_column":1,"end_line":224,"start_byte":11033,"start_column":1,"start_line":219}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CompletionResult, path="$.return")
    if not (_cott_contract_condition(((len((_result).candidates) <= (request).maximum_candidates)), "real.harlequin.catalog.complete_sql", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.complete_sql", clause="ensures:0", phase="ensures", span={"end_byte":11188,"end_column":64,"end_line":220,"start_byte":11129,"start_column":5,"start_line":220}, expected="true", actual="false")
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
        _expected_error_span = {"end_byte":12439,"end_column":65,"end_line":247,"start_byte":12379,"start_column":5,"start_line":247}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/find_catalog.py", "ce24a4f9799bb3e2f0eb2dec940f88fe1b5206cca4fd582ab58a47d104f9ee1d", "find_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.find_catalog")
        _result = _implementation(snapshot, term, maximum_matches)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.find_catalog"
        if _error.span is None:
            _error.span = {"end_byte":12456,"end_column":1,"end_line":250,"start_byte":11206,"start_column":1,"start_line":224}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.find_catalog", phase="implementation-call", span={"end_byte":12456,"end_column":1,"end_line":250,"start_byte":11206,"start_column":1,"start_line":224}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.find_catalog", phase="implementation-call", span={"end_byte":12456,"end_column":1,"end_line":250,"start_byte":11206,"start_column":1,"start_line":224}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CatalogMatch], CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.find_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.find_catalog", phase="error", span={"end_byte":12456,"end_column":1,"end_line":250,"start_byte":11206,"start_column":1,"start_line":224}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.find_catalog", clause="ensures:1", phase="ensures", span={"end_byte":12242,"end_column":61,"end_line":243,"start_byte":12186,"start_column":5,"start_line":243}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            found = _cott_match_value.value
            return (_cott_contract_condition(((maximum_matches <= 1000)), "real.harlequin.catalog.find_catalog", "ensures:2"))
        _cott_contract_condition((False), "real.harlequin.catalog.find_catalog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.find_catalog", clause="ensures:2", phase="ensures", span={"end_byte":12298,"end_column":56,"end_line":244,"start_byte":12247,"start_column":5,"start_line":244}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is CatalogError_LimitExceeded and True:
            limit = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((limit == 1000)), "real.harlequin.catalog.find_catalog", "ensures:3"))
        _cott_contract_condition((False), "real.harlequin.catalog.find_catalog", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.find_catalog", clause="ensures:3", phase="ensures", span={"end_byte":12373,"end_column":75,"end_line":245,"start_byte":12303,"start_column":5,"start_line":245}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogMatch], CatalogError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "complete_sql", "find_catalog", "refresh_catalog", "search_catalog"]
