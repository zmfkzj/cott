import dataclasses
import datetime
import itertools
import os
import threading
import types
from collections.abc import Callable, Iterable
from typing import Any, cast

import click
import pgspecial.iocommands
import pygments.lexers.sql
import pygments.styles
import pygments.util
from cott_runtime import CottList, FrozenMap, Nothing, Ok, Some, U64
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import CompleteEvent, Completer, Completion, PathCompleter, ThreadedCompleter
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import Condition, HasFocus, IsDone, has_completions, has_selection
from prompt_toolkit.formatted_text import ANSI, StyleAndTextTuples
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout.processors import ConditionalProcessor, HighlightMatchingBracketProcessor, TabsProcessor
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import BaseStyle, Style, merge_styles, style_from_pygments_cls
from pygments.style import Style as PygmentsStyle

from real.pgcli.completion import catalog_with_search_path, clear_prevalence_names, complete_sql_text, empty_completion_catalog, prevalence_from, refresh_completion_metadata, update_prevalence
from real.pgcli.completion_types import CompletionCatalog, CompletionRequest, PrevalenceHandle, SpecialCommandInfo
from real.pgcli.connection import close_executor, copy_executor, executor_transaction_status, read_search_path, short_host_name, transaction_indicator
from real.pgcli.connection_types import TransactionStatus_Active, TransactionStatus_InError, TransactionStatus_InTransaction
from real.pgcli.output import table_format_names
from real.pgcli.repl import buffer_should_submit, continuation_prompt, prompt_message_text, toolbar_fragments
from real.pgcli.repl_types import PromptInfo, ReplSettings, ToolbarState
from real.pgcli.session import confirm_quit_with_transaction, function_definition_sql, named_query_names, special_command_catalog, view_definition_sql, watch_pgcli_command
from real.pgcli.session_types import EvaluateError_Failed, RefreshKind_All, RefreshKind_Reset, RefreshKind_SearchPath, Session, TerminalSize


def _style(settings: ReplSettings) -> BaseStyle:
    try:
        syntax = cast(type[PygmentsStyle], pygments.styles.get_style_by_name(settings.syntax_style))
    except pygments.util.ClassNotFound:
        syntax = cast(type[PygmentsStyle], pygments.styles.get_style_by_name("native"))
    mapping = {
        "Token.Menu.Completions.Completion.Current": "completion-menu.completion.current",
        "Token.Menu.Completions.Completion": "completion-menu.completion",
        "Token.Menu.Completions.Meta.Current": "completion-menu.meta.completion.current",
        "Token.Menu.Completions.Meta": "completion-menu.meta.completion",
        "Token.Menu.Completions.MultiColumnMeta": "completion-menu.multi-column-meta",
        "Token.Menu.Completions.ProgressButton": "scrollbar.arrow",
        "Token.Menu.Completions.ProgressBar": "scrollbar",
        "Token.SelectedText": "selected",
        "Token.SearchMatch": "search",
        "Token.SearchMatch.Current": "search.current",
        "Token.Toolbar": "bottom-toolbar",
        "Token.Toolbar.Off": "bottom-toolbar.off",
        "Token.Toolbar.On": "bottom-toolbar.on",
        "Token.Toolbar.Search": "search-toolbar",
        "Token.Toolbar.Search.Text": "search-toolbar.text",
        "Token.Toolbar.System": "system-toolbar",
        "Token.Toolbar.Arg": "arg-toolbar",
        "Token.Toolbar.Arg.Text": "arg-toolbar.text",
        "Token.Toolbar.Transaction.Valid": "bottom-toolbar.transaction.valid",
        "Token.Toolbar.Transaction.Failed": "bottom-toolbar.transaction.failed",
        "Token.Literal.String": "literal.string",
        "Token.Literal.Number": "literal.number",
        "Token.Keyword": "keyword",
    }
    entries: list[tuple[str, str]] = []
    for entry in settings.colors:
        if entry.name in mapping:
            entries.append((mapping[entry.name], entry.value))
    return merge_styles([style_from_pygments_cls(syntax), Style([("bottom-toolbar", "noreverse")]), Style(entries)])


