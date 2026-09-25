from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.core_types import AdapterDescriptor as AdapterDescriptor, AdapterKind as AdapterKind, AdapterKind_Adbc as AdapterKind_Adbc, AdapterKind_BigQuery as AdapterKind_BigQuery, AdapterKind_Cassandra as AdapterKind_Cassandra, AdapterKind_Databricks as AdapterKind_Databricks, AdapterKind_DuckDb as AdapterKind_DuckDb, AdapterKind_MySql as AdapterKind_MySql, AdapterKind_NebulaGraph as AdapterKind_NebulaGraph, AdapterKind_Odbc as AdapterKind_Odbc, AdapterKind_PostgreSql as AdapterKind_PostgreSql, AdapterKind_Sqlite as AdapterKind_Sqlite, AdapterKind_Trino as AdapterKind_Trino, Cell as Cell, Cell_Blob as Cell_Blob, Cell_Integer as Cell_Integer, Cell_Null as Cell_Null, Cell_Real as Cell_Real, Cell_Text as Cell_Text, CliError as CliError, CliError_ConflictingConnectionInputs as CliError_ConflictingConnectionInputs, CliError_InvalidAdapter as CliError_InvalidAdapter, CliError_MissingOptionValue as CliError_MissingOptionValue, CliError_UnknownOption as CliError_UnknownOption, CliOptions as CliOptions, Configuration as Configuration, ConfigurationError as ConfigurationError, ConfigurationError_Invalid as ConfigurationError_Invalid, ConfigurationError_Missing as ConfigurationError_Missing, ConfigurationError_ProfileDuplicate as ConfigurationError_ProfileDuplicate, ConfigurationError_ProfileMissing as ConfigurationError_ProfileMissing, Connection as Connection, ConnectionError as ConnectionError, ConnectionError_AdapterUnavailable as ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed as ConnectionError_AuthenticationFailed, ConnectionError_Failed as ConnectionError_Failed, ConnectionError_InvalidEndpoint as ConnectionError_InvalidEndpoint, ConnectionError_LeaseRejected as ConnectionError_LeaseRejected, ConnectionError_TransactionsUnsupported as ConnectionError_TransactionsUnsupported, ConnectionProfile as ConnectionProfile, ConnectionRequest as ConnectionRequest, DatabaseTarget as DatabaseTarget, DatabaseTarget_File as DatabaseTarget_File, DatabaseTarget_Memory as DatabaseTarget_Memory, FileError as FileError, FileError_InvalidEncoding as FileError_InvalidEncoding, FileError_NotFound as FileError_NotFound, FileError_PermissionDenied as FileError_PermissionDenied, FileError_TransferFailed as FileError_TransferFailed, FileLocation as FileLocation, FileLocation_Local as FileLocation_Local, FileLocation_S3 as FileLocation_S3, FileReference as FileReference, IdeSession as IdeSession, LoadedFile as LoadedFile, QueryBatch as QueryBatch, QueryHistory as QueryHistory, QueryHistoryEntry as QueryHistoryEntry, QueryResult as QueryResult, QueryTab as QueryTab, SavedFile as SavedFile, SessionError as SessionError, SessionError_TabMissing as SessionError_TabMissing, SessionHandle as SessionHandle, Setting as Setting, SqlClientError as SqlClientError, SqlClientError_Cancelled as SqlClientError_Cancelled, SqlClientError_EmptySql as SqlClientError_EmptySql, SqlClientError_ExecutionFailed as SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation as SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded as SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure as SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue as SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql as SqlClientError_UnterminatedSql, Transaction as Transaction, TransactionLease as TransactionLease, TransactionStatus as TransactionStatus, TransactionStatus_Active as TransactionStatus_Active, TransactionStatus_Committed as TransactionStatus_Committed, TransactionStatus_RolledBack as TransactionStatus_RolledBack, TypedRow as TypedRow
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
def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]: ...

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
def load_configuration(path: Path) -> Result[Configuration, ConfigurationError]: ...

"""Plan the connection request without I/O. With options.no_config the
configuration is ignored, as if it had no profiles and no default_profile.
The selected profile name is options.profile, else configuration.default_profile,
else none. A selected name without a profile of exactly that name is
ProfileMissing(name). With no selected name the base request is DuckDb, endpoint
":memory:", no settings and read_only false; otherwise it is the profile's
adapter, endpoint, settings and read_only. Then options.adapter replaces the
adapter, options.connection replaces the endpoint, and options.read_only true
makes the request read-only. Settings always come from the profile."""
def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]: ...

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
def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]: ...

