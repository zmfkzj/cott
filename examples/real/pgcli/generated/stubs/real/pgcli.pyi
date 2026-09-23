from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli_types import BackslashCommand as BackslashCommand, BackslashCommand_Describe as BackslashCommand_Describe, BackslashCommand_Help as BackslashCommand_Help, BackslashCommand_Quit as BackslashCommand_Quit, BackslashCommand_Tables as BackslashCommand_Tables, BackslashCommand_Unknown as BackslashCommand_Unknown, Catalog as Catalog, CatalogRefreshRequest as CatalogRefreshRequest, ClientError as ClientError, ClientError_CatalogFailed as ClientError_CatalogFailed, ClientError_EditorFailed as ClientError_EditorFailed, ClientError_ExportFailed as ClientError_ExportFailed, ClientError_FavoriteFailed as ClientError_FavoriteFailed, ClientError_HistoryFailed as ClientError_HistoryFailed, ClientError_ImportFailed as ClientError_ImportFailed, ClientError_InvalidCommand as ClientError_InvalidCommand, ClientError_InvalidSql as ClientError_InvalidSql, ClientError_NotificationFailed as ClientError_NotificationFailed, ClientError_PagerFailed as ClientError_PagerFailed, ClientError_QueryFailed as ClientError_QueryFailed, ClientError_TerminalFailed as ClientError_TerminalFailed, ClientError_TransactionFailed as ClientError_TransactionFailed, ClientError_UnsupportedFormat as ClientError_UnsupportedFormat, ColumnCatalog as ColumnCatalog, CommandInvocation as CommandInvocation, CommandResult as CommandResult, CompletionPolicy as CompletionPolicy, CompletionRequest as CompletionRequest, CompletionResult as CompletionResult, ConnectionError as ConnectionError, ConnectionError_ConnectionFailed as ConnectionError_ConnectionFailed, ConnectionError_CredentialUnavailable as ConnectionError_CredentialUnavailable, ConnectionError_InvalidDsn as ConnectionError_InvalidDsn, ConnectionError_InvalidPort as ConnectionError_InvalidPort, ConnectionError_MissingDatabase as ConnectionError_MissingDatabase, ConnectionError_ProfileMissing as ConnectionError_ProfileMissing, ConnectionError_PromptDisabled as ConnectionError_PromptDisabled, ConnectionError_SshInvalid as ConnectionError_SshInvalid, ConnectionError_TlsInvalid as ConnectionError_TlsInvalid, ConnectionInputs as ConnectionInputs, ConnectionPlan as ConnectionPlan, ConnectionProfile as ConnectionProfile, ConnectionRequest as ConnectionRequest, ConnectionSettings as ConnectionSettings, CredentialRequest as CredentialRequest, CredentialResolution as CredentialResolution, DatabaseError as DatabaseError, DatabaseError_ConnectionFailed as DatabaseError_ConnectionFailed, DatabaseError_QueryFailed as DatabaseError_QueryFailed, EditorRequest as EditorRequest, EnvironmentInputs as EnvironmentInputs, ExecutedQuery as ExecutedQuery, ExportRequest as ExportRequest, Favorite as Favorite, FavoriteStore as FavoriteStore, FormatRequest as FormatRequest, FormattedQuery as FormattedQuery, HighlightRequest as HighlightRequest, HighlightedSql as HighlightedSql, HistoryEntry as HistoryEntry, HistoryPolicy as HistoryPolicy, ImportRequest as ImportRequest, InputBuffer as InputBuffer, InteractiveRequest as InteractiveRequest, MetaCommand as MetaCommand, MetaCommand_ClearOutput as MetaCommand_ClearOutput, MetaCommand_Connect as MetaCommand_Connect, MetaCommand_ConnectionInfo as MetaCommand_ConnectionInfo, MetaCommand_Copy as MetaCommand_Copy, MetaCommand_DeleteFavorite as MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery as MetaCommand_DeleteNamedQuery, MetaCommand_Describe as MetaCommand_Describe, MetaCommand_Echo as MetaCommand_Echo, MetaCommand_EditBuffer as MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer as MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded as MetaCommand_ExecuteExpanded, MetaCommand_Expanded as MetaCommand_Expanded, MetaCommand_Favorite as MetaCommand_Favorite, MetaCommand_Help as MetaCommand_Help, MetaCommand_History as MetaCommand_History, MetaCommand_ListDataTypes as MetaCommand_ListDataTypes, MetaCommand_ListDatabases as MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges as MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains as MetaCommand_ListDomains, MetaCommand_ListExtensions as MetaCommand_ListExtensions, MetaCommand_ListFavorites as MetaCommand_ListFavorites, MetaCommand_ListForeignTables as MetaCommand_ListForeignTables, MetaCommand_ListFunctions as MetaCommand_ListFunctions, MetaCommand_ListIndexes as MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews as MetaCommand_ListMaterializedViews, MetaCommand_ListNotifications as MetaCommand_ListNotifications, MetaCommand_ListPrivileges as MetaCommand_ListPrivileges, MetaCommand_ListRoles as MetaCommand_ListRoles, MetaCommand_ListSchemas as MetaCommand_ListSchemas, MetaCommand_ListSequences as MetaCommand_ListSequences, MetaCommand_ListTables as MetaCommand_ListTables, MetaCommand_ListTablespaces as MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations as MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews as MetaCommand_ListViews, MetaCommand_NamedQuery as MetaCommand_NamedQuery, MetaCommand_Password as MetaCommand_Password, MetaCommand_PrintBuffer as MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery as MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho as MetaCommand_QueryOutputEcho, MetaCommand_Quit as MetaCommand_Quit, MetaCommand_ReadFile as MetaCommand_ReadFile, MetaCommand_ReadRelativeFile as MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog as MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer as MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery as MetaCommand_SaveNamedQuery, MetaCommand_SetFormat as MetaCommand_SetFormat, MetaCommand_SetLogFile as MetaCommand_SetLogFile, MetaCommand_SetOptions as MetaCommand_SetOptions, MetaCommand_SetOutput as MetaCommand_SetOutput, MetaCommand_SetPager as MetaCommand_SetPager, MetaCommand_Shell as MetaCommand_Shell, MetaCommand_ShowFunction as MetaCommand_ShowFunction, MetaCommand_SqlHelp as MetaCommand_SqlHelp, MetaCommand_Timing as MetaCommand_Timing, MetaCommand_Unknown as MetaCommand_Unknown, MetaCommand_VerboseErrors as MetaCommand_VerboseErrors, MetaCommand_Watch as MetaCommand_Watch, MetaCommand_WriteBuffer as MetaCommand_WriteBuffer, Notification as Notification, NotificationRequest as NotificationRequest, PagerRequest as PagerRequest, PasswordSource as PasswordSource, PasswordSource_Environment as PasswordSource_Environment, PasswordSource_Keyring as PasswordSource_Keyring, PasswordSource_None as PasswordSource_None, PasswordSource_Prompt as PasswordSource_Prompt, PasswordSource_Supplied as PasswordSource_Supplied, PromptAction as PromptAction, PromptAction_PromptPassword as PromptAction_PromptPassword, PromptAction_UsePassword as PromptAction_UsePassword, QueryPlan as QueryPlan, QueryRequest as QueryRequest, QueryResult as QueryResult, RelationCatalog as RelationCatalog, RenderLayout as RenderLayout, RenderLayout_Horizontal as RenderLayout_Horizontal, RenderLayout_Vertical as RenderLayout_Vertical, RenderRequest as RenderRequest, RenderedQuery as RenderedQuery, RoutineCatalog as RoutineCatalog, SessionOptions as SessionOptions, SshSettings as SshSettings, TableCatalog as TableCatalog, TableFormat as TableFormat, TableFormat_Aligned as TableFormat_Aligned, TableFormat_Csv as TableFormat_Csv, TableFormat_Html as TableFormat_Html, TableFormat_Json as TableFormat_Json, TableFormat_JsonLines as TableFormat_JsonLines, TableFormat_Latex as TableFormat_Latex, TableFormat_Markdown as TableFormat_Markdown, TableFormat_Tsv as TableFormat_Tsv, TableFormat_Vertical as TableFormat_Vertical, TlsSettings as TlsSettings, TransactionMode as TransactionMode, TransactionMode_AutoCommit as TransactionMode_AutoCommit, TransactionMode_Manual as TransactionMode_Manual, TransactionMode_ReadOnly as TransactionMode_ReadOnly, TransactionState as TransactionState, TransferResult as TransferResult, WatchRequest as WatchRequest, WatchResult as WatchResult
def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]: ...

