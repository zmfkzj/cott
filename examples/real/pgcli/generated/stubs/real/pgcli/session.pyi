from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.session_types import CommandOutcome as CommandOutcome, EvaluateError as EvaluateError, EvaluateError_ConnectionLost as EvaluateError_ConnectionLost, EvaluateError_Failed as EvaluateError_Failed, EvaluateError_Interrupted as EvaluateError_Interrupted, EvaluateError_NotImplemented as EvaluateError_NotImplemented, Evaluation as Evaluation, QueryOutcome as QueryOutcome, QuitDecision as QuitDecision, RefreshKind as RefreshKind, RefreshKind_All as RefreshKind_All, RefreshKind_Nothing as RefreshKind_Nothing, RefreshKind_Reset as RefreshKind_Reset, RefreshKind_SearchPath as RefreshKind_SearchPath, ScriptOutcome as ScriptOutcome, Session as Session, SessionSettings as SessionSettings, SpecialCommandEntry as SpecialCommandEntry, SpecialHandle as SpecialHandle, SpecialSetup as SpecialSetup, SpecialState as SpecialState, StatementChanges as StatementChanges, TerminalSize as TerminalSize
from real.pgcli.connection_types import Executor
from real.pgcli.output_types import OutputStyle
"""The statement splitting of PGExecute.run. Strip text; "" gives no
statement. Remove beginning comments: repeatedly match the regex
^(/\\*.*?\\*/|--.*?)(?:\\n|$) (re.DOTALL) at the start, remember the match and
continue after it with leading whitespace stripped. Split the remainder with
sqlparse.split, then put the removed comments in front. Each piece becomes
sqlparse.format(piece, strip_comments=True).strip(), then trailing ";"
characters are stripped (rstrip(";")) and the result stripped again; empty
results are dropped. Order is kept."""
def statement_texts_for_run(text: str) -> CottList[str]: ...

"""_execute_statements splitting (-c, -f and \\watch-aware runs): split text with
sqlparse.split and take pieces from the front; skip pieces that are blank
after strip(); a stripped piece that starts with "\\\\" and contains a line
feed is cut at its first line feed: the first line is the statement and the
rest is split again with sqlparse.split and put back in front of the
remaining pieces. Each returned statement is stripped."""
def script_statements(text: str) -> CottList[str]: ...

"""mutated: status's first whitespace-separated word, lower-cased, is insert,
update or delete ("" status is not mutating). meta_changed: sql's first
whitespace-separated word, lower-cased, is alter, create, drop, commit or
rollback. db_changed: sql's first word, lower-cased, is use, \\c or \\connect.
path_changed: sql lower-cased contains "set search_path". A blank sql gives
false for the sql-based flags."""
def classify_statement(sql: str, status: str) -> StatementChanges: ...

"""PGCli._should_limit_output: false in explain mode; false unless sql's first
whitespace-separated word, lower-cased, is select; false when any token of
sqlparse.parse(sql) (flattened) matches keyword LIMIT
(token.match(sqlparse.tokens.Keyword, "LIMIT")); otherwise row_limit != 0
and rowcount > row_limit."""
def should_limit_rows(sql: str, rowcount: I64, row_limit: I64, explain_mode: bool) -> bool: ...

"""The argument split of \\c / \\connect / use: all matches of the regex
"[^"]*"|[^"'\\s]+ in pattern, in order, kept exactly as matched (upstream
discards its quote stripping, so double quotes stay), padded with "" to
four items: database, user, host, port. Extra matches are kept after the
fourth."""
def change_db_arguments(pattern: str) -> CottList[str]: ...