def _store(cells: list[list[object]], session: Session) -> None:
    cells[0][0] = dataclasses.replace(
        session,
        catalog=cast(CompletionCatalog, cells[1][0]),
        settings=dataclasses.replace(session.settings, completion_refreshing=cast(bool, cells[3][0]) and not session.executor.virtual_database),
    )


def _invalidate(cells: list[list[object]]) -> None:
    app: Any = cells[7][0]
    if app is not None:
        app.invalidate()


def _refresh_worker(cells: list[list[object]], settings: ReplSettings) -> None:
    lock = cast(threading.Lock, cells[5][0])
    while True:
        with lock:
            cells[4][0] = False
            base = cast(Session, cells[0][0]).executor
        try:
            if not base.virtual_database:
                if settings.single_connection:
                    executor = base
                else:
                    copied = copy_executor(base)
                    executor = copied.value if isinstance(copied, Ok) else None
                if executor is not None:
                    try:
                        with lock:
                            active = cast(Session, cells[0][0]).executor is base and not cells[4][0]
                        if active:
                            result = refresh_completion_metadata(executor, settings.refresh)
                            if isinstance(result, Ok):
                                recent = list(itertools.islice(cast(FileHistory, cells[6][0]).load_history_strings(), 100))
                                with lock:
                                    if cast(Session, cells[0][0]).executor is base and not cells[4][0]:
                                        prevalence = cast(PrevalenceHandle, cells[2][0])
                                        for text in recent:
                                            prevalence = update_prevalence(prevalence, text, True)
                                        cells[2][0] = prevalence
                                        cells[1][0] = result.value
                                        _store(cells, cast(Session, cells[0][0]))
                                _invalidate(cells)
                    finally:
                        if not settings.single_connection:
                            close_executor(executor)
        except Exception as error:
            click.secho(str(error), err=True, fg="red")
        with lock:
            if cells[4][0]:
                continue
            cells[3][0] = False
            _store(cells, cast(Session, cells[0][0]))
            break
    _invalidate(cells)


def _start_refresh(cells: list[list[object]], settings: ReplSettings, reset: bool) -> None:
    lock = cast(threading.Lock, cells[5][0])
    with lock:
        if reset:
            cells[2][0] = clear_prevalence_names(cast(PrevalenceHandle, cells[2][0]))
            cells[1][0] = empty_completion_catalog()
        if cast(Session, cells[0][0]).executor.virtual_database:
            cells[4][0] = False
            _store(cells, cast(Session, cells[0][0]))
            return
        cells[4][0] = True
        if cells[3][0]:
            if reset:
                _store(cells, cast(Session, cells[0][0]))
            return
        cells[3][0] = True
        _store(cells, cast(Session, cells[0][0]))
    threading.Thread(target=lambda: _refresh_worker(cells, settings), name="completion_refresh", daemon=True).start()


