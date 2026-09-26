import dataclasses
import datetime
import os
import threading
import types
from collections.abc import Callable, Iterable
from typing import Any, Final, cast

import click
import pgspecial.iocommands
import pygments.lexers.sql
import pygments.styles
import pygments.util
from cott_runtime import CottList, FrozenMap, Nothing, Ok, Some
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import CompleteEvent, Completer, Completion, PathCompleter, ThreadedCompleter
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import Condition, HasFocus, IsDone, has_completions, has_selection
from prompt_toolkit.formatted_text import ANSI, AnyFormattedText, StyleAndTextTuples
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout.processors import ConditionalProcessor, HighlightMatchingBracketProcessor, TabsProcessor
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import BaseStyle, Style, merge_styles, style_from_pygments_cls
from pygments.style import Style as PygmentsStyle

from real.pgcli.completion import catalog_with_search_path, clear_prevalence_names, complete_sql_text, prevalence_from, refresh_completion_metadata, update_prevalence
from real.pgcli.completion_types import CompletionCatalog, CompletionRequest, PrevalenceHandle, SpecialCommandInfo
from real.pgcli.connection import close_executor, copy_executor, executor_transaction_status, read_search_path, short_host_name, transaction_indicator
from real.pgcli.connection_types import Executor, TransactionStatus_Active, TransactionStatus_InError, TransactionStatus_InTransaction
from real.pgcli.output import table_format_names
from real.pgcli.repl import buffer_should_submit, continuation_prompt, prompt_message_text, toolbar_fragments
from real.pgcli.repl_types import PromptInfo, ReplSettings, ToolbarState
from real.pgcli.session import confirm_quit_with_transaction, function_definition_sql, named_query_names, special_command_catalog, view_definition_sql, watch_pgcli_command
from real.pgcli.session_types import EvaluateError_Failed, RefreshKind_All, RefreshKind_Reset, RefreshKind_SearchPath, Session, TerminalSize

_VERSION: Final[str] = "4.7.1"
_SESSION: Final[int] = 0
_CATALOG: Final[int] = 1
_PREVALENCE: Final[int] = 2
_REFRESHING: Final[int] = 3
_PENDING: Final[int] = 4
_LOCK: Final[int] = 5
_HISTORY: Final[int] = 6
_APP: Final[int] = 7
_NOW: Final[int] = 8