"""PGCli's pgspecial setup: construct pgspecial.main.PGSpecial(), set
timing_enabled = setup.timing, call pset_pager("on" when enable_pager else
"off"), and set pgspecial.namedqueries.NamedQueries.instance =
NamedQueries.from_config(ConfigObj(os.path.expanduser(config_path),
interpolation=False, encoding="utf-8")) so \\n, \\ns, \\nd, \\np and \\ne read
and rewrite that file's [named queries] section.
Then register pgcli's own commands in this order with PGSpecial.register
(handler, command, syntax, description, arg_type, case_sensitive, aliases):
\\nq ("\\nq", "Toggle named query quiet mode (hide query text)", NO_QUERY,
case sensitive); \\ne ("\\ne name", "Edit a named query in the external
editor."); \\c ("\\c[onnect] database_name", "Change to a new database.",
aliases use, \\connect, USE); \\q ("\\q", "Quit pgcli.", NO_QUERY, case
sensitive, alias :q); quit ("quit", "Quit pgcli.", NO_QUERY, case
insensitive, alias exit); \\# ("\\#", "Refresh auto-completions.", NO_QUERY);
\\refresh ("\\refresh", "Refresh auto-completions.", NO_QUERY); \\i ("\\i
filename", "Execute commands from file."); \\o ("\\o [filename]", "Send all
query results to file."); \\log-file ("\\log-file [filename]", "Log all query
results to a logfile, in addition to the normal output destination.");
\\conninfo ("\\conninfo", "Get connection details"); \\T ("\\T [format]",
"Change the table format used to output results"); \\echo ("\\echo
[string]", "Echo a string to stdout"); \\qecho ("\\qecho [string]", "Echo a
string to the query output channel."); \\v ("\\v [on|off]", "Toggle verbose
errors."). Unless stated, arg_type is PARSED_QUERY and commands are case
sensitive. These registry entries exist for \\? and completion; their
handlers are lambdas (lambda *args, **kwargs: []) returning an empty list,
because real.pgcli.session.evaluate_pgcli_command intercepts every pgcli
command before calling PGSpecial.execute. A ConfigObj error is
Failed(message: str(error))."""
def create_special_handle(setup: SpecialSetup) -> Result[Opaque[Literal["pgcli.pgspecial"]], EvaluateError]: ...

"""Every key of the PGSpecial commands registry in dict order, with its
registered syntax and description (aliases included, hidden entries
included)."""
def special_command_catalog(special: Opaque[Literal["pgcli.pgspecial"]]) -> CottList[SpecialCommandEntry]: ...

"""pgspecial.namedqueries.NamedQueries.instance.list(): the names in the
[named queries] section, in file order."""
def named_query_names(special: Opaque[Literal["pgcli.pgspecial"]]) -> CottList[str]: ...

"""Read the PGSpecial flags: expanded_output, auto_expand, timing_enabled and
pager_config (0 off, 1 long output only, 2 always)."""
def special_display_state(special: Opaque[Literal["pgcli.pgspecial"]]) -> SpecialState: ...