def _complete(cells: list[list[object]], settings: ReplSettings, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
    if document.text.startswith("\\i "):
        path_document = Document(document.text[3:], max(0, document.cursor_position - 3))
        yield from PathCompleter(expanduser=True).get_completions(path_document, complete_event)
        return
    lock = cast(threading.Lock, cells[5][0])
    with lock:
        session = cast(Session, cells[0][0])
        catalog = cast(CompletionCatalog, cells[1][0])
        prevalence = cast(PrevalenceHandle, cells[2][0])
    request = CompletionRequest(
        text=document.text,
        cursor=document.cursor_position,
        smart_completion=session.settings.smart_completion,
        catalog=catalog,
        settings=settings.completer,
        prevalence=prevalence,
        special_commands=CottList(values=[
            SpecialCommandInfo(command=item.command, syntax=item.syntax, description=item.description)
            for item in special_command_catalog(session.special)
        ]),
        named_queries=named_query_names(session.special),
        table_formats=table_format_names(),
    )
    yield from cast(list[Completion], complete_sql_text(request).unwrap())


def _message(cells: list[list[object]]) -> ANSI:
    session = cast(Session, cells[0][0])
    executor = session.executor
    alias = session.settings.dsn_alias
    info = PromptInfo(
        dsn_alias=alias.value if isinstance(alias, Some) else "",
        now_text=cast(str, cells[8][0]),
        user=executor.user,
        host=executor.host,
        short_host=short_host_name(executor.host),
        dbname=executor.dbname,
        port=Some(value=executor.port) if executor.port else Nothing(),
        pid=executor.pid,
        superuser=executor.superuser,
        transaction_indicator=transaction_indicator(executor_transaction_status(executor)),
    )
    return ANSI(prompt_message_text(session.settings.prompt_format, session.settings.prompt_dsn_format, info))


def _toolbar(cells: list[list[object]]) -> StyleAndTextTuples:
    session = cast(Session, cells[0][0])
    current = session.settings
    status = executor_transaction_status(session.executor)
    app: Any = cells[7][0]
    mode = app.vi_state.input_mode if app is not None else InputMode.INSERT
    letter = "N" if mode == InputMode.NAVIGATION else "R" if mode in (InputMode.REPLACE, InputMode.REPLACE_SINGLE) else "M" if mode == InputMode.INSERT_MULTIPLE else "I"
    state = ToolbarState(
        smart_completion=current.smart_completion,
        multi_line=current.multi_line,
        multiline_mode=current.multiline_mode,
        vi_mode=current.vi_mode,
        vi_input_mode=letter,
        explain_mode=current.explain_mode,
        failed_transaction=isinstance(status, TransactionStatus_InError),
        valid_transaction=isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction)),
        refreshing=current.completion_refreshing,
    )
    return [(part.style, part.text) for part in toolbar_fragments(state)]


def _toggle(cells: list[list[object]], field: str, event: KeyPressEvent) -> None:
    lock = cast(threading.Lock, cells[5][0])
    with lock:
        session = cast(Session, cells[0][0])
        if field == "smart_completion":
            updated = dataclasses.replace(session.settings, smart_completion=not session.settings.smart_completion)
        elif field == "multi_line":
            updated = dataclasses.replace(session.settings, multi_line=not session.settings.multi_line)
        elif field == "vi_mode":
            updated = dataclasses.replace(session.settings, vi_mode=not session.settings.vi_mode)
        else:
            updated = dataclasses.replace(session.settings, explain_mode=not session.settings.explain_mode)
        cells[0][0] = dataclasses.replace(session, settings=updated)
        vi_mode = updated.vi_mode
    if field == "vi_mode":
        event.app.editing_mode = EditingMode.VI if vi_mode else EditingMode.EMACS


def _tab(event: KeyPressEvent) -> None:
    buffer = event.app.current_buffer
    if buffer.document.on_first_line or buffer.document.current_line.strip():
        if buffer.complete_state:
            buffer.complete_next()
        else:
            buffer.start_completion(select_first=True)
    else:
        buffer.insert_text("    ")


def _space(event: KeyPressEvent) -> None:
    buffer = event.app.current_buffer
    if buffer.complete_state:
        buffer.complete_next()
    else:
        buffer.start_completion(select_first=False)


def _dismiss_completion(event: KeyPressEvent) -> None:
    event.current_buffer.complete_state = None


def _selected() -> bool:
    state = get_app().current_buffer.complete_state
    return state is not None and state.current_completion is not None


def _submit(cells: list[list[object]]) -> bool:
    app = get_app()
    if _selected() or app.layout.is_searching:
        return False
    current = cast(Session, cells[0][0]).settings
    return buffer_should_submit(app.current_buffer.text, current.multi_line, current.multiline_mode)


def _alt_allowed(cells: list[list[object]]) -> bool:
    current = cast(Session, cells[0][0]).settings
    return not current.vi_mode and not (current.multi_line and current.multiline_mode == "safe")


