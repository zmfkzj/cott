from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.hsql_types import CatalogPath as CatalogPath, HSQL_PROTOCOL_VERSION as HSQL_PROTOCOL_VERSION, HsqlArguments as HsqlArguments, HsqlContext as HsqlContext, HsqlError as HsqlError, HsqlError_Connection as HsqlError_Connection, HsqlError_Crash as HsqlError_Crash, HsqlError_Interrupted as HsqlError_Interrupted, HsqlError_Query as HsqlError_Query, HsqlError_Timeout as HsqlError_Timeout, HsqlError_Usage as HsqlError_Usage, HsqlMode as HsqlMode, HsqlMode_Catalog as HsqlMode_Catalog, HsqlMode_CatalogSearch as HsqlMode_CatalogSearch, HsqlMode_ConfigMode as HsqlMode_ConfigMode, HsqlMode_Execute as HsqlMode_Execute, HsqlMode_History as HsqlMode_History, HsqlMode_HistorySearch as HsqlMode_HistorySearch, HsqlMode_Info as HsqlMode_Info, HsqlMode_Serve as HsqlMode_Serve, HsqlMode_SessionReset as HsqlMode_SessionReset, HsqlMode_SessionStatus as HsqlMode_SessionStatus, HsqlMode_Skill as HsqlMode_Skill, HsqlMode_Spec as HsqlMode_Spec, HsqlResponse as HsqlResponse, LayoutOptions as LayoutOptions, SqlSource as SqlSource, SqlSource_Command as SqlSource_Command, SqlSource_SqlFile as SqlSource_SqlFile
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, Connection, ConnectionRequest
from real.harlequin.config_types import ConfigEntry
from real.harlequin.results_types import ColumnInfo, ResultSet
"""The exit status of failure: Usage 2, Query 1, Connection 3, Timeout 4,
Interrupted 130, Crash 70."""
def hsql_exit_status(failure: HsqlError) -> I64: ...

"""The stderr text for failure: "hsql: error: {message}\\n" (Interrupted is
"hsql: error: interrupted\\n"); Crash is "hsql: error: hsql hit a bug in
itself and could not finish the run.\\nnote: {message}\\n"."""
def hsql_error_line(failure: HsqlError) -> str: ...

"""Parse `hsql [OPTIONS] [CONN_STR]...` (arguments without the program name)
with the click grammar of real.harlequin.cli.parse_harlequin_arguments
(interleaved positionals, "--", --name=VALUE, -xVALUE, clustered short
flags such as -tA or -tAc SQL). Options: -a/--adapter NAME (one of
adapter_names, case-insensitive; default duckdb); -c/--command TEXT and
-f/--file PATH (repeatable, kept in argv order as sources); -o/--output
PATH; --format NAME (table, markdown, md, vertical, csv, tsv, json, jsonl,
ndjson, parquet, orc, feather, arrow, none; case-insensitive); --csv,
--json, --jsonl, --markdown, -x/--vertical shorthands; -t/--tuples-only;
-A/--no-align; --no-header; --no-footer; --null-string TEXT; -P/--profile
NAME; --config-path PATH; -r/--read-only; --timeout SECONDS (> 0);
--ssh-host, --ssh-forward (repeatable), --ssh-batch-mode,
--ssh-allow-reuse, --ssh-timeout SECONDS (> 0); --catalog;
--catalog-search TERM; --path TEXT; --history; --history-search TERM;
--config MODE (show, list-profiles, validate, schema, init); --spec;
--info; --skill; --limit N (integer >= -1, default 500); --display-rows N
(>= -1); --result all|last|N; --on-error stop|continue; --no-write-history;
--stats; --color auto|always|never (default never); --serve NAME;
--session NAME; --session-reset; --session-status; --queue-timeout
SECONDS (> 0); --idle-timeout SECONDS (>= 0, default 1800);
--max-lifetime SECONDS (>= 0, default 28800); --help; --version; plus
each adapter option (spellings that collide with an hsql spelling are
withheld). Errors are Usage with click's messages ("No such option: X",
"Option 'X' requires an argument.", "Invalid value for ...") and these:
two modes: "{first} and {second} can't be used together."; a mode with
-c/-f: "{mode} doesn't run SQL, so it can't be combined with -c/--command
or -f/--file."; a format shorthand with another format selector:
"{a} and {b} both choose an output format; pass only one."; --path
without --catalog or --catalog-search: "--path only applies to --catalog
and --catalog-search."; blank --catalog-search term: "--catalog-search
needs a term to search for."; blank --history-search term:
"--history-search needs a term to search for."; a per-request option with
--serve: "{option} is a per-request option; pass it with each --session
request, not to --serve."; a server-lifetime option without --serve:
"{option} only applies to --serve."; an invalid --result: "--result must
be all, last, or a result number."."""
def parse_hsql_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[HsqlArguments, HsqlError]: ...

