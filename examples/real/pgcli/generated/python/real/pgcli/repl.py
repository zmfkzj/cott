from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with

from real.pgcli.repl_types import PromptInfo, ReplSettings, StyledText, ToolbarState
from real.pgcli.completion_types import CompleterSettings, MetadataRefreshRequest
from real.pgcli.config_types import ConfigEntry
from real.pgcli.session_types import Session

def render_prompt(template: str, info: PromptInfo) -> str:
    """PGCli.get_prompt on template: replace, in this order and each everywhere: "\\dsn_alias"
with info.dsn_alias, "\\t" with now_text, "\\u" with user or "(none)", "\\H"
with host or "(none)", "\\h" with short_host or "(none)", "\\d" with dbname or
"(none)", "\\p" with the port or "5432" when Nothing, "\\i" with str(pid),
"\\#" with "#" for a superuser else ">", "\\n" with a line feed and "\\T" with
transaction_indicator. Every "\\x" sequence here is a literal backslash
followed by the letters."""
    template = _cott_validate_abi(template, str, path="$.template")
    info = _cott_validate_abi(info, PromptInfo, path="$.info")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/repl/render_prompt.py", "487da5006c6260ae2d78f86db692681038ecba57f5e33f5c45b202f601b5463e", "render_prompt", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.repl.render_prompt")
        _result = _implementation(template, info)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.repl.render_prompt"
        if _error.span is None:
            _error.span = {"end_byte":2514,"end_column":1,"end_line":81,"start_byte":1908,"start_column":1,"start_line":68}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.repl.render_prompt", phase="implementation-call", span={"end_byte":2514,"end_column":1,"end_line":81,"start_byte":1908,"start_column":1,"start_line":68}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.repl.render_prompt", phase="implementation-call", span={"end_byte":2514,"end_column":1,"end_line":81,"start_byte":1908,"start_column":1,"start_line":68}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def prompt_message_text(prompt_format: str, prompt_dsn_format: Option[str], info: PromptInfo) -> str:
    """The get_message callable of PGCli._build_cli: the format is
prompt_dsn_format when info.dsn_alias is nonempty and prompt_dsn_format is
Some, otherwise prompt_format. text = real.pgcli.repl.render_prompt(template,
info). When the format equals the default "\\u@\\h:\\d> " and text is longer
than 30 code points, text = render_prompt("\\d> ", info). Finally every
literal four-character "\\x1b" becomes the ESC character (U+001B), so the
caller can wrap the result in prompt_toolkit ANSI(...)."""
    prompt_format = _cott_validate_abi(prompt_format, str, path="$.prompt_format")
    prompt_dsn_format = _cott_validate_abi(prompt_dsn_format, Option[str], path="$.prompt_dsn_format")
    info = _cott_validate_abi(info, PromptInfo, path="$.info")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/repl/prompt_message_text.py", "192a393ca133b5eaf69db6f96d0a1723af3c6e7245c1311af8b0bdeb85e3e940", "prompt_message_text", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.repl.prompt_message_text")
        _result = _implementation(prompt_format, prompt_dsn_format, info)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.repl.prompt_message_text"
        if _error.span is None:
            _error.span = {"end_byte":3167,"end_column":1,"end_line":94,"start_byte":2514,"start_column":1,"start_line":81}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.repl.prompt_message_text", phase="implementation-call", span={"end_byte":3167,"end_column":1,"end_line":94,"start_byte":2514,"start_column":1,"start_line":81}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.repl.prompt_message_text", phase="implementation-call", span={"end_byte":3167,"end_column":1,"end_line":94,"start_byte":2514,"start_column":1,"start_line":81}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def continuation_prompt(width: I64, continuation_char: str) -> str:
    """get_continuation: continuation_char repeated width - 1 times (no repetition
when width < 2) followed by one space. width is a terminal cell count
(at most 10,000 cells); the caller shows it with style "class:continuation"."""
    width = _cott_validate_abi(width, I64, path="$.width")
    continuation_char = _cott_validate_abi(continuation_char, str, path="$.continuation_char")
    if not (_cott_contract_condition(((width <= 10000)), "real.pgcli.repl.continuation_prompt", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="real.pgcli.repl.continuation_prompt", clause="requires:1", phase="requires", span={"end_byte":3517,"end_column":28,"end_line":101,"start_byte":3494,"start_column":5,"start_line":101}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/repl/continuation_prompt.py", "532d5f107af6aaf9968052cd054a069de01180d64376b86a599b88cda0ca4d3a", "continuation_prompt", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.repl.continuation_prompt")
        _result = _implementation(width, continuation_char)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.repl.continuation_prompt"
        if _error.span is None:
            _error.span = {"end_byte":3573,"end_column":1,"end_line":107,"start_byte":3167,"start_column":1,"start_line":94}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.repl.continuation_prompt", phase="implementation-call", span={"end_byte":3573,"end_column":1,"end_line":107,"start_byte":3167,"start_column":1,"start_line":94}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.repl.continuation_prompt", phase="implementation-call", span={"end_byte":3573,"end_column":1,"end_line":107,"start_byte":3167,"start_column":1,"start_line":94}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition((_cott_ends_with(_result, " ")), "real.pgcli.repl.continuation_prompt", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.repl.continuation_prompt", clause="ensures:2", phase="ensures", span={"end_byte":3555,"end_column":37,"end_line":103,"start_byte":3523,"start_column":5,"start_line":103}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def toolbar_fragments(toolbar: ToolbarState) -> CottList[StyledText]:
    """create_toolbar_tokens_func: in order ("class:bottom-toolbar", " "); then
("class:bottom-toolbar.on", "[F2] Smart Completion: ON  ") or
("class:bottom-toolbar.off", "[F2] Smart Completion: OFF  "); then
("class:bottom-toolbar.on", "[F3] Multiline: ON  ") or
("class:bottom-toolbar.off", "[F3] Multiline: OFF  "); when multi_line,
("class:bottom-toolbar", " ([Esc] [Enter] to execute]) ") for multiline_mode
"safe" else ("class:bottom-toolbar", " (Semi-colon [;] will end the line) ");
then ("class:bottom-toolbar", "[F4] Vi-mode (" + vi_input_mode + ")  ") in
vi mode else ("class:bottom-toolbar", "[F4] Emacs-mode  "); then
("class:bottom-toolbar", "[F5] Explain: ON ") or ("class:bottom-toolbar",
"[F5] Explain: OFF "); then ("class:bottom-toolbar.transaction.failed",
"     Failed transaction") when failed_transaction; then
("class:bottom-toolbar.transaction.valid", "     Transaction") when
valid_transaction; then ("class:bottom-toolbar", "     Refreshing
completions...") when refreshing."""
    toolbar = _cott_validate_abi(toolbar, ToolbarState, path="$.toolbar")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/repl/toolbar_fragments.py", "f36061e27f4b99b25e7e4396e6439934a2e91bbae7f24208258f44337dece0dd", "toolbar_fragments", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.repl.toolbar_fragments")
        _result = _implementation(toolbar)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.repl.toolbar_fragments"
        if _error.span is None:
            _error.span = {"end_byte":4761,"end_column":1,"end_line":130,"start_byte":3573,"start_column":1,"start_line":107}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.repl.toolbar_fragments", phase="implementation-call", span={"end_byte":4761,"end_column":1,"end_line":130,"start_byte":3573,"start_column":1,"start_line":107}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.repl.toolbar_fragments", phase="implementation-call", span={"end_byte":4761,"end_column":1,"end_line":130,"start_byte":3573,"start_column":1,"start_line":107}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[StyledText], path="$.return")
    if not (_cott_contract_condition(((len(_result) >= 5)), "real.pgcli.repl.toolbar_fragments", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.repl.toolbar_fragments", clause="ensures:1", phase="ensures", span={"end_byte":4743,"end_column":30,"end_line":126,"start_byte":4718,"start_column":5,"start_line":126}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledText], path="$.return", validator=_cott_validate_abi)
    return _result

def buffer_should_submit(text: str, multi_line: bool, multiline_mode: str) -> bool:
    """pgbuffer.buffer_should_be_handled for the current buffer text: true when
multi_line is false; false when multiline_mode is "safe"; otherwise, with t
= text.strip(), true when t starts with "\\", ends with "\\e" or "\\G", is
complete, equals "exit", "quit" or ":q", or is "". t is complete when
sqlparse.format(t, strip_comments=True).strip() ends with ";" and
real.pgcli.parseutils.is_open_quote(t) is false."""
    text = _cott_validate_abi(text, str, path="$.text")
    multi_line = _cott_validate_abi(multi_line, bool, path="$.multi_line")
    multiline_mode = _cott_validate_abi(multiline_mode, str, path="$.multiline_mode")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/repl/buffer_should_submit.py", "abec5ac7b05f65071fd77d9c6593ace041c2aa29cc93603630caf57911371d1b", "buffer_should_submit", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.repl.buffer_should_submit")
        _result = _implementation(text, multi_line, multiline_mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.repl.buffer_should_submit"
        if _error.span is None:
            _error.span = {"end_byte":5347,"end_column":1,"end_line":144,"start_byte":4761,"start_column":1,"start_line":130}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.repl.buffer_should_submit", phase="implementation-call", span={"end_byte":5347,"end_column":1,"end_line":144,"start_byte":4761,"start_column":1,"start_line":130}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.repl.buffer_should_submit", phase="implementation-call", span={"end_byte":5347,"end_column":1,"end_line":144,"start_byte":4761,"start_column":1,"start_line":130}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    if not (_cott_contract_condition(((multi_line or _result)), "real.pgcli.repl.buffer_should_submit", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.repl.buffer_should_submit", clause="ensures:1", phase="ensures", span={"end_byte":5329,"end_column":35,"end_line":140,"start_byte":5299,"start_column":5,"start_line":140}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def run_pgcli_repl(session: Session, settings: ReplSettings) -> Session:
    """PGCli.run_cli's interactive part, built with the lock-selected
prompt_toolkit without defining any class.

History and completion: history = prompt_toolkit.history.FileHistory(
settings.history_file) (the prompt_toolkit file format: "\\n# <timestamp>"
then each line prefixed with "+"). Keep in mutable local cells (for example
one-element lists) the current session, the current
real.pgcli.completion.CompletionCatalog (starting as session.catalog), the
real.pgcli.completion.PrevalenceHandle (starting as
real.pgcli.completion.prevalence_from of two empty maps) and whether a
refresh runs.
Start a completion refresh (persisting nothing): a daemon threading.Thread
named "completion_refresh" that uses real.pgcli.connection.copy_executor(
executor) (or the session executor when settings.single_connection; a
virtual database never refreshes), then
real.pgcli.completion.refresh_completion_metadata(that executor,
settings.refresh) giving a new catalog, then feeds the last 100 history
strings to real.pgcli.completion.update_prevalence(prevalence, text, true),
closes a copied executor with real.pgcli.connection.close_executor, stores
the new catalog (also as the session's catalog) and invalidates the
application. A refresh requested while one runs restarts it after the
current one finishes. persist modes: Reset replaces the prevalence with
real.pgcli.completion.clear_prevalence_names(prevalence) (keeps keyword
counts); All keeps it; the initial refresh starts from empty counts.
SearchPath only replaces the catalog with
real.pgcli.completion.catalog_with_search_path(catalog, the list from
real.pgcli.connection.read_search_path) (an error keeps the catalog).

Completer: prompt_toolkit.completion.ThreadedCompleter wrapping a
DynamicCompleter-equivalent built without subclassing:
typing.cast(Completer, types.SimpleNamespace(get_completions=lambda
document, complete_event: <private helper>(cells, document,
complete_event))). The helper receives the document: when document.text starts with "\\i " it yields
prompt_toolkit.completion.PathCompleter(expanduser=True) completions for
the word after "\\i "; otherwise it calls
real.pgcli.completion.complete_sql_text(CompletionRequest(document.text,
document.cursor_position, smart_completion, the current catalog,
settings.completer, the current prevalence, special commands from
real.pgcli.session.special_command_catalog as SpecialCommandInfo values,
names from real.pgcli.session.named_query_names,
real.pgcli.output.table_format_names())) and yields the prompt_toolkit
Completion objects of the returned CompletionList
(cast(list[Completion], completions.unwrap())) in order.

PromptSession(lexer=PygmentsLexer(pygments.lexers.sql.PostgresLexer),
reserve_space_for_menu=min_num_menu_lines, message=a callable returning
ANSI(real.pgcli.repl.prompt_message_text(...)) with a PromptInfo from the
current executor (user, host, real.pgcli.connection.short_host_name(host),
dbname, port, pid, superuser, the transaction indicator of
real.pgcli.connection.executor_transaction_status) and
datetime.datetime.today().strftime("%x %X") captured before each prompt,
prompt_continuation=a callable (width, line_number, is_soft_wrap) returning
[("class:continuation", real.pgcli.repl.continuation_prompt(width,
multiline_continuation_char))], bottom_toolbar=a callable returning
real.pgcli.repl.toolbar_fragments(...) as (style, text) tuples when
show_bottom_toolbar else None, complete_style MULTI_COLUMN when
wider_completion_menu else COLUMN, input_processors=[ConditionalProcessor(
HighlightMatchingBracketProcessor(chars="[](){}"), HasFocus(DEFAULT_BUFFER)
& ~IsDone()), TabsProcessor(char1=" ", char2=" ")],
auto_suggest=AutoSuggestFromHistory() when auto_suggest else None,
tempfile_suffix=".sql", multiline=True, history, the completer,
complete_while_typing=True, style=the style described below,
include_default_pygments_style=False, key_bindings=the bindings below,
enable_open_in_editor=True, enable_system_prompt=True, enable_suspend=True,
editing_mode VI when vi_mode else EMACS, search_ignore_case=True,
cursor=ModalCursorShapeConfig() in vi mode else None).
Style: pygments.styles.get_style_by_name(syntax_style) (falling back to
"native" on ClassNotFound) through style_from_pygments_cls, merged with
Style([("bottom-toolbar", "noreverse")]) and Style(list of the [colors]
entries, where entries whose name starts with "Token." are mapped to the
prompt_toolkit class names completion-menu.completion.current,
completion-menu.completion, completion-menu.meta.completion.current,
completion-menu.meta.completion, completion-menu.multi-column-meta,
scrollbar.arrow, scrollbar, selected, search, search.current,
bottom-toolbar, bottom-toolbar.off, bottom-toolbar.on, search-toolbar,
search-toolbar.text, system-toolbar, arg-toolbar, arg-toolbar.text,
bottom-toolbar.transaction.valid, bottom-toolbar.transaction.failed,
literal.string, literal.number, keyword for Token.Menu.Completions.
Completion, ...Completion.Current, ...Meta, ...Meta.Current,
...MultiColumnMeta, Token.Menu.Completions.ProgressButton,
...ProgressBar, Token.SelectedText, Token.SearchMatch,
Token.SearchMatch.Current, Token.Toolbar, Token.Toolbar.Off,
Token.Toolbar.On, Token.Toolbar.Search, Token.Toolbar.Search.Text,
Token.Toolbar.System, Token.Toolbar.Arg, Token.Toolbar.Arg.Text,
Token.Toolbar.Transaction.Valid, Token.Toolbar.Transaction.Failed,
Token.Literal.String, Token.Literal.Number, Token.Keyword; other Token.
names are ignored).

Key bindings (prompt_toolkit KeyBindings; each handler is a lambda calling
a private top-level function with the cells): F2 toggles smart completion; F3
toggles multi_line; F4 toggles vi_mode and sets
event.app.editing_mode; F5 toggles explain_mode; Tab: when the cursor is on
the first line or the current line is not blank, complete_next() when a
completion menu is open else start_completion(select_first=True);
otherwise insert four spaces. Escape (only while completions exist) closes
the menu (complete_state = None); Ctrl-Space: complete_next() when open
else start_completion(select_first=False); Enter while a completion is
selected closes the menu without submitting; Enter when neither a completion
is selected nor searching and real.pgcli.repl.buffer_should_submit(buffer
text, multi_line, multiline_mode) holds: validate_and_handle(); Escape
Enter (Alt-Enter), except in vi mode or safe multi-line mode, inserts a
line feed; Ctrl-P / Ctrl-N (no selection) move backward / forward in
history by event.arg.

Intro unless less_chatty: print "Server: PostgreSQL <server_version>",
"Version: 4.7.1" and "Home: https://pgcli.com".
Loop: text = prompt_session.prompt(); KeyboardInterrupt continues;
EOFError asks real.pgcli.session.confirm_quit_with_transaction and ends the
loop when it allows quitting. Editor commands: while
pgspecial.iocommands.editor_command(text) is set: for "\\e" the file is
pgspecial.iocommands.get_filename(text) and the query
get_editor_query(text) or session.last_query; for "\\ev"/"\\ef" the query is
real.pgcli.session.view_definition_sql / real.pgcli.session.function_definition_sql of the
second word; open pgspecial.iocommands.open_external_editor(filename,
sql=query, editor=$PSQL_EDITOR or $EDITOR or $VISUAL or None); a returned
message (or a definition error) is printed in red on standard error and the
input is dropped; otherwise re-prompt with prompt(default=sql) (Ctrl-C
re-prompts with an empty default) and repeat the check on the new text.
Then real.pgcli.session.watch_pgcli_command(session, text, current
terminal size from prompt_session.output.get_size()). A quit outcome asks
real.pgcli.session.confirm_quit_with_transaction and ends the loop when
allowed. Apply the outcome's refresh (Reset, All or SearchPath as above)
and learn from the text with real.pgcli.completion.update_prevalence(
prevalence, text, false). After the loop print "Goodbye!" unless
less_chatty. Returns the final session."""
    session = _cott_validate_abi(session, Session, path="$.session")
    settings = _cott_validate_abi(settings, ReplSettings, path="$.settings")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/repl/run_pgcli_repl.py", "0f1cc3d68f708524cf7194a3d340a88f446f75fc88f085b717525a500f214425", "run_pgcli_repl", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.repl.run_pgcli_repl")
        _result = _implementation(session, settings)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.repl.run_pgcli_repl"
        if _error.span is None:
            _error.span = {"end_byte":13952,"end_column":1,"end_line":275,"start_byte":5347,"start_column":1,"start_line":144}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.repl.run_pgcli_repl", phase="implementation-call", span={"end_byte":13952,"end_column":1,"end_line":275,"start_byte":5347,"start_column":1,"start_line":144}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.repl.run_pgcli_repl", phase="implementation-call", span={"end_byte":13952,"end_column":1,"end_line":275,"start_byte":5347,"start_column":1,"start_line":144}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Session, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Session, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["PromptInfo", "ReplSettings", "StyledText", "ToolbarState", "buffer_should_submit", "continuation_prompt", "prompt_message_text", "render_prompt", "run_pgcli_repl", "toolbar_fragments"]