"""PGCli._evaluate_command together with PGExecute.run and pgcli's registered
special-command handlers. start = time.time().

Statements: when text.strip() is "" there is exactly one result (no title,
no rows, no status, sql "", success false, not special). Otherwise run
each statement given by the splitting rule of
real.pgcli.session.statement_texts_for_run(text), applied by a private
helper of this implementation (a long script's statement list must not
cross the facade boundary), on session.executor's connection:
a) A statement ending with "\\G" sets the PGSpecial expanded_output to true
for this statement only (restored to false after the statement when it was
false before) and loses the "\\G" (then stripped).
b) Special commands first, in every mode (explain mode never prefixes
them): command, verbose, pattern = pgspecial.main.parse_special_command(sql).
The command resolves like PGSpecial.execute (exact key, else lower-cased key
unless that entry is case sensitive). When it resolves to one of pgcli's
own commands (registered by real.pgcli.session.create_special_handle,
including aliases) it is handled here:
  \\nq: toggle settings.hide_named_query_text; message "Named query quiet
  mode: ON" or "Named query quiet mode: OFF".
  \\ne name: name = pattern.strip(); "" gives "Usage: \\ne <name>". Else open
  pgspecial.iocommands.open_external_editor(sql=the current named query or
  "", editor=$PSQL_EDITOR or $EDITOR or $VISUAL or None); a returned message
  is shown; the stripped result "" gives "<name>: empty query, not saved.",
  an unchanged existing query "<name>: no changes.", otherwise
  NamedQueries.instance.save(name, sql) and "<name>: Created" or
  "<name>: Saved".
  \\c, \\connect, use, USE: with a pattern, args =
  real.pgcli.session.change_db_arguments(pattern) and
  real.pgcli.connection.reconnect_executor(executor, ReconnectRequest(args
  0..3)); a failure prints str(error) in red on standard error and "Previous
  connection kept" on standard output and keeps the executor; without a
  pattern reconnect with all "". Then the message 'You are now connected to
  database "<dbname>" as user "<user>"' with the current executor values.
  \\q, :q, quit, exit: stop and return quit = true (remaining statements are
  not run; the lines produced so far are kept).
  \\#, \\refresh: message "Auto-completion refresh can't be started." for a
  virtual database, else "Auto-completion refresh restarted." when
  settings.completion_refreshing, else "Auto-completion refresh started in
  the background."; refresh becomes All unless virtual.
  \\i filename: "" gives the failed result "\\i: missing required argument";
  read os.path.expanduser(filename) as UTF-8, an OSError gives the failed
  result str(error). With a nonempty settings.destructive_warning: when
  destructive_statements_require_transaction, the transaction is not valid
  (real.pgcli.connection.executor_transaction_status is neither Active nor
  InTransaction) and real.pgcli.parseutils.is_destructive(contents,
  destructive_warning) holds, message "Destructive statements must be run
  within a transaction. Command execution stopped."; otherwise ask
  real.pgcli.session.confirm_destructive_query(contents, warning, dsn_alias,
  force_destructive) and a False answer gives "Wise choice. Command
  execution stopped.". Otherwise run the file contents through these same
  statement rules recursively (on_error RESUME continues after a failure),
  yielding their results.
  \\o [filename]: "" disables file output with "File output disabled"
  (success, not failure); otherwise path = abspath(expanduser(filename));
  when it is not an existing file create it empty (an OSError gives the
  failed result str(error) + "\\nFile output disabled" and disables file
  output); set output_file and message 'Writing to file "<path>"'.
  \\log-file [filename]: "" disables it with "Logfile capture disabled";
  otherwise path = pathlib.Path(filename).expanduser().absolute(), open it
  in "a+" mode to check it (an OSError gives the failed result str(error) +
  "\\nLogfile capture disabled" and disables logging); set log_file and
  message 'Writing to file "<path>"'.
  \\conninfo: 'You are connected to database "<dbname>" as user "<user>" on
  <where> at port "<port>".' where <where> is socket "<host>" when host
  starts with "/" and host "<host>" otherwise.
  \\T format: when format is one of real.pgcli.output.table_format_names()
  set table_format and message "Changed table format to <format>";
  otherwise "Table format <format> not recognized. Allowed formats:" then
  "\\n\\t<name>" for each name, then "\\nCurrently set to: <table_format>".
  \\echo text and \\qecho text: message text (pattern).
  \\v [on|off]: "on" / "off" set verbose_errors, anything else toggles it;
  message "Verbose errors on." or "off." (the upstream expression yields
  "off." alone when off).
\\do is registered in pgspecial to the placeholder handler (unlike \\dp
and \\z, whose handlers are replaced by dbcommands.list_privileges).
Recognize the parsed \\do command key before PGSpecial.execute and return
EvaluateError.NotImplemented without running that handler, which raises
a forbidden-to-name Python exception. Any other resolved command runs
with PGSpecial.execute(cursor, sql) on a new cursor
of the connection (None when the connection refuses a cursor); each yielded
4-tuple (title, rows, headers, status) is one result. A
psycopg.errors.ProtocolViolation from a virtual database gives a failed
result with its message and a reconnect. Unresolved commands throw
pgspecial.main.CommandNotFound (catch that imported exception by name)
and continue as SQL.
c) SQL: in explain mode prefix "EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS,
FORMAT JSON) ". Register a notice handler that appends to the title "\\n" +
message_primary and "\\n" + message_detail when present (title starts as
""). Execute on a new cursor. With a description, headers are the column
names and the result keeps the cursor rows and cursor.statusmessage;
without one the status is cursor.statusmessage. For a pgbouncer virtual
database "show help" statements run through pgconn.exec_ and return only
the command status.
d) A psycopg.DatabaseError while the connection is still open
(connection.closed == 0) becomes a failed result whose status is
click.style(error text, fg="red"), so it is shown on standard output with
the other lines. The error text is str(error), plus, when
settings.verbose_errors, "\\n" and the lines "Severity: " severity,
"Severity (non-localized): " severity_nonlocalized, "SQLSTATE code: "
sqlstate, "Message: " message_primary, "Detail: " message_detail, "Hint: "
message_hint, "Position: " statement_position, "Internal position: "
internal_position, "Internal query: " internal_query, "Where: " context,
"Schema name: " schema_name, "Table name: " table_name, "Column name: "
column_name, "Data type name: " datatype_name, "Constraint name: "
constraint_name, "File: " source_file, "Line: " source_line, "Routine: "
source_function for each psycopg Diagnostic field that is not None, joined
by "\\n". It stops the run unless on_error is RESUME. When the connection is
closed the error is not formatted: psycopg.OperationalError is
ConnectionLost(str(error)) and any other error Failed(str(error)).
KeyboardInterrupt is Interrupted; \\do was handled before
PGSpecial.execute as NotImplemented; all other exceptions are
Failed(str(error)). Python source must never use the forbidden
NotImplementedError identifier, including in an except clause; likewise
do not use type(error).__name__ or other runtime introspection.

Formatting, for each result in order: rows of a SELECT beyond the row limit
(real.pgcli.session.should_limit_rows(sql, rowcount, settings.row_limit,
settings.explain_mode)) are cut to min(row_limit, rowcount), the status
becomes "SELECT <limit>" and "The result was limited to <limit> rows" is
printed in red with click.secho. The rows reach the formatter as
real.pgcli.output.ResultSet(columns = headers, type_names from the cursor
description (cursor.adapters.types.get(type_code).name, "" when unknown or
not a cursor), rows = cott_runtime Opaque(tag="pgcli.result-rows",
value=a new Python list holding one tuple per row with the Python values
exactly as fetched, never converted), rowcount = cursor.rowcount when the
rows came from a cursor (including pgspecial results that return a cursor)
or -1 when they came from a Python list (pgspecial list results) or were
cut by the row limit). A result without rows passes Nothing.
When hide_named_query_text is on, the command is a successful special
"\\n name" execution (text stripped starts with "\\n " but not "\\ns " or
"\\nd ") and the title starts with "> ", the title is dropped. Each result
is formatted by real.pgcli.output.format_output(title, rows, status,
OutputSettings(table_format, column_date_formats, max_field_width,
decimal_format, float_format, missing_value = null_string, expanded =
PGSpecial.expanded_output or settings.expanded_output, max_width =
Some(screen.columns) when PGSpecial.auto_expand or settings.auto_expand
else Nothing, header_casing = Some(session.catalog) when
case_column_headers else Nothing, style = output_style, tuples_only, query
= text), explain_mode); the evaluation's output is the texts of the results
with at least one item joined by "\\n" and items is the sum of their item
counts. A format_output Err(Failed(message)) makes the whole evaluation
Failed(message), so the command's output is discarded as upstream does
when formatting raises.
execution_time is measured before formatting each result and total_time
after. For successful results the StatementChanges of
real.pgcli.session.classify_statement(sql, status) are OR-ed together; a
failed result makes successful false. is_special is the last result's flag.
refresh: Reset when db_changed, else All when meta_changed (or requested by
\\refresh), else SearchPath when path_changed, else Nothing. The returned
session carries the changed settings and executor and last_query = text."""
def evaluate_pgcli_command(session: Session, text: str, screen: TerminalSize) -> Result[Evaluation, EvaluateError]: ...