"""The hsql help text in click's layout: "Usage: hsql [OPTIONS] [CONN_STR]...",
a blank line, the description "  Run SQL against a database and exit.
hsql is Harlequin's headless CLI." with a line listing the installed
adapter names ("  Installed adapters: duckdb, sqlite, ..."), then
"Options:" with every hsql option of parse_hsql_arguments (spellings,
metavar, help sentence with its default), and, when selected is Some, a
section "{display_name} Adapter Options:" with options."""
def hsql_help(descriptors: CottList[AdapterDescriptor], selected: Option[AdapterDescriptor], options: CottList[AdapterOption]) -> str: ...

"""Render result_set in a text layout (upstream harlequin.layout): layout
is "table", "markdown" (also "md") or "vertical". Cells are the Python
str() of each value (bytes as their Python repr; floats by repr), SQL NULL
as options.null_string or "NULL", CRLF normalized to LF. Rows are capped
at options.max_rows before widths are measured. Widths count terminal
cells (wcwidth for non-ASCII). Table aligned: header " a | b" (a leading
space, " | " separators, each cell padded), rule of "-" with "-+-" at
separators, then rows the same way; the last column is not padded;
multi-line cells continue on the next physical line with "+" at the
separator. Table unaligned: header and rows joined by "|", no rule.
Markdown: "| a | b |", "| --- | --- |" (minimum width 3), cells with "|"
escaped as "\\\\|" and newlines as "<br>", footer as "*(N rows)*" after a
blank line. Vertical aligned: each record starts "-[ RECORD N ]" followed
by dashes to the widest line, then "name | value" lines with names padded;
unaligned "name|value". Footer (when options.footer): "(1 row)" or
"(N rows)"; "(SHOWN of TOTAL rows)" when capped; "(SHOWN of >FETCHED
rows)" when result_set.truncated. header false drops the header and rule
(vertical: record rules become blank lines). With options.color the
header cells are wrapped in "\\u001b[1m...\\u001b[0m" and NULL cells in
"\\u001b[2m...\\u001b[0m". Every line ends with "\\n"."""
def layout_text(result_set: ResultSet, layout: str, options: LayoutOptions) -> str: ...

"""The file suffix of an output format: table and vertical ".txt", markdown
and md ".md", csv ".csv", tsv ".tsv", json ".json", jsonl ".jsonl", ndjson
".ndjson", parquet ".parquet", orc ".orc", feather ".feather", arrow
".arrow", none "" (and "" for anything else)."""
def format_suffix(format: str) -> str: ...

"""Parse an hsql --path (upstream navigate.parse): a blank path is the root
(no segments). Segments are separated by "."; a segment wholly in double
quotes is literal (a doubled "" is one quote, dots and wildcards are
literal); a bare final segment containing * or ? is the pattern. Errors are
Usage: an empty segment "'{path}' has an empty segment. Separate labels
with one dot, and quote a label that contains a dot, like \\"my.table\\".";
an unquoted wildcard before the last segment "'{segment}' contains a
wildcard in the middle of a path, which is not supported. A wildcard is
only allowed in the last path segment."; an unterminated quote "The quoted
segment starting at {rest} never closes. Write a literal quote as \\"\\".";
a partially quoted segment "'{segment}' mixes quoted and bare text. Quote
the whole segment or none of it."."""
def parse_catalog_path(path: str) -> Result[CatalogPath, HsqlError]: ...

"""A label as a --path segment: wrapped in double quotes (inner quotes
doubled) when it is empty, has leading or trailing whitespace, or contains
".", "*", "?" or a double quote; otherwise unchanged."""
def spell_catalog_label(label: str) -> str: ...