def resolve_profile(name: str, profiles: CottList[ConnectionProfile]) -> Result[ConnectionProfile, ConnectionError]: ...

def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]: ...

def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]: ...

def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]: ...

"""Resolve a password with short-circuit priority: nonempty supplied_password
returns Supplied; otherwise nonempty environment_password returns Environment.
Those fields are already resolved input, so do not read process environment.
Otherwise, if use_keyring is true, require nonempty service and user and call
the lock-selected keyring.get_password(service, user). A nonempty result
returns Keyring. A None or empty result means no stored credential and proceeds
to the prompt policy. A backend/lookup failure returns CredentialUnavailable
with a fixed nonsecret message; never write/delete a keyring entry.
If still unresolved and no_prompt is true, return PromptDisabled without
reading stdin or opening the terminal. Otherwise prompt exactly once using
getpass.getpass with a fixed "Password: " prompt. Do not permit its echoed-input
fallback: treat getpass.GetPassWarning as an error. A nonempty response returns
Prompt; an explicitly submitted empty response returns password="" with
PasswordSource.None (passwordless authentication). EOF, cancellation, terminal
or hidden-input failure returns CredentialUnavailable without echoing secrets.
Never log or include any password, service credential or raw exception in errors."""
def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]: ...

"""Probe an authenticated PostgreSQL session using the lock-selected psycopg
driver, execute SELECT 1, and close it before returning Unit. This function
does not install a global session or retain a transaction or SSH daemon.
A real successful query, not an open TCP socket, establishes success.

Parse plan.dsn with psycopg.conninfo.conninfo_to_dict (empty means no DSN).
Nonempty settings.host, port, user, password and database override the DSN's
corresponding host, port, user, password and dbname; empty settings leave
the DSN value in place. Require a nonempty resolved dbname. Validate a supplied
port as decimal 1..65535; the default port is 5432. Pass connection parameters
as psycopg keyword arguments, never SQL or shell text.
plan.tls.mode overrides sslmode: empty means prefer; otherwise accept exactly
disable, allow, prefer, require, verify-ca, verify-full. The Path value "."
means an omitted certificate path. Other root_certificate, certificate and
private_key paths override sslrootcert, sslcert and sslkey respectively.
The certificate and private key are supplied together or both omitted.
Invalid DSN/port/TLS data maps to ConnectionFailed, the only declared error.
Set connect_timeout=10 regardless of DSN and issue no application writes.

Without SSH connect directly. With Some(ssh), use the installed OpenSSH ssh
executable with an argument vector, never a shell. Validate nonempty jump
host/user, positive port, and a single remote database host (no comma-separated
host list, Unix socket or control characters). Preserve the resolved database
hostname for TLS verification, but connect to the loopback tunnel using
hostaddr=127.0.0.1 and the allocated local port. Missing remote host defaults
to localhost from the jump host's perspective.
Launch a foreground control master with -M -N, a private mode-0700 temporary
directory and control socket, BatchMode=yes, StrictHostKeyChecking=yes,
ExitOnForwardFailure=yes, ConnectTimeout=10, ControlPersist=no and
GatewayPorts=no. Existing known_hosts is authority: never accept an unknown
key automatically. Use -p and -l for jump port/user; private_key "." means
no explicit identity file, otherwise use -i. Reject jump host beginning "-".
Wait at most ten monotonic seconds for ssh -S socket -O check to succeed.
Allocate a loopback-only port through a short-lived bound socket, then ask
the authenticated master with -O forward -L 127.0.0.1:port:dbhost:dbport.
Quote IPv6 hosts with forwarding-syntax brackets. A bind race is a declared
failure, never permission to connect through an unconfirmed forwarding.
Confirm the control request succeeded before contacting PostgreSQL.
All ssh commands are bounded; stdin is DEVNULL, no password prompt or shell,
no password in argv, and subprocess output is not copied into diagnostics.

On every path close the psycopg connection, request control-master exit,
terminate then kill and wait for a still-running owned foreground process,
and remove the temporary control directory. Never kill an unrelated PID.
All validation, driver, authentication, TLS, SSH, query, timeout or cleanup
failures return ConnectionFailed with a fixed nonsecret category message;
never include a DSN, password, private-key contents or raw exception text."""
def connect(plan: ConnectionPlan) -> Result[Unit, ConnectionError]: ...