def _editor(cells: list[list[object]], prompt: PromptSession[str], text: str) -> str | None:
    io: Any = pgspecial.iocommands
    while True:
        command = cast(object, io.editor_command(text))
        if not command:
            return text
        if not isinstance(command, str):
            raise TypeError("editor command is not text")
        filename: str | None = None
        if command in ("\\ev", "\\ef"):
            words = text.split()
            spec = words[1] if len(words) > 1 else ""
            executor = cast(Session, cells[0][0]).executor
            definition = view_definition_sql(executor, spec) if command == "\\ev" else function_definition_sql(executor, spec)
            if not isinstance(definition, Ok):
                error = definition.error
                click.secho(error.message if isinstance(error, EvaluateError_Failed) else str(error), err=True, fg="red")
                return None
            query = definition.value
        else:
            raw_filename = cast(object, io.get_filename(text))
            filename = str(raw_filename) if raw_filename is not None else None
            raw_query = cast(object, io.get_editor_query(text))
            query = str(raw_query) if raw_query else cast(Session, cells[0][0]).last_query
        opened = cast(object, io.open_external_editor(filename, sql=query, editor=os.environ.get("PSQL_EDITOR") or os.environ.get("EDITOR") or os.environ.get("VISUAL") or None))
        if not isinstance(opened, tuple) or len(cast(tuple[object, ...], opened)) != 2:
            raise TypeError("editor did not return a query and message")
        result = cast(tuple[object, object], opened)
        sql = str(result[0]) if result[0] is not None else ""
        if result[1]:
            click.secho(str(result[1]), err=True, fg="red")
            return None
        while True:
            cells[8][0] = datetime.datetime.today().strftime("%x %X")
            try:
                text = prompt.prompt(default=sql)
                break
            except KeyboardInterrupt:
                sql = ""


def _screen(prompt: PromptSession[str]) -> TerminalSize:
    size = prompt.output.get_size()
    return TerminalSize(columns=size.columns, rows=size.rows)


def _validate(event: KeyPressEvent) -> None:
    event.current_buffer.validate_and_handle()


def _newline(event: KeyPressEvent) -> None:
    event.current_buffer.insert_text("\n")


def _history_back(event: KeyPressEvent) -> None:
    event.current_buffer.history_backward(count=event.arg)


def _history_forward(event: KeyPressEvent) -> None:
    event.current_buffer.history_forward(count=event.arg)


def _bindings(cells: list[list[object]]) -> KeyBindings:
    kb = KeyBindings()
    f2: Callable[[KeyPressEvent], None] = lambda event: _toggle(cells, "smart_completion", event)
    f3: Callable[[KeyPressEvent], None] = lambda event: _toggle(cells, "multi_line", event)
    f4: Callable[[KeyPressEvent], None] = lambda event: _toggle(cells, "vi_mode", event)
    f5: Callable[[KeyPressEvent], None] = lambda event: _toggle(cells, "explain_mode", event)
    tab: Callable[[KeyPressEvent], None] = lambda event: _tab(event)
    dismiss: Callable[[KeyPressEvent], None] = lambda event: _dismiss_completion(event)
    space: Callable[[KeyPressEvent], None] = lambda event: _space(event)
    submit: Callable[[KeyPressEvent], None] = lambda event: _validate(event)
    newline: Callable[[KeyPressEvent], None] = lambda event: _newline(event)
    back: Callable[[KeyPressEvent], None] = lambda event: _history_back(event)
    forward: Callable[[KeyPressEvent], None] = lambda event: _history_forward(event)
    kb.add("f2")(f2)
    kb.add("f3")(f3)
    kb.add("f4")(f4)
    kb.add("f5")(f5)
    kb.add("tab")(tab)
    kb.add("escape", filter=has_completions)(dismiss)
    kb.add("c-space")(space)
    kb.add("enter", filter=Condition(lambda: _selected()))(dismiss)
    kb.add("enter", filter=HasFocus(DEFAULT_BUFFER) & Condition(lambda: _submit(cells)))(submit)
    kb.add("escape", "enter", filter=Condition(lambda: _alt_allowed(cells)))(newline)
    kb.add("c-p", filter=~has_selection)(back)
    kb.add("c-n", filter=~has_selection)(forward)
    return kb