def _token_class(name: str) -> str | None:
    mapping: dict[str, str] = {
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
    return mapping.get(name)


def _build_style(settings: ReplSettings) -> BaseStyle:
    try:
        pyg = cast(type[PygmentsStyle], pygments.styles.get_style_by_name(settings.syntax_style))
    except pygments.util.ClassNotFound:
        pyg = cast(type[PygmentsStyle], pygments.styles.get_style_by_name("native"))
    entries: list[tuple[str, str]] = []
    for entry in settings.colors:
        if entry.name.startswith("Token."):
            cls = _token_class(entry.name)
            if cls is not None:
                entries.append((cls, entry.value))
        else:
            entries.append((entry.name, entry.value))
    return merge_styles([style_from_pygments_cls(pyg), Style([("bottom-toolbar", "noreverse")]), Style(entries)])


def _get(cells: list[list[object]], index: int) -> object:
    return cells[index][0]


def _put(cells: list[list[object]], index: int, value: object) -> None:
    cells[index][0] = value


def _lock(cells: list[list[object]]) -> threading.Lock:
    return cast(threading.Lock, _get(cells, _LOCK))


def _session(cells: list[list[object]]) -> Session:
    return cast(Session, _get(cells, _SESSION))


def _catalog(cells: list[list[object]]) -> CompletionCatalog:
    return cast(CompletionCatalog, _get(cells, _CATALOG))


def _prevalence(cells: list[list[object]]) -> PrevalenceHandle:
    return cast(PrevalenceHandle, _get(cells, _PREVALENCE))


def _store_session(cells: list[list[object]], session: Session) -> None:
    _put(cells, _SESSION, dataclasses.replace(session, catalog=_catalog(cells)))


def _set_mode(cells: list[list[object]], name: str, value: bool) -> None:
    with _lock(cells):
        session = _session(cells)
        if name == "smart_completion":
            settings = dataclasses.replace(session.settings, smart_completion=value)
        elif name == "multi_line":
            settings = dataclasses.replace(session.settings, multi_line=value)
        elif name == "vi_mode":
            settings = dataclasses.replace(session.settings, vi_mode=value)
        else:
            settings = dataclasses.replace(session.settings, explain_mode=value)
        _put(cells, _SESSION, dataclasses.replace(session, settings=settings))


def _empty_prevalence() -> PrevalenceHandle:
    return prevalence_from(FrozenMap(values={}), FrozenMap(values={}))


def _invalidate(cells: list[list[object]]) -> None:
    app = cast(Any, _get(cells, _APP))
    if app is not None:
        app.invalidate()


def _refresh_once(cells: list[list[object]], settings: ReplSettings) -> None:
    base: Executor = _session(cells).executor
    if base.virtual_database:
        return
    if settings.single_connection:
        executor = base
    else:
        copied = copy_executor(base)
        if not isinstance(copied, Ok):
            return
        executor = copied.value
    try:
        result = refresh_completion_metadata(executor, settings.refresh)
    finally:
        if not settings.single_connection:
            close_executor(executor)
    if not isinstance(result, Ok):
        return
    with _lock(cells):
        prevalence = _prevalence(cells)
        history = cast(FileHistory, _get(cells, _HISTORY))
        for text in list(history.get_strings())[-100:]:
            prevalence = update_prevalence(prevalence, text, True)
        _put(cells, _PREVALENCE, prevalence)
        _put(cells, _CATALOG, result.value)
        _store_session(cells, _session(cells))
    _invalidate(cells)


def _refresh_worker(cells: list[list[object]], settings: ReplSettings) -> None:
    lock = _lock(cells)
    while True:
        with lock:
            _put(cells, _PENDING, False)
        try:
            _refresh_once(cells, settings)
        except Exception as error:
            click.secho(str(error), err=True, fg="red")
        with lock:
            if not _get(cells, _PENDING):
                _put(cells, _REFRESHING, False)
                break
    _invalidate(cells)


def _start_refresh(cells: list[list[object]], settings: ReplSettings, reset: bool) -> None:
    if _session(cells).executor.virtual_database:
        return
    with _lock(cells):
        if reset:
            _put(cells, _PREVALENCE, clear_prevalence_names(_prevalence(cells)))
        _put(cells, _PENDING, True)
        if _get(cells, _REFRESHING):
            return
        _put(cells, _REFRESHING, True)
    worker: Callable[[], None] = lambda: _refresh_worker(cells, settings)
    thread = threading.Thread(target=worker, name="completion_refresh", daemon=True)
    thread.start()


def _complete(cells: list[list[object]], settings: ReplSettings, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
    if document.text.startswith("\\i "):
        yield from PathCompleter(expanduser=True).get_completions(Document(document.text_before_cursor[3:]), complete_event)
        return
    session = _session(cells)
    commands = CottList(values=[SpecialCommandInfo(command=e.command, syntax=e.syntax, description=e.description) for e in special_command_catalog(session.special)])
    request = CompletionRequest(
        text=document.text,
        cursor=document.cursor_position,
        smart_completion=session.settings.smart_completion,
        catalog=_catalog(cells),
        settings=settings.completer,
        prevalence=_prevalence(cells),
        special_commands=commands,
        named_queries=named_query_names(session.special),
        table_formats=table_format_names(),
    )
    yield from cast(list[Completion], complete_sql_text(request).unwrap())


def _prompt_info(cells: list[list[object]]) -> PromptInfo:
    session = _session(cells)
    executor = session.executor
    alias = session.settings.dsn_alias
    return PromptInfo(
        dsn_alias=alias.value if isinstance(alias, Some) else "",
        now_text=str(_get(cells, _NOW)),
        user=executor.user,
        host=executor.host,
        short_host=short_host_name(executor.host),
        dbname=executor.dbname,
        port=Some(value=executor.port) if executor.port else Nothing(),
        pid=executor.pid,
        superuser=executor.superuser,
        transaction_indicator=transaction_indicator(executor_transaction_status(executor)),
    )


def _message(cells: list[list[object]]) -> ANSI:
    settings = _session(cells).settings
    return ANSI(prompt_message_text(settings.prompt_format, settings.prompt_dsn_format, _prompt_info(cells)))


def _continuation(char: str, width: int) -> StyleAndTextTuples:
    return [("class:continuation", continuation_prompt(width, char))]


def _vi_letter(cells: list[list[object]]) -> str:
    app = cast(Any, _get(cells, _APP))
    if app is None:
        return "I"
    mode = app.vi_state.input_mode
    if mode == InputMode.NAVIGATION:
        return "N"
    if mode in (InputMode.REPLACE, InputMode.REPLACE_SINGLE):
        return "R"
    if mode == InputMode.INSERT_MULTIPLE:
        return "M"
    return "I"


def _toolbar(cells: list[list[object]]) -> StyleAndTextTuples:
    session = _session(cells)
    settings = session.settings
    status = executor_transaction_status(session.executor)
    state = ToolbarState(
        smart_completion=settings.smart_completion,
        multi_line=settings.multi_line,
        multiline_mode=settings.multiline_mode,
        vi_mode=settings.vi_mode,
        vi_input_mode=_vi_letter(cells),
        explain_mode=settings.explain_mode,
        failed_transaction=isinstance(status, TransactionStatus_InError),
        valid_transaction=isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction)),
        refreshing=bool(_get(cells, _REFRESHING)),
    )
    out: StyleAndTextTuples = []
    for fragment in toolbar_fragments(state):
        out.append((fragment.style, fragment.text))
    return out