"""prompt_utils.confirm_destructive_query: Nothing when
real.pgcli.parseutils.is_destructive(queries, keywords) is false; Some(true)
when force; Nothing when standard input is not a terminal; otherwise ask
click.confirm("You're about to run a destructive command" + (" in " +
click.style(alias, fg="red") when dsn_alias is Some) + ".\\nDo you want to
proceed?") and return Some(answer), where click.Abort (Ctrl-C/Ctrl-D) is
Some(false)."""
def confirm_destructive_query(queries: str, keywords: CottList[str], dsn_alias: Option[str], force: bool) -> Option[bool]: ...

"""PGCli.execute_command. Start from QueryOutcome(text, successful false,
times 0, flags false).
Destructive check when settings.destructive_warning is nonempty: when
destructive_statements_require_transaction, the transaction is not valid
and real.pgcli.parseutils.is_destructive(text, destructive_warning) holds,
print "Destructive statements must be run within a transaction." and treat
the command as cancelled; otherwise ask
real.pgcli.session.confirm_destructive_query(text, destructive_warning,
dsn_alias, force_destructive): Some(false) prints "Wise choice!" and is
cancelled; Some(true) without force prints "Your call!".
Then real.pgcli.session.evaluate_pgcli_command(session, text, screen).
Cancelled or Interrupted: when destructive_warning_restarts_connection,
reconnect (real.pgcli.connection.reconnect_executor with all "") and print
in red on standard error "cancelled query and restarted connection";
otherwise print in red on standard error "cancelled query".
NotImplemented prints "Not Yet Implemented." in yellow. ConnectionLost
prints the message in red on standard error, then unless this is already a
retry: print "Reconnecting..." in green, reconnect; on failure print
"Reconnect Failed" in red and the error text in red on standard error; on
success print "Reconnected!" in green and, when auto_retry_closed_connection
or the user confirms click.confirm("Run the query from before
reconnecting?") (Abort counts as no), print "Running query..." in green and
run this whole procedure once more as a retry. Failed prints the message in
red on standard error. A quit evaluation returns quit = true without
routing output.
Output routing for a successful evaluation: when output_file is set and
text does not start with "\\o ", "\\log-file", "\\? " or "\\echo ", append to
that file (UTF-8) the text line (unless the named-query quiet rule of
real.pgcli.session.evaluate_pgcli_command hides it), the evaluation output,
and an empty line, each through click.echo(file=...); an OSError is
printed in red on standard error. Otherwise, when items > 0, show the
output with the pager rule: click.echo when PGSpecial
pager_config is 0, when settings.scripted, or while a \\watch is running;
with pager_config 1 and table_format != "csv" use click.echo_via_pager only
when the output's "\\n"-separated line count is at least screen.rows - 4 or
any line with ANSI escapes removed (regex \\x1b(\\[.*?[@-~]|\\].*?(\\x07|\\x1b\\\\)))
is longer than screen.columns, else click.echo; with pager_config 2 always
click.echo_via_pager. Then, when log_file is set, text does not start with
those prefixes and is not blank, append to the log file the current
datetime.datetime.now().isoformat(), the text line (same quiet rule), the
evaluation output, and an empty line; an OSError is printed in red on
standard error. KeyboardInterrupt during output is ignored.
Timing: when PGSpecial timing_enabled, print
real.pgcli.output.timing_report(total_time, execution_time).
The outcome carries the evaluation's session (or the reconnected one), its
query record, refresh and quit."""
def execute_pgcli_command(session: Session, text: str, screen: TerminalSize) -> CommandOutcome: ...

