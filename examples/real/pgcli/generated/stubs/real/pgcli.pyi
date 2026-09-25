from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli_types import BackslashCommand as BackslashCommand, BackslashCommand_Describe as BackslashCommand_Describe, BackslashCommand_Help as BackslashCommand_Help, BackslashCommand_Quit as BackslashCommand_Quit, BackslashCommand_Tables as BackslashCommand_Tables, BackslashCommand_Unknown as BackslashCommand_Unknown, Catalog as Catalog, CatalogRefreshRequest as CatalogRefreshRequest, CliCommand as CliCommand, CliCommand_Help as CliCommand_Help, CliCommand_Session as CliCommand_Session, ClientCertificate as ClientCertificate, ClientError as ClientError, ClientError_CatalogFailed as ClientError_CatalogFailed, ClientError_ConnectionFailed as ClientError_ConnectionFailed, ClientError_EditorFailed as ClientError_EditorFailed, ClientError_ExportFailed as ClientError_ExportFailed, ClientError_FavoriteFailed as ClientError_FavoriteFailed, ClientError_HistoryFailed as ClientError_HistoryFailed, ClientError_ImportFailed as ClientError_ImportFailed, ClientError_InvalidArguments as ClientError_InvalidArguments, ClientError_InvalidCommand as ClientError_InvalidCommand, ClientError_InvalidSql as ClientError_InvalidSql, ClientError_NotificationFailed as ClientError_NotificationFailed, ClientError_PagerFailed as ClientError_PagerFailed, ClientError_QueryFailed as ClientError_QueryFailed, ClientError_TerminalFailed as ClientError_TerminalFailed, ClientError_TransactionFailed as ClientError_TransactionFailed, ClientError_TunnelUnsupported as ClientError_TunnelUnsupported, ClientError_UnsupportedFormat as ClientError_UnsupportedFormat, ColumnCatalog as ColumnCatalog, CommandInvocation as CommandInvocation, CommandResult as CommandResult, CompletionPolicy as CompletionPolicy, CompletionRequest as CompletionRequest, CompletionResult as CompletionResult, ConnectionError as ConnectionError, ConnectionError_ConnectionFailed as ConnectionError_ConnectionFailed, ConnectionError_CredentialUnavailable as ConnectionError_CredentialUnavailable, ConnectionError_InvalidDsn as ConnectionError_InvalidDsn, ConnectionError_InvalidPort as ConnectionError_InvalidPort, ConnectionError_MissingDatabase as ConnectionError_MissingDatabase, ConnectionError_ProfileMissing as ConnectionError_ProfileMissing, ConnectionError_PromptDisabled as ConnectionError_PromptDisabled, ConnectionError_SshInvalid as ConnectionError_SshInvalid, ConnectionInputs as ConnectionInputs, ConnectionPlan as ConnectionPlan, ConnectionProfile as ConnectionProfile, ConnectionReceipt as ConnectionReceipt, ConnectionRequest as ConnectionRequest, ConnectionSettings as ConnectionSettings, CredentialRequest as CredentialRequest, CredentialResolution as CredentialResolution, DatabaseError as DatabaseError, DatabaseError_ConnectionFailed as DatabaseError_ConnectionFailed, DatabaseError_QueryFailed as DatabaseError_QueryFailed, EditorRequest as EditorRequest, EnvironmentInputs as EnvironmentInputs, ExecutedQuery as ExecutedQuery, ExportRequest as ExportRequest, Favorite as Favorite, FavoriteStore as FavoriteStore, FormatRequest as FormatRequest, FormattedQuery as FormattedQuery, HighlightRequest as HighlightRequest, HighlightedSql as HighlightedSql, HistoryEntry as HistoryEntry, HistoryPolicy as HistoryPolicy, ImportRequest as ImportRequest, InputBuffer as InputBuffer, InteractiveRequest as InteractiveRequest, MetaCommand as MetaCommand, MetaCommand_Connect as MetaCommand_Connect, MetaCommand_ConnectionInfo as MetaCommand_ConnectionInfo, MetaCommand_Copy as MetaCommand_Copy, MetaCommand_DeleteFavorite as MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery as MetaCommand_DeleteNamedQuery, MetaCommand_Describe as MetaCommand_Describe, MetaCommand_Echo as MetaCommand_Echo, MetaCommand_EditBuffer as MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer as MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded as MetaCommand_ExecuteExpanded, MetaCommand_Expanded as MetaCommand_Expanded, MetaCommand_Favorite as MetaCommand_Favorite, MetaCommand_Help as MetaCommand_Help, MetaCommand_History as MetaCommand_History, MetaCommand_ListDataTypes as MetaCommand_ListDataTypes, MetaCommand_ListDatabases as MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges as MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains as MetaCommand_ListDomains, MetaCommand_ListExtensions as MetaCommand_ListExtensions, MetaCommand_ListFavorites as MetaCommand_ListFavorites, MetaCommand_ListForeignTables as MetaCommand_ListForeignTables, MetaCommand_ListFunctions as MetaCommand_ListFunctions, MetaCommand_ListIndexes as MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews as MetaCommand_ListMaterializedViews, MetaCommand_ListPrivileges as MetaCommand_ListPrivileges, MetaCommand_ListRoles as MetaCommand_ListRoles, MetaCommand_ListSchemas as MetaCommand_ListSchemas, MetaCommand_ListSequences as MetaCommand_ListSequences, MetaCommand_ListTables as MetaCommand_ListTables, MetaCommand_ListTablespaces as MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations as MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews as MetaCommand_ListViews, MetaCommand_NamedQuery as MetaCommand_NamedQuery, MetaCommand_PrintBuffer as MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery as MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho as MetaCommand_QueryOutputEcho, MetaCommand_Quit as MetaCommand_Quit, MetaCommand_ReadFile as MetaCommand_ReadFile, MetaCommand_ReadRelativeFile as MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog as MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer as MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery as MetaCommand_SaveNamedQuery, MetaCommand_SetFormat as MetaCommand_SetFormat, MetaCommand_SetPager as MetaCommand_SetPager, MetaCommand_ShowFunction as MetaCommand_ShowFunction, MetaCommand_SqlHelp as MetaCommand_SqlHelp, MetaCommand_Timing as MetaCommand_Timing, MetaCommand_Unknown as MetaCommand_Unknown, MetaCommand_WriteBuffer as MetaCommand_WriteBuffer, Notification as Notification, NotificationRequest as NotificationRequest, PagerRequest as PagerRequest, PasswordSource as PasswordSource, PasswordSource_Environment as PasswordSource_Environment, PasswordSource_Keyring as PasswordSource_Keyring, PasswordSource_None as PasswordSource_None, PasswordSource_Prompt as PasswordSource_Prompt, PasswordSource_Supplied as PasswordSource_Supplied, PromptAction as PromptAction, PromptAction_PromptPassword as PromptAction_PromptPassword, PromptAction_UsePassword as PromptAction_UsePassword, QueryPlan as QueryPlan, QueryRequest as QueryRequest, QueryResult as QueryResult, RelationCatalog as RelationCatalog, RenderLayout as RenderLayout, RenderLayout_Horizontal as RenderLayout_Horizontal, RenderLayout_Vertical as RenderLayout_Vertical, RenderRequest as RenderRequest, RenderedQuery as RenderedQuery, RoutineCatalog as RoutineCatalog, SQL_KEYWORDS as SQL_KEYWORDS, SessionMode as SessionMode, SessionMode_ExecuteOnce as SessionMode_ExecuteOnce, SessionMode_Interactive as SessionMode_Interactive, SessionOptions as SessionOptions, SessionReport as SessionReport, SshSettings as SshSettings, TableCatalog as TableCatalog, TableFormat as TableFormat, TableFormat_Aligned as TableFormat_Aligned, TableFormat_Csv as TableFormat_Csv, TableFormat_Html as TableFormat_Html, TableFormat_Json as TableFormat_Json, TableFormat_JsonLines as TableFormat_JsonLines, TableFormat_Latex as TableFormat_Latex, TableFormat_Markdown as TableFormat_Markdown, TableFormat_Tsv as TableFormat_Tsv, TableFormat_Vertical as TableFormat_Vertical, TlsMode as TlsMode, TlsMode_Allow as TlsMode_Allow, TlsMode_Default as TlsMode_Default, TlsMode_Disable as TlsMode_Disable, TlsMode_Prefer as TlsMode_Prefer, TlsMode_Require as TlsMode_Require, TlsMode_VerifyCa as TlsMode_VerifyCa, TlsMode_VerifyFull as TlsMode_VerifyFull, TlsSettings as TlsSettings, TransactionMode as TransactionMode, TransactionMode_AutoCommit as TransactionMode_AutoCommit, TransactionMode_Manual as TransactionMode_Manual, TransactionMode_ReadOnly as TransactionMode_ReadOnly, TransactionState as TransactionState, TransactionStatus as TransactionStatus, TransactionStatus_Active as TransactionStatus_Active, TransactionStatus_Failed as TransactionStatus_Failed, TransactionStatus_Idle as TransactionStatus_Idle, TransferResult as TransferResult, WatchRequest as WatchRequest, WatchResult as WatchResult
"""Parse value as one libpq connection string: a postgresql:// or postgres://
URI (percent-decoded) or whitespace-separated key=value pairs. Return its
host, port, user, password and dbname parameters verbatim; an absent
parameter is "". A string libpq cannot parse, and one that names no
database, is InvalidDsn whose value is a fixed category message that never
contains any part of the input, which may include a password."""
def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]: ...