def _on_f2(cells: list[list[object]]) -> None:
    _set_mode(cells, "smart_completion", not _session(cells).settings.smart_completion)


def _on_f3(cells: list[list[object]]) -> None:
    _set_mode(cells, "multi_line", not _session(cells).settings.multi_line)


def _on_f4(cells: list[list[object]], event: KeyPressEvent) -> None:
    vi = not _session(cells).settings.vi_mode
    _set_mode(cells, "vi_mode", vi)
    event.app.editing_mode = EditingMode.VI if vi else EditingMode.EMACS


def _on_f5(cells: list[list[object]]) -> None:
    _set_mode(cells, "explain_mode", not _session(cells).settings.explain_mode)


def _on_tab(event: KeyPressEvent) -> None:
    buffer = event.app.current_buffer
    document = buffer.document
    if document.on_first_line or document.current_line.strip():
        if buffer.complete_state:
            buffer.complete_next()
        else:
            buffer.start_completion(select_first=True)
    else:
        buffer.insert_text("    ")


def _on_escape(event: KeyPressEvent) -> None:
    event.current_buffer.complete_state = None


def _on_ctrl_space(event: KeyPressEvent) -> None:
    buffer = event.app.current_buffer
    if buffer.complete_state:
        buffer.complete_next()
    else:
        buffer.start_completion(select_first=False)


def _completion_selected() -> bool:
    state = get_app().current_buffer.complete_state
    return state is not None and state.current_completion is not None


def _should_submit(cells: list[list[object]]) -> bool:
    app = get_app()
    if _completion_selected() or app.layout.is_searching:
        return False
    settings = _session(cells).settings
    return buffer_should_submit(app.current_buffer.text, settings.multi_line, settings.multiline_mode)


def _on_enter_selected(event: KeyPressEvent) -> None:
    event.current_buffer.complete_state = None


def _on_enter_submit(event: KeyPressEvent) -> None:
    event.current_buffer.validate_and_handle()


def _on_alt_enter(event: KeyPressEvent) -> None:
    event.current_buffer.insert_text("\n")


def _on_ctrl_p(event: KeyPressEvent) -> None:
    event.current_buffer.history_backward(count=event.arg)


def _on_ctrl_n(event: KeyPressEvent) -> None:
    event.current_buffer.history_forward(count=event.arg)


def _alt_enter_allowed(cells: list[list[object]]) -> bool:
    settings = _session(cells).settings
    return not settings.vi_mode and not (settings.multi_line and settings.multiline_mode == "safe")


def _editor() -> str | None:
    return os.environ.get("PSQL_EDITOR") or os.environ.get("EDITOR") or os.environ.get("VISUAL") or None


