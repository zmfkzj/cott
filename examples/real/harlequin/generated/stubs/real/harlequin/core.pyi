from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.core_types import AdapterDescriptor as AdapterDescriptor, AdapterKind as AdapterKind, AdapterKind_Adbc as AdapterKind_Adbc, AdapterKind_BigQuery as AdapterKind_BigQuery, AdapterKind_Cassandra as AdapterKind_Cassandra, AdapterKind_Databricks as AdapterKind_Databricks, AdapterKind_DuckDb as AdapterKind_DuckDb, AdapterKind_MySql as AdapterKind_MySql, AdapterKind_NebulaGraph as AdapterKind_NebulaGraph, AdapterKind_Odbc as AdapterKind_Odbc, AdapterKind_PostgreSql as AdapterKind_PostgreSql, AdapterKind_Sqlite as AdapterKind_Sqlite, AdapterKind_Trino as AdapterKind_Trino, Cell as Cell, Cell_Blob as Cell_Blob, Cell_Integer as Cell_Integer, Cell_Null as Cell_Null, Cell_Real as Cell_Real, Cell_Text as Cell_Text, CliError as CliError, CliError_ConflictingConnectionInputs as CliError_ConflictingConnectionInputs, CliError_InvalidAdapter as CliError_InvalidAdapter, CliError_MissingOptionValue as CliError_MissingOptionValue, CliError_UnknownOption as CliError_UnknownOption, CliOptions as CliOptions, Configuration as Configuration, ConfigurationError as ConfigurationError, ConfigurationError_Invalid as ConfigurationError_Invalid, ConfigurationError_Missing as ConfigurationError_Missing, ConfigurationError_ProfileDuplicate as ConfigurationError_ProfileDuplicate, ConfigurationError_ProfileMissing as ConfigurationError_ProfileMissing, Connection as Connection, ConnectionError as ConnectionError, ConnectionError_AdapterUnavailable as ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed as ConnectionError_AuthenticationFailed, ConnectionError_Failed as ConnectionError_Failed, ConnectionError_InvalidEndpoint as ConnectionError_InvalidEndpoint, ConnectionProfile as ConnectionProfile, ConnectionRequest as ConnectionRequest, DatabaseTarget as DatabaseTarget, DatabaseTarget_File as DatabaseTarget_File, DatabaseTarget_Memory as DatabaseTarget_Memory, FileError as FileError, FileError_InvalidEncoding as FileError_InvalidEncoding, FileError_NotFound as FileError_NotFound, FileError_PermissionDenied as FileError_PermissionDenied, FileError_TransferFailed as FileError_TransferFailed, FileLocation as FileLocation, FileLocation_Local as FileLocation_Local, FileLocation_S3 as FileLocation_S3, FileReference as FileReference, IdeSession as IdeSession, LoadedFile as LoadedFile, QueryBatch as QueryBatch, QueryHistory as QueryHistory, QueryHistoryEntry as QueryHistoryEntry, QueryResult as QueryResult, QueryTab as QueryTab, SavedFile as SavedFile, SessionError as SessionError, SessionError_HistoryCapacityInvalid as SessionError_HistoryCapacityInvalid, SessionError_TabMissing as SessionError_TabMissing, SessionHandle as SessionHandle, Setting as Setting, SqlClientError as SqlClientError, SqlClientError_Cancelled as SqlClientError_Cancelled, SqlClientError_EmptySql as SqlClientError_EmptySql, SqlClientError_ExecutionFailed as SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation as SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded as SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure as SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue as SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql as SqlClientError_UnterminatedSql, Transaction as Transaction, TransactionLease as TransactionLease, TypedRow as TypedRow
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
def adapter_descriptors() -> CottList[AdapterDescriptor]: ...

def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]: ...

"""Use tomllib; cast each dict/list to dict[str, object]/list[object] before use."""
def load_configuration(path: Path) -> Result[Configuration, ConfigurationError]: ...

"""Use isinstance, not match, for each Option; select the named or default profile."""
def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]: ...

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
def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]: ...

"""Validate SessionHandle and lock it. If already closed, return Unit successfully.
Otherwise invalidate the active lease and mark closed before cleanup, so no
stale handle can regain authority even if the SDK reports a close failure.
Roll back an outstanding supported transaction on this same driver, then close
the ExitStack so every registered callback is attempted. Do not commit or
reopen any connection. Cleanup failure returns Failed with a fixed message;
success returns Unit. No resource is transferred to a hidden registry."""
def disconnect(connection: Connection) -> Result[Unit, ConnectionError]: ...

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
def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]: ...

"""Borrow transaction.connection and acquire its session lock. Require active=true,
an open matching SessionHandle, and exact lease object identity with its active
transaction. Reject a stale, already-finished, disconnected or wrong-owner
lease as Failed without touching a different session.
Call the actual existing SDK driver's commit. Never reconnect by id/endpoint.
On success clear the active lease and return the same connection and lease
with active=false. On a driver failure, clear the lease, mark the session closed,
attempt rollback and every registered cleanup callback, and return Failed with
a fixed nonsecret message; do not leave an ambiguously reusable transaction."""
def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]: ...

"""Apply the same ownership and live-lease requirements as commit_transaction,
but call the existing SDK driver's rollback. Success clears the active lease
and returns the same connection and lease with active=false. Double completion,
stale leases and disconnected sessions are Failed, never successful no-ops.
A driver failure clears the lease, marks the session closed, attempts all
cleanup callbacks and returns Failed with a fixed nonsecret message."""
def rollback_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]: ...

def open_query_tab(id: str, title: str, source: str) -> QueryTab: ...

def edit_query_tab(tab: QueryTab, source: str, cursor: U64) -> QueryTab: ...

def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory: ...

def start_session(connection: Connection, history_capacity: U64) -> IdeSession: ...

def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession: ...

def activate_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]: ...

"""Use isinstance checks, not match, for active_tab_id."""
def close_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]: ...

def split_statements(sql: str) -> Result[CottList[str], SqlClientError]: ...

def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]: ...

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
def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]: ...

"""Set sdk: Any = boto3; client: Any = sdk.client("s3"); decode Body to source: str."""
def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]: ...

def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]: ...

"""Parse/connect; read SQL at sql> until .quit/EOF; execute and print tab-separated results."""
def run(arguments: CottList[str]) -> Never: ...

__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_HistoryCapacityInvalid", "SessionError_TabMissing", "SessionHandle", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TransactionLease", "TypedRow", "activate_query_tab", "adapter_descriptors", "add_query_tab", "append_query_history", "begin_transaction", "close_query_tab", "commit_transaction", "connect", "disconnect", "edit_query_tab", "execute_sql", "execute_statements", "load_configuration", "load_query_file", "open_query_tab", "parse_cli", "resolve_profile", "rollback_transaction", "run", "save_query_file", "split_statements", "start_session"]