"""The error for a --path segment that names nothing: "There is no '{segment}'
under {parent}." (parent spelled "'{parent}'", or "the top level of the
catalog" when Nothing), then " Did you mean: {a}, {b}?" with up to three
real.harlequin.sqltext.close_matches(segment, siblings, 3) (each spelled with
spell_catalog_label) when any; else " It contains: {first five}" plus
", and N more" when there are more; else " That level is empty."."""
def missing_label_message(segment: str, parent: Option[str], siblings: CottList[str]) -> str: ...

"""The --stats line: compact JSON (separators "," and ":") with keys in this
order: "status", "statements", "rows", "truncated", "limit" (null when
Nothing), "elapsed_ms", "columns" (a list of {"name":...,"type":...} with
type the column's type_label), and "error" only when failure_text is Some;
followed by "\\n"."""
def stats_json(status: str, statements: U64, rows: U64, truncated: bool, limit: Option[U64], elapsed_ms: U64, columns: CottList[ColumnInfo], failure_text: Option[str]) -> str: ...

"""Whether name is a session name: 1 to 64 characters, each an ASCII letter,
digit, "_" or "-"."""
def valid_session_name(name: str) -> bool: ...

"""The socket of session name: "{XDG_RUNTIME_DIR}/hsql/{name}.sock" when
XDG_RUNTIME_DIR is set and nonempty in environment, else
"{TMPDIR or /tmp}/hsql-{uid}/{name}.sock"."""
def session_socket_path(name: str, environment: FrozenMap[str, str], uid: I64) -> Path: ...

"""Serve one connected hsql request (the Execute, Catalog and CatalogSearch
modes) on connection, as a cold run and a warm session both do.
Execute: read the sources in order (files relative to cwd; "-" is
stdin_text; an OSError is Usage "could not read {path}: {reason}"), split
each with real.harlequin.sqltext.split_statements, run them with
real.harlequin.adapters.execute_statements(connection, statements, limit
(Nothing for -1), continue_on_error), then fetch every cursor with
real.harlequin.adapters.fetch_result((connection, executed, limit, Nothing). When
arguments.write_history each statement is logged with
real.harlequin.history.record_query/real.harlequin.history.update_query  (program "hsql", the
redacted sql). Select results per arguments.result; more than one result
for a single-result format (csv, tsv, json, parquet, orc, feather, arrow)
to a file or stdout is Usage "{n} result sets, but {format} holds one;
use --result last, --result N, or -o DIR for one file each". Write each
selected result: layouts with layout_text (LayoutOptions from -t, -A,
--no-header, --no-footer, --null-string, color decided by --color and
context tty/NO_COLOR, max_rows from --display-rows or 40 for table and
markdown, 10 for vertical, -1 for all) joined into stdout, separated by a
blank line; file formats with real.harlequin.export.write_result into a
temporary file whose bytes become stdout (csv null defaults to ""); -o
FILE writes stdout there instead; -o DIR writes "result-{n}{suffix}" files
and names each on stderr as "note: wrote {path}"; format none writes
nothing. Warnings on stderr: "note: results truncated at --limit {n};
pass --limit -1 for all rows" when a result was truncated; "note: printed
{shown} of {total} rows; pass --display-rows -1 for all of them" when the
footer is hidden and rows were capped; "note: --display-rows only applies
to text layouts; use --limit to fetch fewer rows." for a non-layout
format. A statement failure writes hsql_error_line(Query("{title}\\n
{message}")) and status 1 (after the earlier results). --timeout starts a
timer that calls real.harlequin.adapters.cancel_queries  (Timeout "timed out after {n}s", status
4). --stats appends stats_json to stderr.
Catalog: parse_catalog_path(arguments.catalog_path or ""), walk labels
from real.harlequin.adapters.load_catalog  with real.harlequin.adapters.load_catalog_children  (a missing label is Usage
missing_label_message), and list the level's children (filtered by the
pattern with fnmatch.fnmatchcase) as a result set with columns path, name,
query_name, type, type_label (path spelled with spell_catalog_label and
joined by "."). CatalogSearch: real.harlequin.adapters.search_catalog  under that scope.
Every stderr text is passed through real.harlequin.sqltext.redact_text
with context.secrets."""
def execute_hsql_request(connection: Connection, arguments: HsqlArguments, cwd: Path, stdin_text: Option[str], context: HsqlContext) -> HsqlResponse: ...