def _handle_editor(cells: list[list[object]], prompt_session: PromptSession[str], text: str) -> str | None:
    iocommands: Any = pgspecial.iocommands
    while True:
        command = cast(object, iocommands.editor_command(text))
        if not command:
            return text
        cmd = str(command)
        filename: str | None = None
        if cmd in ("\\ev", "\\ef"):
            parts = text.split()
            spec = parts[1] if len(parts) > 1 else ""
            if cmd == "\\ev":
                result = view_definition_sql(_session(cells).executor, spec)
            else:
                result = function_definition_sql(_session(cells).executor, spec)
            if not isinstance(result, Ok):
                error = result.error
                click.secho(error.message if isinstance(error, EvaluateError_Failed) else "", err=True, fg="red")
                return None
            query = result.value
        else:
            raw_filename = cast(object, iocommands.get_filename(text))
            filename = str(raw_filename) if raw_filename is not None else None
            raw_query = cast(object, iocommands.get_editor_query(text))
            query = str(raw_query) if raw_query else _session(cells).last_query
        opened = cast(object, iocommands.open_external_editor(filename, sql=query, editor=_editor()))
        if not isinstance(opened, tuple):
            raise TypeError("editor did not return a query and message")
        values = cast(tuple[object, ...], opened)
        sql = str(values[0]) if values[0] is not None else ""
        message = values[1]
        if message:
            click.secho(str(message), err=True, fg="red")
            return None
        while True:
            _put(cells, _NOW, datetime.datetime.today().strftime("%x %X"))
            try:
                text = prompt_session.prompt(default=sql)
                break
            except KeyboardInterrupt:
                sql = ""


def _screen(prompt_session: PromptSession[str]) -> TerminalSize:
    size = prompt_session.output.get_size()
    return TerminalSize(columns=size.columns, rows=size.rows)


