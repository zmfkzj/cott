from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.repl_types import PromptInfo as PromptInfo, ReplSettings as ReplSettings, StyledText as StyledText, ToolbarState as ToolbarState
from real.pgcli.completion_types import CompleterSettings, MetadataRefreshRequest
from real.pgcli.config_types import ConfigEntry
from real.pgcli.session_types import Session
"""PGCli.get_prompt on template: replace, in this order and each everywhere: "\\dsn_alias"
with info.dsn_alias, "\\t" with now_text, "\\u" with user or "(none)", "\\H"
with host or "(none)", "\\h" with short_host or "(none)", "\\d" with dbname or
"(none)", "\\p" with the port or "5432" when Nothing, "\\i" with str(pid),
"\\#" with "#" for a superuser else ">", "\\n" with a line feed and "\\T" with
transaction_indicator. Every "\\x" sequence here is a literal backslash
followed by the letters."""
def render_prompt(template: str, info: PromptInfo) -> str: ...

"""The get_message callable of PGCli._build_cli: the format is
prompt_dsn_format when info.dsn_alias is nonempty and prompt_dsn_format is
Some, otherwise prompt_format. text = real.pgcli.repl.render_prompt(template,
info). When the format equals the default "\\u@\\h:\\d> " and text is longer
than 30 code points, text = render_prompt("\\d> ", info). Finally every
literal four-character "\\x1b" becomes the ESC character (U+001B), so the
caller can wrap the result in prompt_toolkit ANSI(...)."""
def prompt_message_text(prompt_format: str, prompt_dsn_format: Option[str], info: PromptInfo) -> str: ...

"""get_continuation: continuation_char repeated width - 1 times (no repetition
when width < 2) followed by one space. width is a terminal cell count
(at most 10,000 cells); the caller shows it with style "class:continuation"."""
def continuation_prompt(width: I64, continuation_char: str) -> str: ...

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
def toolbar_fragments(toolbar: ToolbarState) -> CottList[StyledText]: ...

"""pgbuffer.buffer_should_be_handled for the current buffer text: true when
multi_line is false; false when multiline_mode is "safe"; otherwise, with t
= text.strip(), true when t starts with "\\", ends with "\\e" or "\\G", is
complete, equals "exit", "quit" or ":q", or is "". t is complete when
sqlparse.format(t, strip_comments=True).strip() ends with ";" and
real.pgcli.parseutils.is_open_quote(t) is false."""
def buffer_should_submit(text: str, multi_line: bool, multiline_mode: str) -> bool: ...

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
def run_pgcli_repl(session: Session, settings: ReplSettings) -> Session: ...

__all__ = ["PromptInfo", "ReplSettings", "StyledText", "ToolbarState", "buffer_should_submit", "continuation_prompt", "prompt_message_text", "render_prompt", "run_pgcli_repl", "toolbar_fragments"]