"""`hsql --serve NAME`: validate name with valid_session_name (Usage
"invalid session name '{name}': use 1 to 64 letters, digits, _ or -"),
create the runtime directory of session_socket_path (mode 0700; it must be
a real directory owned by this uid with no group/other bits, else Usage),
take an exclusive filelock.FileLock(timeout=0) on "{name}.lock" beside the
socket, released when the session ends (filelock.Timeout: Usage
"session '{name}' is already running"), remove a stale socket, connect
with real.harlequin.adapters.connect(request) (failure: "hsql: error:
{title}\\n{message}" and return 3), bind an AF_UNIX stream socket, and print
"note: session '{name}' is ready ({adapter}). Send it queries with `hsql
--session {name} -c ...`, or set HSQL_SESSION={name}. Ctrl-C stops it."
to stderr. Frames are "!BI" (kind byte, payload length) with payload at
most 64 MiB; kinds HELLO=1 REQUEST=2 STDOUT=3 STDERR=4 EXIT=5 STATUS=6
CANCEL=7. Each accepted peer (SO_PEERCRED uid must equal ours, else
"note: refused a connection from uid {uid}, which is not yours.") first
receives HELLO with HSQL_PROTOCOL_VERSION; a REQUEST payload is a JSON
object {"argv": [...], "cwd": str, "env": {"NO_COLOR"?,
"HARLEQUIN_CONFIG_PATH"?}, "stdin": str|null, "stdout_tty": bool,
"stderr_tty": bool, "id": hex}; requests run one at a time in arrival
order (arguments.queue_timeout_seconds bounds the wait: Timeout "waited
{n}s for the session's previous request and never reached the database
(--queue-timeout).") through parse_hsql_arguments and
execute_hsql_request, replying STDOUT chunks of at most 64 KiB, STDERR,
then EXIT with the 4-byte status; --session-reset closes and reconnects;
STATUS replies a JSON object with keys session, pid, version, adapter,
connection, connection_options, uptime_s, requests, state (idle, busy or
unavailable), queued, transaction_mode, ssh, idle_timeout_s,
expires_in_s without waiting behind a running query; CANCEL with a
request id cancels it with real.harlequin.adapters.cancel_queries.. Each request logs "note:
request {n}: exit {code} in {ms}ms". The server stops after
idle_timeout_seconds without requests or max_lifetime_seconds of age (0
disables either), or on Ctrl-C, printing "note: session '{name}' stopped
after {n} request(s).", closing the connection, removing the socket and
returning 0."""
def serve_hsql_session(name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, environment: FrozenMap[str, str]) -> I64: ...

"""The warm-session client of the serve_hsql_session wire protocol: connect an
AF_UNIX stream socket to session_socket_path(name, environment,
os.getuid()). Every frame is struct.pack("!BI", kind, len(payload)) followed
by payload; kinds are HELLO=1 REQUEST=2 STDOUT=3 STDERR=4 EXIT=5 STATUS=6
CANCEL=7. The server first sends HELLO whose payload is its version as
UTF-8; one that differs from HSQL_PROTOCOL_VERSION is
Err(Connection("session '{name}' runs hsql {v}; restart it with this
version")). When arguments contain --session-status, send one STATUS frame
with an empty payload and return Ok(HsqlResponse(stdout = the STATUS reply
payload + b"\\n", stderr "", status 0)). Otherwise send one REQUEST whose
payload is the UTF-8 JSON object {"argv": arguments, "cwd": str(cwd),
"env": {only NO_COLOR and HARLEQUIN_CONFIG_PATH when present in
environment}, "stdin": stdin_text or null, "stdout_tty": stdout_tty,
"stderr_tty": stderr_tty, "id": secrets.token_hex(8)}, then read frames,
concatenating STDOUT payloads as stdout bytes and STDERR payloads decoded
as UTF-8 text, until EXIT, whose payload is struct.pack("!i", status);
return Ok(HsqlResponse(stdout, stderr, status)). On KeyboardInterrupt while
waiting, open a second connection, read its HELLO, send CANCEL whose
payload is the request id as UTF-8, close it and return
Err(Interrupted). A socket that cannot be connected
(OSError) is Err(Connection("no session named '{name}' is running. Start
one with `hsql --serve {name} ...`.")); a connection closed before EXIT is
Err(Connection("session '{name}' closed the connection"))."""
def send_session_request(name: str, arguments: CottList[str], cwd: Path, stdin_text: Option[str], environment: FrozenMap[str, str], stdout_tty: bool, stderr_tty: bool) -> Result[HsqlResponse, HsqlError]: ...