"""Validate SessionHandle and lock it. If already closed, return Unit successfully.
Otherwise invalidate the active lease and mark closed before cleanup, so no
stale handle can regain authority even if the SDK reports a close failure.
Roll back an outstanding supported transaction on this same driver, then close
the ExitStack so every registered callback is attempted. Do not commit or
reopen any connection. Cleanup failure returns Failed with a fixed message;
success returns Unit. No resource is transferred to a hidden registry."""
def disconnect(connection: Connection) -> Result[Unit, ConnectionError]: ...

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
def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]: ...

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
def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]: ...

"""Apply the same status and lease-authority checks as commit_transaction, with the
same LeaseRejected results, but call the existing SDK driver's rollback. Success
clears the active lease and returns the same connection and lease with
status=RolledBack. Double completion, stale leases and disconnected sessions are
never successful no-ops. A driver failure clears the lease, marks the session
closed, attempts all cleanup callbacks and returns Failed with a fixed nonsecret
message."""
def rollback_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]: ...

def open_query_tab(id: str, title: str, source: str) -> QueryTab: ...

"""Replace the tab's source and move its cursor, clamped to the end of source.
The tab becomes dirty when source differs from its previous source."""
def edit_query_tab(tab: QueryTab, source: str, cursor: U64) -> QueryTab: ...

"""Append entry as the newest entry; when history is full, drop the oldest entries
so that at most capacity remain."""
def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory: ...

"""Start editor state for connection: no tabs, no active tab, empty history with
history_capacity."""
def start_session(connection: Connection, history_capacity: U64) -> IdeSession: ...

"""A tab with the same id is replaced in place; otherwise tab is appended.
The added tab becomes active."""
def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession: ...

"""Make the tab with tab_id active. An unknown id is TabMissing(tab_id)."""
def activate_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]: ...

"""Remove the tab with tab_id, keeping the order of the others. When it was active,
the tab that followed it becomes active, else the tab that preceded it, else
none; otherwise the active tab is unchanged. An unknown id is TabMissing(tab_id)."""
def close_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]: ...

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
def split_statements(sql: str) -> Result[CottList[str], SqlClientError]: ...

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
def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]: ...

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
def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]: ...

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
def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]: ...

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
def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]: ...

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
def run(arguments: CottList[str]) -> Never: ...

__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_PostgreSql", "AdapterKind_Sqlite", "AdapterKind_Trino", "Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "CliError", "CliError_ConflictingConnectionInputs", "CliError_InvalidAdapter", "CliError_MissingOptionValue", "CliError_UnknownOption", "CliOptions", "Configuration", "ConfigurationError", "ConfigurationError_Invalid", "ConfigurationError_Missing", "ConfigurationError_ProfileDuplicate", "ConfigurationError_ProfileMissing", "Connection", "ConnectionError", "ConnectionError_AdapterUnavailable", "ConnectionError_AuthenticationFailed", "ConnectionError_Failed", "ConnectionError_InvalidEndpoint", "ConnectionError_LeaseRejected", "ConnectionError_TransactionsUnsupported", "ConnectionProfile", "ConnectionRequest", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "FileError", "FileError_InvalidEncoding", "FileError_NotFound", "FileError_PermissionDenied", "FileError_TransferFailed", "FileLocation", "FileLocation_Local", "FileLocation_S3", "FileReference", "IdeSession", "LoadedFile", "QueryBatch", "QueryHistory", "QueryHistoryEntry", "QueryResult", "QueryTab", "SavedFile", "SessionError", "SessionError_TabMissing", "SessionHandle", "Setting", "SqlClientError", "SqlClientError_Cancelled", "SqlClientError_EmptySql", "SqlClientError_ExecutionFailed", "SqlClientError_ReadOnlyViolation", "SqlClientError_ResultLimitExceeded", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "Transaction", "TransactionLease", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Committed", "TransactionStatus_RolledBack", "TypedRow", "activate_query_tab", "adapter_descriptors", "add_query_tab", "append_query_history", "begin_transaction", "close_query_tab", "commit_transaction", "connect", "disconnect", "edit_query_tab", "execute_sql", "execute_statements", "load_configuration", "load_query_file", "open_query_tab", "parse_cli", "resolve_profile", "rollback_transaction", "run", "save_query_file", "split_statements", "start_session"]