"""Return the first profile in list order whose name equals name exactly
(case-sensitive, no trimming); when none does, return ProfileMissing(name: name)."""
def resolve_profile(name: str, profiles: CottList[ConnectionProfile]) -> Result[ConnectionProfile, ConnectionError]: ...

"""Merge explicit inputs over environment values field by field. The merged
database must be nonempty. A nonempty merged port must consist of ASCII
digits denoting 1..65535, otherwise return InvalidPort(value: the merged
port); an empty port stays empty and means libpq's default."""
def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]: ...

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
def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]: ...

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
def parse_arguments(arguments: CottList[str], environment: EnvironmentInputs) -> Result[CliCommand, ClientError]: ...

"""Decide how to obtain a password: a nonempty password is used as is; an empty
one is prompted for unless prompting is disabled."""
def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]: ...

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
def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]: ...

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
def connect(plan: ConnectionPlan) -> Result[ConnectionReceipt, ConnectionError]: ...

"""Open an explicit transaction in the client's transaction model."""
def begin_transaction(mode: TransactionMode) -> TransactionState: ...

"""Commit the open transaction. Committing when no transaction is open, or after
it failed (PostgreSQL rolls a failed transaction back instead), is
TransactionFailed."""
def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]: ...

"""Roll back an open or failed transaction. Rolling back when no transaction is
open is TransactionFailed."""
def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]: ...

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
def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult: ...