"""The hsql command (arguments without the program name); writes result
bytes to stdout and diagnostics to stderr (stdout flushed first) and exits
with the status. No arguments: print hsql_help to stderr and exit 2.
Session routing first: the last --session NAME (or --session=NAME, up to
"--"), else HSQL_SESSION unless an argument is --serve; a routed request
(reading stdin when an argument is "-f -" / "--file -") goes through
send_session_request; for HSQL_SESSION an unreachable session prints
"note: HSQL_SESSION={name} is not running; running cold." and continues
cold, for --session it exits 3.
Cold: real.harlequin.cli.first_pass finds -a/-P/--config-path; config
files come from real.harlequin.config.config_search_paths (explicit path,
else HARLEQUIN_CONFIG_PATH) read with real.harlequin.config.read_config_file  and merged with
real.harlequin.config.merge_config_files;; the profile is real.harlequin.config.select_profile  + real.harlequin.config.interpolate_profile

(-P None means no profile); the adapter is -a, else the profile's
adapter, else duckdb; parse_hsql_arguments with that adapter's options;
--help prints hsql_help to stdout (exit 0); --version prints "hsql,
version {HARLEQUIN_VERSION}" (exit 0). Profile entries are merged under
the explicit options (TUI-only keys theme, keymap_name, show_files,
show_s3, locale, viewer_max_rows, no_download_tzdata ignored). Modes that
do not connect: --history/--history-search read
real.harlequin.history.recent_queries (paths from real.harlequin.history.harlequin_paths;;
connection narrowing only when -P, -a or CONN_STR was typed; --limit rows,
one more read to detect truncation) and print them with layout_text as a
result set with columns run_at, program, profile, adapter, status, rows,
elapsed_ms, sql; --config show (merged config as TOML with secrets
replaced by "********", or JSON with --format json), list-profiles (one
name per line), validate (real.harlequin.config.validate_config_file  problems as
"{path}: {key}: {message}" lines, exit 2 when any, else "config is
valid"), schema (a JSON Schema object of the profile keys and adapter
options), init (real.harlequin.config.write_profile  of the typed options to the chosen profile;
-P required, "None" refused); --spec prints JSON {"hsql": {options...},
"adapters": {name: [option objects]}} (narrowed by an explicit -a);
--info prints JSON with "version", "python", "config_files",
"profile", and "adapters" capability objects; --skill prints the
packaged Markdown skill describing hsql usage (to -o DIR as
"SKILL.md"). --serve NAME runs serve_hsql_session. Otherwise connect with
real.harlequin.adapters.connect (the SSH tunnel through
real.harlequin.support.open_ssh_tunnel when --ssh-host; connection
failures exit 3 with "hsql: error: {title}\\n{message}"), no SQL source is
Usage "no SQL to run. Pass -c/--command or -f/--file, or see 'hsql
--help'.", then execute_hsql_request, write its stdout bytes and stderr
text, close the connection and exit with its status. Errors print
hsql_error_line and exit hsql_exit_status; Ctrl-C exits 130; an
unexpected exception exits 70."""
def run_hsql(arguments: CottList[str]) -> Never: ...

__all__ = ["CatalogPath", "HSQL_PROTOCOL_VERSION", "HsqlArguments", "HsqlContext", "HsqlError", "HsqlError_Connection", "HsqlError_Crash", "HsqlError_Interrupted", "HsqlError_Query", "HsqlError_Timeout", "HsqlError_Usage", "HsqlMode", "HsqlMode_Catalog", "HsqlMode_CatalogSearch", "HsqlMode_ConfigMode", "HsqlMode_Execute", "HsqlMode_History", "HsqlMode_HistorySearch", "HsqlMode_Info", "HsqlMode_Serve", "HsqlMode_SessionReset", "HsqlMode_SessionStatus", "HsqlMode_Skill", "HsqlMode_Spec", "HsqlResponse", "LayoutOptions", "SqlSource", "SqlSource_Command", "SqlSource_SqlFile", "execute_hsql_request", "format_suffix", "hsql_error_line", "hsql_exit_status", "hsql_help", "layout_text", "missing_label_message", "parse_catalog_path", "parse_hsql_arguments", "run_hsql", "send_session_request", "serve_hsql_session", "session_socket_path", "spell_catalog_label", "stats_json", "valid_session_name"]