"""PGCli.handle_watch_command: (watch_sql, seconds) =
pgspecial.iocommands.get_watch_command(text). When watch_sql is not None
and blank, use session.last_query; when that is "" print in red on standard
error "\\watch cannot be used with an empty query" and behave as if nothing
was watched. With a watch statement: repeat
real.pgcli.session.execute_pgcli_command(session, watch_sql, screen) (the
pager is not used while watching), then print "Waiting for <seconds>
seconds before repeating" and time.sleep(seconds), until KeyboardInterrupt
(at any point) stops the loop; the outcome is the last completed execution
(or a failed record for the text when none completed). Without a watch
statement execute text once through execute_pgcli_command. In every case
the returned session's last_query is the executed query text."""
def watch_pgcli_command(session: Session, text: str, screen: TerminalSize) -> CommandOutcome: ...

"""PGCli._execute_statements: run every statement given by the splitting rule
of real.pgcli.session.script_statements(text), applied by a private helper
of this implementation (a long script's statement list must not cross the
facade boundary), through real.pgcli.session.watch_pgcli_command, carrying
the session forward. A statement whose outcome is not successful makes ok
false and stops the run unless settings.on_error is "RESUME". A quit
outcome stops the run with quit = true."""
def run_script_text(session: Session, text: str, screen: TerminalSize) -> ScriptOutcome: ...

"""_check_ongoing_transaction_and_allow_quitting: quit = true when the
transaction is not valid (real.pgcli.connection.executor_transaction_status
is neither Active nor InTransaction). Otherwise loop on click.prompt("A transaction is ongoing.
Choose `c` to COMMIT, `r` to ROLLBACK, `a` to abort exit, `force` to exit
anyway.", default="a") (click.Abort prints an empty line and counts as
"a"), lower-cased: "a" gives quit = false; "force" gives quit = true; "c"
runs "commit" and "r" runs "rollback" through
real.pgcli.session.execute_pgcli_command(session, answer command, screen)
and quit is whether that command succeeded; any other answer asks again.
The returned session is the latest one."""
def confirm_quit_with_transaction(session: Session, screen: TerminalSize) -> QuitDecision: ...