"""Complete with the default interactive policy: the result is exactly
complete_catalog_sql(request, CompletionPolicy(max_candidates: 50,
include_keywords: true))."""
def complete_sql(request: CompletionRequest) -> CompletionResult: ...

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
def highlight_sql(request: HighlightRequest) -> HighlightedSql: ...

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
def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]: ...

"""Insert input into buffer.text at buffer.cursor and move the cursor to the end
of the inserted text."""
def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer: ...

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
def parse_meta_command(source: str) -> MetaCommand: ...

"""Classify source through parse_meta_command(source): Quit -> Quit, Help -> Help,
ListTables -> Tables, Describe -> Describe, every other command -> Unknown."""
def recognize_backslash(source: str) -> BackslashCommand: ...

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
def render_query(request: RenderRequest) -> RenderedQuery: ...

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
def format_query(request: FormatRequest) -> FormattedQuery: ...

"""Append entry to entries, then apply HistoryPolicy normalization. This is a
pure list transformation with no clock or filesystem access."""
def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]: ...

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
def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]: ...

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
def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]: ...

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
def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]: ...

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
def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]: ...

"""Run sql once on a new autocommit connection built only from the nonempty
fields of connection (host, port, user, password, dbname; libpq defaults
otherwise; no connection string, TLS settings or SSH hop), then close it.
Return the columns and all rows of the last statement that produced rows, in
server order, with QueryResult cell text; no columns and no rows when no
statement produced rows. Failing to open the connection or authenticate is
ConnectionFailed; a statement error is QueryFailed."""
def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]: ...

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
def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]: ...