def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]: ...

def complete_sql(request: CompletionRequest) -> CompletionResult: ...

def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult: ...

def highlight_sql(request: HighlightRequest) -> HighlightedSql: ...

def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]: ...

def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer: ...

def recognize_backslash(source: str) -> BackslashCommand: ...

def parse_meta_command(source: str) -> MetaCommand: ...

def render_query(request: RenderRequest) -> RenderedQuery: ...

def format_query(request: FormatRequest) -> FormattedQuery: ...

def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]: ...

def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]: ...

def begin_transaction(mode: TransactionMode) -> TransactionState: ...

def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]: ...

def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]: ...

"""Read policy.path as the HistoryEntry JSON format and apply HistoryPolicy
normalization only after validating every row, including rows later trimmed.
A missing file is an empty success. Invalid UTF-8/JSON/field types, a non-array
root, a non-regular or symlink leaf, and other I/O failures return
HistoryFailed(path=policy.path, message=a fixed nonsecret category).
Reject files larger than 16 MiB using a bounded read; do not execute file content."""
def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]: ...

"""Apply HistoryPolicy normalization, then write the HistoryEntry JSON format
with ensure_ascii=False, compact separators and one final newline. Preserve
field values exactly and reject serialized data larger than 16 MiB.
Replace policy.path atomically using an exclusive same-directory temporary
file, mode 0600, flush/fsync then os.replace, followed by parent directory fsync.
Parent directories are not created. Reject a symlink/non-regular existing leaf.
On precommit failure preserve the original and remove the temporary file.
Return HistoryFailed(path=policy.path, message=a fixed nonsecret category) for
serialization or I/O failure; never leave a partially truncated history file."""
def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]: ...