"""-l/--list: run PGExecute.full_databases' query exactly:
SELECT d.datname as "Name", pg_catalog.pg_get_userbyid(d.datdba) as "Owner",
pg_catalog.pg_encoding_to_char(d.encoding) as "Encoding", d.datcollate as
"Collate", d.datctype as "Ctype", pg_catalog.array_to_string(d.datacl,
E'\\n') AS "Access privileges" FROM pg_catalog.pg_database d ORDER BY 1,
and return the text of real.pgcli.output.format_output(Some("List of
databases"), Some(ResultSet(column names, type names, the fetched rows as a
"pgcli.result-rows" Opaque, cursor.rowcount)), Some(cursor.statusmessage),
OutputSettings(table_format "ascii", no column date formats,
max_field_width Some(500), other fields at their defaults), false).
Errors, including a format_output error, are Failed(str(error))."""
def database_listing(executor: Executor) -> Result[str, EvaluateError]: ...

"""--ping: run "SELECT 1" through the connection; true when it completes,
false on any exception."""
def ping_database(executor: Executor) -> bool: ...

"""Execute each init command in order as PGExecute.run(command) without
pgspecial and without an exception formatter: every statement given by the
splitting rule of real.pgcli.session.statement_texts_for_run(command),
applied by a private helper of this implementation, runs as plain SQL and
its rows are discarded. The first exception is Failed(str(error)) and stops."""
def run_init_commands(executor: Executor, commands: CottList[str]) -> Result[Unit, EvaluateError]: ...

"""PGExecute.view_definition for \\ev: run WITH v AS (SELECT %s::
pg_catalog.regclass::pg_catalog.oid AS v_oid) SELECT nspname, relname,
relkind, pg_catalog.pg_get_viewdef(c.oid, true), array_remove(array_remove(
c.reloptions,'check_option=local'), 'check_option=cascaded') AS reloptions,
CASE WHEN 'check_option=local' = ANY (c.reloptions) THEN 'LOCAL'::text WHEN
'check_option=cascaded' = ANY (c.reloptions) THEN 'CASCADED'::text ELSE NULL
END AS checkoption FROM pg_catalog.pg_class c LEFT JOIN
pg_catalog.pg_namespace n ON (c.relnamespace = n.oid) JOIN v ON (c.oid =
v.v_oid) with spec as parameter. psycopg.ProgrammingError gives
Failed("View <spec> does not exist."). The result is "CREATE OR REPLACE
MATERIALIZED VIEW {name} AS \\n{stmt}" for relkind "m", else "CREATE OR
REPLACE VIEW {name} AS \\n{stmt}", composed with psycopg.sql
(Identifier(nspname, relname), SQL(viewdef)) and rendered with as_string."""
def view_definition_sql(executor: Executor, spec: str) -> Result[str, EvaluateError]: ...

"""PGExecute.function_definition for \\ef: WITH f AS (SELECT
%s::pg_catalog.regproc::pg_catalog.oid AS f_oid) SELECT
pg_catalog.pg_get_functiondef(f.f_oid) FROM f with spec as parameter, the
first column of the first row; psycopg.ProgrammingError gives
Failed("Function <spec> does not exist.")."""
def function_definition_sql(executor: Executor, spec: str) -> Result[str, EvaluateError]: ...

__all__ = ["CommandOutcome", "EvaluateError", "EvaluateError_ConnectionLost", "EvaluateError_Failed", "EvaluateError_Interrupted", "EvaluateError_NotImplemented", "Evaluation", "QueryOutcome", "QuitDecision", "RefreshKind", "RefreshKind_All", "RefreshKind_Nothing", "RefreshKind_Reset", "RefreshKind_SearchPath", "ScriptOutcome", "Session", "SessionSettings", "SpecialCommandEntry", "SpecialHandle", "SpecialSetup", "SpecialState", "StatementChanges", "TerminalSize", "change_db_arguments", "classify_statement", "confirm_destructive_query", "confirm_quit_with_transaction", "create_special_handle", "database_listing", "evaluate_pgcli_command", "execute_pgcli_command", "function_definition_sql", "named_query_names", "ping_database", "run_init_commands", "run_script_text", "script_statements", "should_limit_rows", "special_command_catalog", "special_display_state", "statement_texts_for_run", "view_definition_sql", "watch_pgcli_command"]