"""Execute request.query max_iterations times through execute_planned_query,
waiting interval_ms milliseconds between consecutive executions and not
after the last. The first failing execution stops the watch and its error is
returned unchanged. last_result is the final execution's result."""
def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]: ...

"""Read a Catalog snapshot through one read-only connection with the
ConnectionPlan parameters using fixed, parameterized catalog queries, then
close the connection. Connection and query failures are CatalogFailed."""
def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]: ...

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
def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]: ...

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
def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]: ...

"""LISTEN on every channel, each quoted as an SQL identifier, over one
autocommit connection with the ConnectionPlan parameters. Collect
notifications in arrival order until max_notifications have arrived or
timeout_ms monotonic milliseconds have passed since listening began,
whichever comes first; each carries its channel, payload and sender pid.
UNLISTEN and close the connection on every path. Connection and listening
failures are NotificationFailed."""
def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]: ...

"""Write buffer.text as UTF-8 to temporary_path, start the editor on it and wait
for it to exit, then read the file back. editor is split into words at
whitespace (no shell) and temporary_path is appended as the last argument; the
editor inherits the terminal. A zero exit status returns the file's text
without one trailing line feed, with the cursor at its end and
buffer.multiline kept. temporary_path is removed on every path. A missing
editor executable, a nonzero exit or signal, and I/O or decoding failures
are EditorFailed with a fixed category message."""
def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]: ...

"""Show text on the terminal. When enabled is false, or text has at most
terminal_height lines, write text and one line feed to standard output.
Otherwise start the pager command, split into words at whitespace (no shell),
with text and one line feed on its standard input, and wait for it to exit;
a pager that exits with status 0 after closing its input early succeeds.
A pager that cannot start or exits nonzero, and a failed write to standard
output, are PagerFailed with a fixed category message."""
def page_output(request: PagerRequest) -> Result[Unit, ClientError]: ...

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
def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]: ...

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
def run_interactive(request: InteractiveRequest) -> Result[SessionReport, ClientError]: ...

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
def run(arguments: CottList[str]) -> Never: ...

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "CliCommand", "CliCommand_Help", "CliCommand_Session", "ClientCertificate", "ClientError", "ClientError_CatalogFailed", "ClientError_ConnectionFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidArguments", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_TunnelUnsupported", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionReceipt", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetPager", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SQL_KEYWORDS", "SessionMode", "SessionMode_ExecuteOnce", "SessionMode_Interactive", "SessionOptions", "SessionReport", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsMode", "TlsMode_Allow", "TlsMode_Default", "TlsMode_Disable", "TlsMode_Prefer", "TlsMode_Require", "TlsMode_VerifyCa", "TlsMode_VerifyFull", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Failed", "TransactionStatus_Idle", "TransferResult", "WatchRequest", "WatchResult", "begin_transaction", "commit_transaction", "complete_catalog_sql", "complete_sql", "connect", "edit_in_editor", "edit_multiline", "execute_planned_query", "execute_query", "export_query", "format_query", "highlight_sql", "import_delimited", "load_favorites", "load_history", "page_output", "parse_arguments", "parse_dsn", "parse_meta_command", "plan_query", "prompt_policy", "receive_notifications", "recognize_backslash", "refresh_catalog", "remember_history", "render_query", "resolve_connection", "resolve_connection_plan", "resolve_credential", "resolve_profile", "rollback_transaction", "run", "run_interactive", "run_meta_command", "save_favorites", "save_history", "watch_query"]
