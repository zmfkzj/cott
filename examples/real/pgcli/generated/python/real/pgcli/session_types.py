from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.pgcli.connection_types import Executor
from real.pgcli.output_types import OutputStyle

"""A live pgspecial.main.PGSpecial instance (its own expanded_output,
auto_expand, timing_enabled, pager_config and command registry) whose
pgspecial.namedqueries.NamedQueries.instance was set for this session."""
SpecialHandle: TypeAlias = Opaque[Literal["pgcli.pgspecial"]]

"""PGCli's mutable output and execution settings. output_file is the \\o target
and log_file the \\log-file (or --log-file) target, both absolute paths.
scripted is true while running -c/-f commands (the pager is never used then).
completion_refreshing tells whether a background completion refresh is running
(it selects the \\refresh message)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SessionSettings:
    __hash__ = None
    table_format: str
    expanded_output: bool
    auto_expand: bool
    multi_line: bool
    multiline_mode: str
    vi_mode: bool
    explain_mode: bool
    smart_completion: bool
    hide_named_query_text: bool
    verbose_errors: bool
    output_file: Option[str]
    log_file: Option[str]
    row_limit: I64
    max_field_width: Option[U32]
    null_string: str
    on_error: str
    destructive_warning: CottList[str]
    destructive_warning_restarts_connection: bool
    destructive_statements_require_transaction: bool
    force_destructive: bool
    auto_retry_closed_connection: bool
    tuples_only: bool
    less_chatty: bool
    decimal_format: str
    float_format: str
    column_date_formats: FrozenMap[str, str]
    case_column_headers: bool
    output_style: Option[OutputStyle]
    prompt_format: str
    prompt_dsn_format: Option[str]
    dsn_alias: Option[str]
    scripted: bool
    completion_refreshing: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "table_format", _cott_validate_abi(self.table_format, str, path="$.table_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "expanded_output", _cott_validate_abi(self.expanded_output, bool, path="$.expanded_output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_expand", _cott_validate_abi(self.auto_expand, bool, path="$.auto_expand"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multi_line", _cott_validate_abi(self.multi_line, bool, path="$.multi_line"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multiline_mode", _cott_validate_abi(self.multiline_mode, str, path="$.multiline_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "vi_mode", _cott_validate_abi(self.vi_mode, bool, path="$.vi_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "explain_mode", _cott_validate_abi(self.explain_mode, bool, path="$.explain_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "smart_completion", _cott_validate_abi(self.smart_completion, bool, path="$.smart_completion"))
        if not _cott_validated_construction():
            object.__setattr__(self, "hide_named_query_text", _cott_validate_abi(self.hide_named_query_text, bool, path="$.hide_named_query_text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "verbose_errors", _cott_validate_abi(self.verbose_errors, bool, path="$.verbose_errors"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output_file", _cott_validate_abi(self.output_file, Option[str], path="$.output_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "log_file", _cott_validate_abi(self.log_file, Option[str], path="$.log_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "row_limit", _cott_validate_abi(self.row_limit, I64, path="$.row_limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_field_width", _cott_validate_abi(self.max_field_width, Option[U32], path="$.max_field_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "null_string", _cott_validate_abi(self.null_string, str, path="$.null_string"))
        if not _cott_validated_construction():
            object.__setattr__(self, "on_error", _cott_validate_abi(self.on_error, str, path="$.on_error"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destructive_warning", _cott_validate_abi(self.destructive_warning, CottList[str], path="$.destructive_warning"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destructive_warning_restarts_connection", _cott_validate_abi(self.destructive_warning_restarts_connection, bool, path="$.destructive_warning_restarts_connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destructive_statements_require_transaction", _cott_validate_abi(self.destructive_statements_require_transaction, bool, path="$.destructive_statements_require_transaction"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_destructive", _cott_validate_abi(self.force_destructive, bool, path="$.force_destructive"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_retry_closed_connection", _cott_validate_abi(self.auto_retry_closed_connection, bool, path="$.auto_retry_closed_connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tuples_only", _cott_validate_abi(self.tuples_only, bool, path="$.tuples_only"))
        if not _cott_validated_construction():
            object.__setattr__(self, "less_chatty", _cott_validate_abi(self.less_chatty, bool, path="$.less_chatty"))
        if not _cott_validated_construction():
            object.__setattr__(self, "decimal_format", _cott_validate_abi(self.decimal_format, str, path="$.decimal_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "float_format", _cott_validate_abi(self.float_format, str, path="$.float_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "column_date_formats", _cott_validate_abi(self.column_date_formats, FrozenMap[str, str], path="$.column_date_formats"))
        if not _cott_validated_construction():
            object.__setattr__(self, "case_column_headers", _cott_validate_abi(self.case_column_headers, bool, path="$.case_column_headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output_style", _cott_validate_abi(self.output_style, Option[OutputStyle], path="$.output_style"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt_format", _cott_validate_abi(self.prompt_format, str, path="$.prompt_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt_dsn_format", _cott_validate_abi(self.prompt_dsn_format, Option[str], path="$.prompt_dsn_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn_alias", _cott_validate_abi(self.dsn_alias, Option[str], path="$.dsn_alias"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scripted", _cott_validate_abi(self.scripted, bool, path="$.scripted"))
        if not _cott_validated_construction():
            object.__setattr__(self, "completion_refreshing", _cott_validate_abi(self.completion_refreshing, bool, path="$.completion_refreshing"))

"""One pgcli session. catalog is the completer's current
real.pgcli.completion.CompletionCatalog (its casing word list is used for
column headers when case_column_headers is on; the empty catalog before the
first completion refresh). last_query is the text of the last command handled
(query_history[-1].query), "" when none."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Session:
    __hash__ = None
    settings: SessionSettings
    executor: Executor
    special: Opaque[Literal["pgcli.pgspecial"]]
    catalog: Opaque[Literal["pgcli.completion-catalog"]]
    last_query: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "settings", _cott_validate_abi(self.settings, SessionSettings, path="$.settings"))
        if not _cott_validated_construction():
            object.__setattr__(self, "executor", _cott_validate_abi(self.executor, Executor, path="$.executor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "special", _cott_validate_abi(self.special, Opaque[Literal["pgcli.pgspecial"]], path="$.special"))
        if not _cott_validated_construction():
            object.__setattr__(self, "catalog", _cott_validate_abi(self.catalog, Opaque[Literal["pgcli.completion-catalog"]], path="$.catalog"))
        if not _cott_validated_construction():
            object.__setattr__(self, "last_query", _cott_validate_abi(self.last_query, str, path="$.last_query"))

"""The terminal the output is shown on, in character cells."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TerminalSize:
    __hash__ = None
    columns: U32
    rows: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, U32, path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, U32, path="$.rows"))

"""MetaQuery: the record of one handled command. total_time and execution_time
are seconds."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryOutcome:
    __hash__ = None
    query: str
    successful: bool
    total_time: F64
    execution_time: F64
    meta_changed: bool
    db_changed: bool
    path_changed: bool
    mutated: bool
    is_special: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, str, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "successful", _cott_validate_abi(self.successful, bool, path="$.successful"))
        if not _cott_validated_construction():
            object.__setattr__(self, "total_time", _cott_validate_abi(self.total_time, F64, path="$.total_time"))
        if not _cott_validated_construction():
            object.__setattr__(self, "execution_time", _cott_validate_abi(self.execution_time, F64, path="$.execution_time"))
        if not _cott_validated_construction():
            object.__setattr__(self, "meta_changed", _cott_validate_abi(self.meta_changed, bool, path="$.meta_changed"))
        if not _cott_validated_construction():
            object.__setattr__(self, "db_changed", _cott_validate_abi(self.db_changed, bool, path="$.db_changed"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path_changed", _cott_validate_abi(self.path_changed, bool, path="$.path_changed"))
        if not _cott_validated_construction():
            object.__setattr__(self, "mutated", _cott_validate_abi(self.mutated, bool, path="$.mutated"))
        if not _cott_validated_construction():
            object.__setattr__(self, "is_special", _cott_validate_abi(self.is_special, bool, path="$.is_special"))

"""What completion data must be refreshed after a command, most drastic first:
Reset (the database changed: clear the completer and refresh, keeping only
learned keyword priorities), All (DDL/commit/rollback or \\refresh: refresh
keeping all learned priorities), SearchPath (only re-read the search path),
Nothing."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshKind_Nothing:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshKind_Reset:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshKind_All:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshKind_SearchPath:
    pass

RefreshKind: TypeAlias = Union[RefreshKind_Nothing, RefreshKind_Reset, RefreshKind_All, RefreshKind_SearchPath]

"""The result of one handled command: the updated session, the MetaQuery, the
refresh to perform, and quit when a quit command (\\q, :q, quit, exit) was
executed."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandOutcome:
    __hash__ = None
    session: Session
    query: QueryOutcome
    refresh: RefreshKind
    quit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "session", _cott_validate_abi(self.session, Session, path="$.session"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, QueryOutcome, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "refresh", _cott_validate_abi(self.refresh, RefreshKind, path="$.refresh"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quit", _cott_validate_abi(self.quit, bool, path="$.quit"))

"""Output of one evaluated command before routing: output is every output item of
the command's results joined by "\\n" (upstream "\\n".join(output)) and items is
how many items there were (0 means upstream's empty output list)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Evaluation:
    __hash__ = None
    session: Session
    output: str
    items: U64
    query: QueryOutcome
    refresh: RefreshKind
    quit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "session", _cott_validate_abi(self.session, Session, path="$.session"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output", _cott_validate_abi(self.output, str, path="$.output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, U64, path="$.items"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, QueryOutcome, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "refresh", _cott_validate_abi(self.refresh, RefreshKind, path="$.refresh"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quit", _cott_validate_abi(self.quit, bool, path="$.quit"))

"""Failures of evaluate_pgcli_command that execute_pgcli_command handles:
ConnectionLost is a psycopg.OperationalError (it triggers the reconnect
logic), Interrupted is a KeyboardInterrupt, NotImplemented is pgspecial's
unsupported \\do placeholder command, Failed is any other exception
with message = str(error)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluateError_ConnectionLost:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluateError_Interrupted:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluateError_NotImplemented:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluateError_Failed:
    __hash__ = None
    message: str

EvaluateError: TypeAlias = Union[EvaluateError_ConnectionLost, EvaluateError_Interrupted, EvaluateError_NotImplemented, EvaluateError_Failed]

"""The pgspecial registry entries shown by \\? and offered by completion."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SpecialCommandEntry:
    __hash__ = None
    command: str
    syntax: str
    description: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "command", _cott_validate_abi(self.command, str, path="$.command"))
        if not _cott_validated_construction():
            object.__setattr__(self, "syntax", _cott_validate_abi(self.syntax, str, path="$.syntax"))
        if not _cott_validated_construction():
            object.__setattr__(self, "description", _cott_validate_abi(self.description, str, path="$.description"))

"""Inputs of create_special_handle: timing is [main] timing (false with -t),
enable_pager is [main] enable_pager and config_path is the user's pgclirc
path whose [named queries] section the named-query commands read and rewrite."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SpecialSetup:
    __hash__ = None
    timing: bool
    enable_pager: bool
    config_path: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "timing", _cott_validate_abi(self.timing, bool, path="$.timing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "enable_pager", _cott_validate_abi(self.enable_pager, bool, path="$.enable_pager"))
        if not _cott_validated_construction():
            object.__setattr__(self, "config_path", _cott_validate_abi(self.config_path, Path, path="$.config_path"))

"""Statement-level classification of one executed statement."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StatementChanges:
    __hash__ = None
    mutated: bool
    meta_changed: bool
    db_changed: bool
    path_changed: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mutated", _cott_validate_abi(self.mutated, bool, path="$.mutated"))
        if not _cott_validated_construction():
            object.__setattr__(self, "meta_changed", _cott_validate_abi(self.meta_changed, bool, path="$.meta_changed"))
        if not _cott_validated_construction():
            object.__setattr__(self, "db_changed", _cott_validate_abi(self.db_changed, bool, path="$.db_changed"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path_changed", _cott_validate_abi(self.path_changed, bool, path="$.path_changed"))

"""The statement splitting of PGExecute.run. Strip text; "" gives no
statement. Remove beginning comments: repeatedly match the regex
^(/\\*.*?\\*/|--.*?)(?:\\n|$) (re.DOTALL) at the start, remember the match and
continue after it with leading whitespace stripped. Split the remainder with
sqlparse.split, then put the removed comments in front. Each piece becomes
sqlparse.format(piece, strip_comments=True).strip(), then trailing ";"
characters are stripped (rstrip(";")) and the result stripped again; empty
results are dropped. Order is kept."""
"""_execute_statements splitting (-c, -f and \\watch-aware runs): split text with
sqlparse.split and take pieces from the front; skip pieces that are blank
after strip(); a stripped piece that starts with "\\\\" and contains a line
feed is cut at its first line feed: the first line is the statement and the
rest is split again with sqlparse.split and put back in front of the
remaining pieces. Each returned statement is stripped."""
"""mutated: status's first whitespace-separated word, lower-cased, is insert,
update or delete ("" status is not mutating). meta_changed: sql's first
whitespace-separated word, lower-cased, is alter, create, drop, commit or
rollback. db_changed: sql's first word, lower-cased, is use, \\c or \\connect.
path_changed: sql lower-cased contains "set search_path". A blank sql gives
false for the sql-based flags."""
"""PGCli._should_limit_output: false in explain mode; false unless sql's first
whitespace-separated word, lower-cased, is select; false when any token of
sqlparse.parse(sql) (flattened) matches keyword LIMIT
(token.match(sqlparse.tokens.Keyword, "LIMIT")); otherwise row_limit != 0
and rowcount > row_limit."""
"""The argument split of \\c / \\connect / use: all matches of the regex
"[^"]*"|[^"'\\s]+ in pattern, in order, kept exactly as matched (upstream
discards its quote stripping, so double quotes stay), padded with "" to
four items: database, user, host, port. Extra matches are kept after the
fourth."""
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
"""Every key of the PGSpecial commands registry in dict order, with its
registered syntax and description (aliases included, hidden entries
included)."""
"""pgspecial.namedqueries.NamedQueries.instance.list(): the names in the
[named queries] section, in file order."""
"""Read the PGSpecial flags: expanded_output, auto_expand, timing_enabled and
pager_config (0 off, 1 long output only, 2 always)."""
"""The PGSpecial display flags."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SpecialState:
    __hash__ = None
    expanded_output: bool
    auto_expand: bool
    timing_enabled: bool
    pager_config: I64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "expanded_output", _cott_validate_abi(self.expanded_output, bool, path="$.expanded_output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_expand", _cott_validate_abi(self.auto_expand, bool, path="$.auto_expand"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timing_enabled", _cott_validate_abi(self.timing_enabled, bool, path="$.timing_enabled"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pager_config", _cott_validate_abi(self.pager_config, I64, path="$.pager_config"))

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
"""prompt_utils.confirm_destructive_query: Nothing when
real.pgcli.parseutils.is_destructive(queries, keywords) is false; Some(true)
when force; Nothing when standard input is not a terminal; otherwise ask
click.confirm("You're about to run a destructive command" + (" in " +
click.style(alias, fg="red") when dsn_alias is Some) + ".\\nDo you want to
proceed?") and return Some(answer), where click.Abort (Ctrl-C/Ctrl-D) is
Some(false)."""
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
"""PGCli._execute_statements: run every statement given by the splitting rule
of real.pgcli.session.script_statements(text), applied by a private helper
of this implementation (a long script's statement list must not cross the
facade boundary), through real.pgcli.session.watch_pgcli_command, carrying
the session forward. A statement whose outcome is not successful makes ok
false and stops the run unless settings.on_error is "RESUME". A quit
outcome stops the run with quit = true."""
"""Whether quitting may proceed, with the latest session."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QuitDecision:
    __hash__ = None
    session: Session
    quit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "session", _cott_validate_abi(self.session, Session, path="$.session"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quit", _cott_validate_abi(self.quit, bool, path="$.quit"))

"""The result of running a script text."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ScriptOutcome:
    __hash__ = None
    session: Session
    ok: bool
    quit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "session", _cott_validate_abi(self.session, Session, path="$.session"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ok", _cott_validate_abi(self.ok, bool, path="$.ok"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quit", _cott_validate_abi(self.quit, bool, path="$.quit"))

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
"""--ping: run "SELECT 1" through the connection; true when it completes,
false on any exception."""
"""Execute each init command in order as PGExecute.run(command) without
pgspecial and without an exception formatter: every statement given by the
splitting rule of real.pgcli.session.statement_texts_for_run(command),
applied by a private helper of this implementation, runs as plain SQL and
its rows are discarded. The first exception is Failed(str(error)) and stops."""
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
"""PGExecute.function_definition for \\ef: WITH f AS (SELECT
%s::pg_catalog.regproc::pg_catalog.oid AS f_oid) SELECT
pg_catalog.pg_get_functiondef(f.f_oid) FROM f with spec as parameter, the
first column of the first row; psycopg.ProgrammingError gives
Failed("Function <spec> does not exist.")."""
__all__ = ["CommandOutcome", "EvaluateError", "EvaluateError_ConnectionLost", "EvaluateError_Failed", "EvaluateError_Interrupted", "EvaluateError_NotImplemented", "Evaluation", "QueryOutcome", "QuitDecision", "RefreshKind", "RefreshKind_All", "RefreshKind_Nothing", "RefreshKind_Reset", "RefreshKind_SearchPath", "ScriptOutcome", "Session", "SessionSettings", "SpecialCommandEntry", "SpecialHandle", "SpecialSetup", "SpecialState", "StatementChanges", "TerminalSize"]