def run_pgcli_repl(session: Session, settings: ReplSettings) -> Session:
    history = FileHistory(settings.history_file)
    # Session, catalog, prevalence, refreshing, restart, lock, history, application, prompt time.
    cells: list[list[object]] = [
        [session],
        [session.catalog],
        [prevalence_from(FrozenMap[str, U64](values={}), FrozenMap[str, U64](values={}))],
        [False],
        [False],
        [threading.Lock()],
        [history],
        [None],
        [""],
    ]
    _start_refresh(cells, settings, False)
    complete_callback: Callable[[Document, CompleteEvent], Iterable[Completion]] = lambda document, event: _complete(cells, settings, document, event)
    completer = ThreadedCompleter(cast(Completer, types.SimpleNamespace(get_completions=complete_callback)))
    prompt: PromptSession[str] = PromptSession(
        message=lambda: _message(cells),
        lexer=PygmentsLexer(pygments.lexers.sql.PostgresLexer),
        reserve_space_for_menu=settings.min_num_menu_lines,
        prompt_continuation=lambda width, line_number, is_soft_wrap: [("class:continuation", continuation_prompt(width, settings.multiline_continuation_char))],
        bottom_toolbar=(lambda: _toolbar(cells)) if settings.show_bottom_toolbar else None,
        complete_style=CompleteStyle.MULTI_COLUMN if settings.wider_completion_menu else CompleteStyle.COLUMN,
        input_processors=[ConditionalProcessor(HighlightMatchingBracketProcessor(chars="[](){}"), HasFocus(DEFAULT_BUFFER) & ~IsDone()), TabsProcessor(char1=" ", char2=" ")],
        auto_suggest=AutoSuggestFromHistory() if settings.auto_suggest else None,
        tempfile_suffix=".sql",
        multiline=True,
        history=history,
        completer=completer,
        complete_while_typing=True,
        style=_style(settings),
        include_default_pygments_style=False,
        key_bindings=_bindings(cells),
        enable_open_in_editor=True,
        enable_system_prompt=True,
        enable_suspend=True,
        editing_mode=EditingMode.VI if session.settings.vi_mode else EditingMode.EMACS,
        search_ignore_case=True,
        cursor=ModalCursorShapeConfig() if session.settings.vi_mode else None,
    )
    cells[7][0] = prompt.app
    if not session.settings.less_chatty:
        click.echo("Server: PostgreSQL " + session.executor.server_version)
        click.echo("Version: 4.7.1")
        click.echo("Home: https://pgcli.com")
    lock = cast(threading.Lock, cells[5][0])
    while True:
        cells[8][0] = datetime.datetime.today().strftime("%x %X")
        try:
            text = prompt.prompt()
        except KeyboardInterrupt:
            continue
        except EOFError:
            decision = confirm_quit_with_transaction(cast(Session, cells[0][0]), _screen(prompt))
            with lock:
                _store(cells, decision.session)
            if decision.quit:
                break
            continue
        edited = _editor(cells, prompt, text)
        if edited is None:
            continue
        text = edited
        with lock:
            current = cast(Session, cells[0][0])
        screen = _screen(prompt)
        outcome = watch_pgcli_command(current, text, screen)
        with lock:
            _store(cells, outcome.session)
        if outcome.quit:
            decision = confirm_quit_with_transaction(cast(Session, cells[0][0]), screen)
            with lock:
                _store(cells, decision.session)
            if decision.quit:
                break
        if isinstance(outcome.refresh, RefreshKind_Reset):
            _start_refresh(cells, settings, True)
        elif isinstance(outcome.refresh, RefreshKind_All):
            _start_refresh(cells, settings, False)
        elif isinstance(outcome.refresh, RefreshKind_SearchPath):
            path = read_search_path(cast(Session, cells[0][0]).executor)
            if isinstance(path, Ok):
                with lock:
                    cells[1][0] = catalog_with_search_path(cast(CompletionCatalog, cells[1][0]), path.value)
                    _store(cells, cast(Session, cells[0][0]))
        with lock:
            cells[2][0] = update_prevalence(cast(PrevalenceHandle, cells[2][0]), text, False)
    final = cast(Session, cells[0][0])
    if not final.settings.less_chatty:
        click.echo("Goodbye!")
    return final