def run_pgcli_repl(session: Session, settings: ReplSettings) -> Session:
    history = FileHistory(settings.history_file)
    cells: list[list[object]] = [
        [session],
        [session.catalog],
        [_empty_prevalence()],
        [False],
        [False],
        [threading.Lock()],
        [history],
        [None],
        [datetime.datetime.today().strftime("%x %X")],
    ]
    _start_refresh(cells, settings, False)
    getter: Callable[[Document, CompleteEvent], Iterable[Completion]] = lambda document, complete_event: _complete(cells, settings, document, complete_event)
    inner = types.SimpleNamespace(get_completions=getter)
    completer = ThreadedCompleter(cast(Completer, inner))
    kb = KeyBindings()
    h_f2: Callable[[KeyPressEvent], None] = lambda event: _on_f2(cells)
    h_f3: Callable[[KeyPressEvent], None] = lambda event: _on_f3(cells)
    h_f4: Callable[[KeyPressEvent], None] = lambda event: _on_f4(cells, event)
    h_f5: Callable[[KeyPressEvent], None] = lambda event: _on_f5(cells)
    h_tab: Callable[[KeyPressEvent], None] = lambda event: _on_tab(event)
    h_esc: Callable[[KeyPressEvent], None] = lambda event: _on_escape(event)
    h_cspace: Callable[[KeyPressEvent], None] = lambda event: _on_ctrl_space(event)
    h_enter_sel: Callable[[KeyPressEvent], None] = lambda event: _on_enter_selected(event)
    h_enter_submit: Callable[[KeyPressEvent], None] = lambda event: _on_enter_submit(event)
    selected_ok: Callable[[], bool] = lambda: _completion_selected()
    submit_ok: Callable[[], bool] = lambda: _should_submit(cells)
    h_alt: Callable[[KeyPressEvent], None] = lambda event: _on_alt_enter(event)
    h_cp: Callable[[KeyPressEvent], None] = lambda event: _on_ctrl_p(event)
    h_cn: Callable[[KeyPressEvent], None] = lambda event: _on_ctrl_n(event)
    alt_ok: Callable[[], bool] = lambda: _alt_enter_allowed(cells)
    kb.add("f2")(h_f2)
    kb.add("f3")(h_f3)
    kb.add("f4")(h_f4)
    kb.add("f5")(h_f5)
    kb.add("tab")(h_tab)
    kb.add("escape", filter=has_completions)(h_esc)
    kb.add("c-space")(h_cspace)
    kb.add("enter", filter=Condition(selected_ok))(h_enter_sel)
    kb.add("enter", filter=HasFocus(DEFAULT_BUFFER) & Condition(submit_ok))(h_enter_submit)
    kb.add("escape", "enter", filter=Condition(alt_ok))(h_alt)
    kb.add("c-p", filter=~has_selection)(h_cp)
    kb.add("c-n", filter=~has_selection)(h_cn)

    message: Callable[[], AnyFormattedText] = lambda: _message(cells)
    continuation: Callable[[int, int, int], AnyFormattedText] = lambda width, line_number, is_soft_wrap: _continuation(settings.multiline_continuation_char, width)
    toolbar: Callable[[], AnyFormattedText] | None = None
    if settings.show_bottom_toolbar:
        toolbar = lambda: _toolbar(cells)
    prompt_session: PromptSession[str] = PromptSession(
        message=message,
        lexer=PygmentsLexer(pygments.lexers.sql.PostgresLexer),
        reserve_space_for_menu=settings.min_num_menu_lines,
        prompt_continuation=continuation,
        bottom_toolbar=toolbar,
        complete_style=CompleteStyle.MULTI_COLUMN if settings.wider_completion_menu else CompleteStyle.COLUMN,
        input_processors=[
            ConditionalProcessor(HighlightMatchingBracketProcessor(chars="[](){}"), HasFocus(DEFAULT_BUFFER) & ~IsDone()),
            TabsProcessor(char1=" ", char2=" "),
        ],
        auto_suggest=AutoSuggestFromHistory() if settings.auto_suggest else None,
        tempfile_suffix=".sql",
        multiline=True,
        history=history,
        completer=completer,
        complete_while_typing=True,
        style=_build_style(settings),
        include_default_pygments_style=False,
        key_bindings=kb,
        enable_open_in_editor=True,
        enable_system_prompt=True,
        enable_suspend=True,
        editing_mode=EditingMode.VI if session.settings.vi_mode else EditingMode.EMACS,
        search_ignore_case=True,
        cursor=ModalCursorShapeConfig() if session.settings.vi_mode else None,
    )
    _put(cells, _APP, prompt_session.app)

    if not session.settings.less_chatty:
        click.echo("Server: PostgreSQL " + session.executor.server_version)
        click.echo("Version: " + _VERSION)
        click.echo("Home: https://pgcli.com")

    lock = _lock(cells)
    while True:
        _put(cells, _NOW, datetime.datetime.today().strftime("%x %X"))
        try:
            text = prompt_session.prompt()
        except KeyboardInterrupt:
            continue
        except EOFError:
            decision = confirm_quit_with_transaction(_session(cells), _screen(prompt_session))
            with lock:
                _store_session(cells, decision.session)
            if decision.quit:
                break
            continue
        edited = _handle_editor(cells, prompt_session, text)
        if edited is None:
            continue
        text = edited
        current = _session(cells)
        current = dataclasses.replace(current, catalog=_catalog(cells), settings=dataclasses.replace(current.settings, completion_refreshing=bool(_get(cells, _REFRESHING))))
        screen = _screen(prompt_session)
        outcome = watch_pgcli_command(current, text, screen)
        with lock:
            _store_session(cells, outcome.session)
        if outcome.quit:
            decision = confirm_quit_with_transaction(_session(cells), screen)
            with lock:
                _store_session(cells, decision.session)
            if decision.quit:
                break
        refresh = outcome.refresh
        if isinstance(refresh, RefreshKind_Reset):
            _start_refresh(cells, settings, True)
        elif isinstance(refresh, RefreshKind_All):
            _start_refresh(cells, settings, False)
        elif isinstance(refresh, RefreshKind_SearchPath):
            path = read_search_path(_session(cells).executor)
            if isinstance(path, Ok):
                with lock:
                    _put(cells, _CATALOG, catalog_with_search_path(_catalog(cells), path.value))
                    _store_session(cells, _session(cells))
        with lock:
            _put(cells, _PREVALENCE, update_prevalence(_prevalence(cells), text, False))

    if not _session(cells).settings.less_chatty:
        click.echo("Goodbye!")
    return _session(cells)