"""Append entry to entries, then apply the exact HistoryPolicy normalization.
This is pure list transformation with no clock or filesystem access."""
def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]: ...

"""Read store.path as the Favorite JSON format; a missing file is an empty success.
Preserve all valid entries in file order; more than store.max_entries is an
error, not truncation. Validate every row, including tags and duplicate names.
Reject invalid UTF-8/JSON, files over 16 MiB, non-regular/symlink leaves and
genuine I/O failures. Return FavoriteFailed(name=str(store.path)) for all file,
shape, duplicate-name or capacity failures. Do not silently skip invalid rows."""
def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]: ...

"""Validate Favorite names and capacity exactly as the persistence format requires,
retaining input order. Write UTF-8 JSON with ensure_ascii=False, compact
separators and one newline; reject serialized data over 16 MiB.
Use an exclusive same-directory temporary file, mode 0600, flush/fsync,
os.replace and parent fsync. Do not create parents or follow symlink leaves;
preserve the old file and remove the temporary file on precommit failure.
Every validation/serialization/I/O failure is FavoriteFailed(name=str(store.path))."""
def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]: ...

def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]: ...

def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]: ...

def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]: ...

def page_output(request: PagerRequest) -> Result[Unit, ClientError]: ...

def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]: ...

def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]: ...

def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]: ...

def run_interactive(request: InteractiveRequest) -> Result[Unit, ClientError]: ...

"""Run a real psycopg line-oriented PostgreSQL REPL. arguments excludes argv[0].
Use argparse with program name pgcli-cott, optional positional DSN, -h/--host,
-p/--port, -U/--username, -d/--dbname, -c/--command and --help. Reserve -h for
host, not help. Unknown or malformed arguments print usage to stderr and exit 2;
--help prints usage and exits 0 without connecting. Nonempty supplied flags
override the DSN; unspecified connection fields retain libpq defaults and
PGHOST/PGPORT/PGUSER/PGDATABASE/PGPASSWORD environment behavior. Never accept a
password argument, echo credentials or disable the DSN's TLS verification.
Connect once using psycopg.connect with autocommit=True and connect_timeout=10.
With -c, execute that complete SQL string once. Otherwise read one complete
SQL command per stdin line (no multiline parser); skip empty lines and leave
on a line equal to \\q or quit after stripping. EOF is normal termination.
Print "pgcli> " only when stdin is a terminal. Execute SQL through a real
cursor; for row results print tab-separated column names followed by rows in
driver order, rendering SQL NULL as NULL and other cells with str. For
commands without rows print cursor.statusmessage when nonempty.
On a query error print only a fixed "query failed" message to stderr; in -c
mode exit 1, otherwise continue accepting lines but remember failure. Normal
EOF/quit exits 0 if every query succeeded, otherwise 1. Connection or I/O
failure exits 1 with a fixed category message. KeyboardInterrupt exits 130.
Close every cursor and the connection before sys.exit; never log raw exception
text or leave a background connection. This entrypoint does not create a hidden
global session or infer a richer argument grammar from the upstream project."""
def run(arguments: CottList[str]) -> Never: ...

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "Catalog", "CatalogRefreshRequest", "ClientError", "ClientError_CatalogFailed", "ClientError_EditorFailed", "ClientError_ExportFailed", "ClientError_FavoriteFailed", "ClientError_HistoryFailed", "ClientError_ImportFailed", "ClientError_InvalidCommand", "ClientError_InvalidSql", "ClientError_NotificationFailed", "ClientError_PagerFailed", "ClientError_QueryFailed", "ClientError_TerminalFailed", "ClientError_TransactionFailed", "ClientError_UnsupportedFormat", "ColumnCatalog", "CommandInvocation", "CommandResult", "CompletionPolicy", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_ConnectionFailed", "ConnectionError_CredentialUnavailable", "ConnectionError_InvalidDsn", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_ProfileMissing", "ConnectionError_PromptDisabled", "ConnectionError_SshInvalid", "ConnectionError_TlsInvalid", "ConnectionInputs", "ConnectionPlan", "ConnectionProfile", "ConnectionRequest", "ConnectionSettings", "CredentialRequest", "CredentialResolution", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EditorRequest", "EnvironmentInputs", "ExecutedQuery", "ExportRequest", "Favorite", "FavoriteStore", "FormatRequest", "FormattedQuery", "HighlightRequest", "HighlightedSql", "HistoryEntry", "HistoryPolicy", "ImportRequest", "InputBuffer", "InteractiveRequest", "MetaCommand", "MetaCommand_ClearOutput", "MetaCommand_Connect", "MetaCommand_ConnectionInfo", "MetaCommand_Copy", "MetaCommand_DeleteFavorite", "MetaCommand_DeleteNamedQuery", "MetaCommand_Describe", "MetaCommand_Echo", "MetaCommand_EditBuffer", "MetaCommand_ExecuteBuffer", "MetaCommand_ExecuteExpanded", "MetaCommand_Expanded", "MetaCommand_Favorite", "MetaCommand_Help", "MetaCommand_History", "MetaCommand_ListDataTypes", "MetaCommand_ListDatabases", "MetaCommand_ListDefaultPrivileges", "MetaCommand_ListDomains", "MetaCommand_ListExtensions", "MetaCommand_ListFavorites", "MetaCommand_ListForeignTables", "MetaCommand_ListFunctions", "MetaCommand_ListIndexes", "MetaCommand_ListMaterializedViews", "MetaCommand_ListNotifications", "MetaCommand_ListPrivileges", "MetaCommand_ListRoles", "MetaCommand_ListSchemas", "MetaCommand_ListSequences", "MetaCommand_ListTables", "MetaCommand_ListTablespaces", "MetaCommand_ListTextSearchConfigurations", "MetaCommand_ListViews", "MetaCommand_NamedQuery", "MetaCommand_Password", "MetaCommand_PrintBuffer", "MetaCommand_PrintNamedQuery", "MetaCommand_QueryOutputEcho", "MetaCommand_Quit", "MetaCommand_ReadFile", "MetaCommand_ReadRelativeFile", "MetaCommand_RefreshCatalog", "MetaCommand_ResetBuffer", "MetaCommand_SaveNamedQuery", "MetaCommand_SetFormat", "MetaCommand_SetLogFile", "MetaCommand_SetOptions", "MetaCommand_SetOutput", "MetaCommand_SetPager", "MetaCommand_Shell", "MetaCommand_ShowFunction", "MetaCommand_SqlHelp", "MetaCommand_Timing", "MetaCommand_Unknown", "MetaCommand_VerboseErrors", "MetaCommand_Watch", "MetaCommand_WriteBuffer", "Notification", "NotificationRequest", "PagerRequest", "PasswordSource", "PasswordSource_Environment", "PasswordSource_Keyring", "PasswordSource_None", "PasswordSource_Prompt", "PasswordSource_Supplied", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryPlan", "QueryRequest", "QueryResult", "RelationCatalog", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "RoutineCatalog", "SessionOptions", "SshSettings", "TableCatalog", "TableFormat", "TableFormat_Aligned", "TableFormat_Csv", "TableFormat_Html", "TableFormat_Json", "TableFormat_JsonLines", "TableFormat_Latex", "TableFormat_Markdown", "TableFormat_Tsv", "TableFormat_Vertical", "TlsSettings", "TransactionMode", "TransactionMode_AutoCommit", "TransactionMode_Manual", "TransactionMode_ReadOnly", "TransactionState", "TransferResult", "WatchRequest", "WatchResult", "begin_transaction", "commit_transaction", "complete_catalog_sql", "complete_sql", "connect", "edit_in_editor", "edit_multiline", "execute_planned_query", "execute_query", "export_query", "format_query", "highlight_sql", "import_delimited", "load_favorites", "load_history", "page_output", "parse_dsn", "parse_meta_command", "plan_query", "prompt_policy", "receive_notifications", "recognize_backslash", "refresh_catalog", "remember_history", "render_query", "resolve_connection", "resolve_connection_plan", "resolve_credential", "resolve_profile", "rollback_transaction", "run", "run_interactive", "run_meta_command", "save_favorites", "save_history", "watch_query"]
