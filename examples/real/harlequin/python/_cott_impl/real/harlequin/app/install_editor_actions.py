import contextlib
import os
import re
import threading
import time
import types
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, cast

from cott_runtime import CottList, Err, Ok, Some, UNIT, Unit
from prompt_toolkit.application import Application, run_in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion, ThreadedCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.filters import to_filter
from prompt_toolkit.selection import SelectionState

from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.catalog import buffer_identifiers, complete
from real.harlequin.catalog_types import CompletionSet
from real.harlequin.files import complete_path, expand_path, load_text_file, save_text_file
from real.harlequin.files_types import FileError, FileError_InvalidEncoding, FileError_IsADirectory, FileError_NotFound, FileError_PermissionDenied
from real.harlequin.ide import apply_completions, error_modal, input_key, input_modal
from real.harlequin.ide_types import InputModal, InputOutcome_Cancel, InputOutcome_Complete, InputOutcome_Stay, InputPurpose, InputPurpose_Find, InputPurpose_GoToLine, InputPurpose_OpenFile, InputPurpose_SaveFile
from real.harlequin.sqltext import format_sql, toggle_comment
from real.harlequin.sqltext_types import TextRange
from real.harlequin.support import adopt_recovery, copy_to_clipboard, edit_externally, load_buffer_cache, osc52_sequence, paste_from_clipboard, remove_file, resolve_editor, save_buffer_cache
from real.harlequin.support_types import BufferCache, BufferState, ExternalEditorError_NoEditor

_MOVES: Final[str] = "up,down,left,right,word_left,word_right,line_start,line_end,doc_start,doc_end"
_DELETES: Final[str] = "delete_left,delete_right,delete_word_left,delete_word_right,delete_line,delete_to_start_of_line,delete_to_end_of_line"
_MALFORMED: Final[str] = "The IDE session handle is malformed."


def _lock(s: dict[str, object]) -> contextlib.AbstractContextManager[object]:
    return cast(contextlib.AbstractContextManager[object], s["lock"])


def _entries(s: dict[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], s["buffers"])


def _active(s: dict[str, object]) -> Buffer:
    return cast(Buffer, _entries(s)[cast(int, s["active"])]["buffer"])


def _context(s: dict[str, object]) -> IdeContext:
    return cast(IdeContext, s["context"])


def _invalidate(s: dict[str, object]) -> None:
    app = cast(Application[object], s["app"])
    app.invalidate()


def _notify(s: dict[str, object], title: str | None, message: str, severity: str) -> None:
    cast(Callable[[str | None, str, str], None], s["notify"])(title, message, severity)


def _focus(s: dict[str, object]) -> None:
    cast(Callable[[str], None], s["focus"])("focus_query_editor")


def _dialog(s: dict[str, object], kind: str, model: object) -> None:
    cast(Callable[[str, object], None], s["open_dialog"])(kind, model)


def _anchor(buffer: Buffer) -> int:
    selection = buffer.selection_state
    return buffer.cursor_position if selection is None else selection.original_cursor_position


def _set(buffer: Buffer, text: str, anchor: int, cursor: int) -> None:
    a = max(0, min(anchor, len(text)))
    c = max(0, min(cursor, len(text)))
    buffer.set_document(Document(text, c), bypass_readonly=True)
    buffer.selection_state = SelectionState(original_cursor_position=a) if a != c else None


def _word_before_cursor(document: Document) -> str:
    before = document.text_before_cursor
    start = len(before)
    quote = ""
    while start:
        char = before[start - 1]
        if quote:
            start -= 1
            if char == quote:
                quote = ""
        elif char in "\"'`":
            quote = char
            start -= 1
        elif char.isalnum() or char in "_$.:":
            start -= 1
        else:
            break
    return before[start:]


def _complete(s: dict[str, object], document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
    prefix = _word_before_cursor(document)
    if not prefix:
        return []
    with _lock(s):
        candidates = cast(CompletionSet, s["completions"])
    if candidates.tag != "harlequin.completions":
        return []
    matches = complete(candidates, buffer_identifiers(document.text), prefix, 50)
    return [Completion(text=item.value, start_position=-len(prefix), display=item.label, display_meta=item.type_label) for item in matches]


def _completer(s: dict[str, object]) -> Completer:
    get_completions: Callable[[Document, CompleteEvent], Iterable[Completion]] = lambda document, complete_event: _complete(s, document, complete_event)
    return ThreadedCompleter(cast(Completer, types.SimpleNamespace(get_completions=get_completions)))


def _new(s: dict[str, object], text: str) -> None:
    with _lock(s):
        buffer = Buffer(multiline=True, completer=_completer(s), complete_while_typing=True)
        _set(buffer, text, len(text), len(text))
        counter = cast(int, s["tab_counter"]) + 1
        s["tab_counter"] = counter
        entries = _entries(s)
        entries.append({"title": f"Tab {counter}", "buffer": buffer})
        s["active"] = len(entries) - 1
    _focus(s)
    _invalidate(s)


def _close(s: dict[str, object]) -> None:
    with _lock(s):
        entries = _entries(s)
        index = cast(int, s["active"])
        if len(entries) == 1:
            buffer = _active(s)
            if buffer.text:
                buffer.save_to_undo_stack()
                _set(buffer, "", 0, 0)
            else:
                buffer.exit_selection()
                buffer.cursor_position = 0
        else:
            entries.pop(index)
            s["active"] = index % len(entries)
    _focus(s)
    _invalidate(s)


def _next(s: dict[str, object]) -> None:
    with _lock(s):
        entries = _entries(s)
        if len(entries) < 2:
            return
        s["active"] = (cast(int, s["active"]) + 1) % len(entries)
    _focus(s)
    _invalidate(s)


def _format(s: dict[str, object]) -> None:
    with _lock(s):
        buffer = _active(s)
        result = format_sql(buffer.text)
        if isinstance(result, Err):
            _dialog(s, "text", error_modal("Formatting Error", "There was an error while formatting your file:", result.error.message))
        elif result.value == buffer.text:
            _notify(s, None, "Query was already formatted; no changes made.", "information")
        else:
            position = buffer.cursor_position
            buffer.save_to_undo_stack()
            _set(buffer, result.value, position, position)
            _notify(s, None, "Formatted query.", "information")
    _invalidate(s)


def _comment(s: dict[str, object]) -> None:
    with _lock(s):
        buffer = _active(s)
        anchor, cursor = _anchor(buffer), buffer.cursor_position
        edited = toggle_comment(buffer.text, TextRange(start=min(anchor, cursor), end=max(anchor, cursor)))
        if edited.text != buffer.text:
            buffer.save_to_undo_stack()
            if anchor <= cursor:
                _set(buffer, edited.text, edited.anchor, edited.cursor)
            else:
                _set(buffer, edited.text, edited.cursor, edited.anchor)
    _invalidate(s)


def _target(document: Document, op: str) -> int:
    position = document.cursor_position
    if op == "word_left":
        offset = document.find_previous_word_beginning()
        return position + offset if offset is not None else 0
    if op == "word_right":
        offset = document.find_next_word_ending(include_current_position=True)
        return position + offset if offset is not None else len(document.text)
    if op == "line_start":
        return position + document.get_start_of_line_position()
    if op == "line_end":
        return position + document.get_end_of_line_position()
    if op == "doc_start":
        return 0
    if op == "doc_end":
        return len(document.text)
    return position


def _move(s: dict[str, object], op: str, select: bool) -> None:
    with _lock(s):
        buffer = _active(s)
        if select:
            if buffer.selection_state is None:
                buffer.start_selection()
        else:
            buffer.exit_selection()
        if op == "up":
            buffer.cursor_up()
        elif op == "down":
            buffer.cursor_down()
        elif op == "left":
            buffer.cursor_left()
        elif op == "right":
            buffer.cursor_right()
        elif op in ("page_up", "page_down"):
            app = cast(Application[object], s["app"])
            info = app.layout.current_window.render_info
            rows = info.window_height if info is not None else cast(Callable[[], tuple[int, int]], s["size"])()[1]
            count = max(rows - 1, 1)
            if op == "page_up":
                buffer.cursor_up(count=count)
            else:
                buffer.cursor_down(count=count)
        else:
            buffer.cursor_position = _target(buffer.document, op)
    _invalidate(s)


def _scroll(s: dict[str, object], down: bool) -> None:
    with _lock(s):
        window = cast(Application[object], s["app"]).layout.current_window
        info = window.render_info
        if info is None:
            return
        buffer = _active(s)
        if down:
            if window.vertical_scroll < info.content_height - info.window_height:
                if info.cursor_position.y <= info.configured_scroll_offsets.top:
                    buffer.cursor_down()
                window.vertical_scroll += 1
        elif window.vertical_scroll > 0:
            first_height = info.get_height_for_line(info.first_visible_line())
            cursor_up = info.cursor_position.y - (info.window_height - 1 - first_height - info.configured_scroll_offsets.bottom)
            for _ in range(max(0, cursor_up)):
                buffer.cursor_up()
            window.vertical_scroll -= 1
    _invalidate(s)


def _select(s: dict[str, object], scope: str) -> None:
    with _lock(s):
        buffer = _active(s)
        document = buffer.document
        if scope == "all":
            start, end = 0, len(buffer.text)
        elif scope == "word":
            left, right = document.find_boundaries_of_current_word()
            start, end = document.cursor_position + left, document.cursor_position + right
        else:
            start, end = _target(document, "line_start"), _target(document, "line_end")
        buffer.cursor_position = end
        buffer.selection_state = SelectionState(original_cursor_position=start) if start != end else None
    _invalidate(s)


def _delete(s: dict[str, object], op: str) -> None:
    with _lock(s):
        buffer = _active(s)
        if buffer.selection_state is not None:
            buffer.save_to_undo_stack()
            buffer.cut_selection()
        else:
            document = buffer.document
            start = end = document.cursor_position
            if op == "delete_left":
                start = max(0, start - 1)
            elif op == "delete_right":
                end = min(len(buffer.text), end + 1)
            elif op == "delete_word_left":
                start = _target(document, "word_left")
            elif op == "delete_word_right":
                end = _target(document, "word_right")
            elif op == "delete_to_start_of_line":
                start = _target(document, "line_start")
            elif op == "delete_to_end_of_line":
                end = _target(document, "line_end")
            else:
                start = _target(document, "line_start")
                end = _target(document, "line_end")
                if end < len(buffer.text):
                    end += 1
                elif start:
                    start -= 1
            if start != end:
                buffer.save_to_undo_stack()
                buffer.cursor_position = end
                buffer.delete_before_cursor(count=end - start)
    _invalidate(s)


def _file_error(error: FileError) -> str:
    if isinstance(error, FileError_NotFound):
        return f"No such file: {error.path}"
    if isinstance(error, FileError_IsADirectory):
        return f"{error.path} is a directory."
    if isinstance(error, FileError_PermissionDenied):
        return f"Permission denied: {error.path}"
    if isinstance(error, FileError_InvalidEncoding):
        return f"{error.path} is not a UTF-8 text file."
    return f"{error.path}: {error.message}"


def _input(s: dict[str, object], purpose: InputPurpose) -> None:
    _dialog(s, "input", input_modal(purpose, ""))
    _invalidate(s)


def _find(s: dict[str, object], cells: dict[str, object]) -> None:
    with _lock(s):
        query = cast(str, cells["search"])
        if not query:
            _input(s, InputPurpose_Find())
            return
        buffer = _active(s)
        anchor, cursor = _anchor(buffer), buffer.cursor_position
        offset = max(anchor, cursor) if anchor != cursor else cursor + 1
        first: re.Match[str] | None = None
        match: re.Match[str] | None = None
        for found in re.finditer(re.escape(query), buffer.text, re.IGNORECASE):
            if first is None:
                first = found
            if found.start() >= offset:
                match = found
                break
        if match is None:
            match = first
        if match is None:
            _notify(s, None, f"No matches found for {query!r}.", "warning")
        else:
            buffer.cursor_position = match.end()
            buffer.selection_state = SelectionState(original_cursor_position=match.start())
    _focus(s)
    _invalidate(s)


def _submit(s: dict[str, object], cells: dict[str, object], modal: InputModal, value: str) -> None:
    if isinstance(modal.purpose, InputPurpose_Find):
        cells["search"] = value
        _find(s, cells)
        return
    with _lock(s):
        buffer = _active(s)
        if isinstance(modal.purpose, InputPurpose_GoToLine):
            row = min(max(int(value) - 1, 0), buffer.document.line_count - 1)
            buffer.exit_selection()
            buffer.cursor_position = buffer.document.translate_row_col_to_index(row, 0)
        else:
            path = expand_path(value, Path.home(), Path.cwd())
            if isinstance(modal.purpose, InputPurpose_SaveFile):
                saved = save_text_file(path, buffer.text)
                if isinstance(saved, Err):
                    _dialog(s, "text", error_modal("File Error", "Harlequin could not save your query:", _file_error(saved.error)))
                else:
                    _notify(s, None, f"Editor contents saved to {path}", "information")
            else:
                loaded = load_text_file(path)
                if isinstance(loaded, Err):
                    _dialog(s, "text", error_modal("File Error", "Harlequin could not open your query:", _file_error(loaded.error)))
                else:
                    buffer.save_to_undo_stack()
                    _set(buffer, loaded.value, 0, 0)
    _invalidate(s)


def _input_key(s: dict[str, object], cells: dict[str, object], key: str, text: str) -> None:
    with _lock(s):
        dialog = s["dialog"]
        if not isinstance(dialog, tuple):
            return
        model = cast(tuple[str, object], dialog)[1]
        if not isinstance(model, InputModal):
            return
        step = input_key(model, key, text)
        outcome = step.outcome
        if isinstance(outcome, InputOutcome_Stay):
            s["dialog"] = ("input", step.modal)
        elif isinstance(outcome, InputOutcome_Complete):
            s["dialog"] = ("input", apply_completions(step.modal, complete_path(outcome.value, Path.home(), Path.cwd())))
        else:
            cast(Callable[[], None], s["close_dialog"])()
            _focus(s)
            if not isinstance(outcome, InputOutcome_Cancel):
                _submit(s, cells, step.modal, outcome.value)
    _invalidate(s)


def _run_editor(s: dict[str, object], app: Application[object], buffer: Buffer, text: str, command: CottList[str]) -> None:
    result = edit_externally(text, command)
    with _lock(s):
        if isinstance(result, Err):
            error = result.error
            _notify(s, "Editor Error", "No editor found." if isinstance(error, ExternalEditorError_NoEditor) else error.message, "error")
        elif isinstance(result.value.text, Some):
            position = buffer.cursor_position
            buffer.save_to_undo_stack()
            _set(buffer, result.value.text.value, position, position)
        else:
            _notify(s, "Editor Error", f"External editor exited with status {result.value.returncode}.", "error")
    app.invalidate()


def _external(s: dict[str, object], app: Application[object]) -> None:
    resolved = resolve_editor(_context(s).environment)
    if isinstance(resolved, Err):
        error = resolved.error
        message = "No external editor found. Set $VISUAL or $EDITOR." if isinstance(error, ExternalEditorError_NoEditor) else error.message
        _notify(s, "Editor Error", message, "error")
        _invalidate(s)
        return
    with _lock(s):
        buffer = _active(s)
        text = buffer.text
    run_in_terminal(lambda: _run_editor(s, app, buffer, text, resolved.value))


def _copy(s: dict[str, object], cut: bool) -> None:
    with _lock(s):
        buffer = _active(s)
        anchor, cursor = _anchor(buffer), buffer.cursor_position
        text = buffer.text[min(anchor, cursor):max(anchor, cursor)]
        if not text:
            return
        copied = copy_to_clipboard(text)
        if isinstance(copied, Err):
            app = cast(Application[object], s["app"])
            app.output.write_raw(osc52_sequence(text))
            app.output.flush()
        if cut:
            buffer.save_to_undo_stack()
            buffer.cut_selection()
    _invalidate(s)


def _insert(s: dict[str, object], text: str) -> None:
    with _lock(s):
        buffer = _active(s)
        buffer.exit_selection()
        if text:
            buffer.save_to_undo_stack()
            buffer.insert_text(text)
    _focus(s)
    _invalidate(s)


def _paste(s: dict[str, object]) -> None:
    result = paste_from_clipboard()
    if isinstance(result, Err):
        _notify(s, "Clipboard Error", result.error.message, "error")
        _invalidate(s)
    else:
        _insert(s, result.value)


def _undo(s: dict[str, object], redo: bool) -> None:
    with _lock(s):
        buffer = _active(s)
        if redo:
            buffer.redo()
        else:
            buffer.undo()
    _invalidate(s)


def _selection(s: dict[str, object]) -> tuple[str, int, int]:
    with _lock(s):
        buffer = _active(s)
        return buffer.text, _anchor(buffer), buffer.cursor_position


def _snapshot(s: dict[str, object]) -> BufferCache:
    states: list[BufferState] = []
    for entry in _entries(s):
        buffer = cast(Buffer, entry["buffer"])
        states.append(BufferState(text=buffer.text, anchor=_anchor(buffer), cursor=buffer.cursor_position))
    return BufferCache(focus_index=cast(int, s["active"]), buffers=CottList(values=states))


def _checkpoint(s: dict[str, object], cells: dict[str, object], stop: threading.Event) -> None:
    while not stop.wait(60.0):
        with _lock(s):
            cache = _snapshot(s)
            key = (cache.focus_index, tuple((item.text, item.anchor, item.cursor) for item in cache.buffers))
            if not any(item.text.strip() for item in cache.buffers) or key == cells["last"]:
                continue
        saved = save_buffer_cache(cast(Path, cells["recovery"]), cache)
        if isinstance(saved, Ok):
            with _lock(s):
                cells["last"] = key


def _finish(s: dict[str, object], cells: dict[str, object], stop: threading.Event, worker: threading.Thread, crash: bool) -> None:
    stop.set()
    worker.join()
    with _lock(s):
        cache = _snapshot(s)
        paths = _context(s).paths
    if crash:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        save_buffer_cache(paths.cache_dir / f"recovered-{stamp}-{os.getpid()}.json", cache)
    else:
        saved = save_buffer_cache(paths.buffer_cache, cache)
        if isinstance(saved, Ok):
            remove_file(cast(Path, cells["recovery"]))


def _restore(s: dict[str, object], cache: BufferCache) -> None:
    entries: list[dict[str, object]] = []
    for state in cache.buffers:
        buffer = Buffer(multiline=True, completer=_completer(s), complete_while_typing=True)
        _set(buffer, state.text, state.anchor, state.cursor)
        entries.append({"title": f"Tab {len(entries) + 1}", "buffer": buffer})
    if entries:
        s["buffers"] = entries
        s["tab_counter"] = len(entries)
        s["active"] = min(max(cache.focus_index, 0), len(entries) - 1)


def _load(s: dict[str, object]) -> None:
    paths = _context(s).paths
    recovered = adopt_recovery(paths.cache_dir, time.time())
    if isinstance(recovered, Ok) and isinstance(recovered.value, Some):
        _restore(s, recovered.value.value)
        _notify(s, "Buffers recovered", "Recovered buffers from a session that ended unexpectedly.", "information")
        return
    loaded = load_buffer_cache(paths.buffer_cache)
    if isinstance(recovered, Err) or isinstance(loaded, Err):
        _notify(s, None, "Harlequin could not load its cache.", "warning")
    if isinstance(loaded, Ok) and isinstance(loaded.value, Some):
        _restore(s, loaded.value.value)


def _register_move(s: dict[str, object], handlers: dict[str, Callable[[], None]], op: str) -> None:
    handlers["code_editor.cursor_" + op] = lambda: _move(s, op, False)
    handlers["code_editor.select_" + op] = lambda: _move(s, op, True)


def _register_delete(s: dict[str, object], handlers: dict[str, Callable[[], None]], op: str) -> None:
    handlers["code_editor." + op] = lambda: _delete(s, op)


def install_editor_actions(session: IdeSession) -> Unit:
    if session.handle.tag != "harlequin.ide":
        raise ValueError(_MALFORMED)
    raw = session.handle.unwrap()
    if not isinstance(raw, dict):
        raise ValueError(_MALFORMED)
    s = cast(dict[str, object], raw)
    if not isinstance(s.get("context"), IdeContext) or not isinstance(s.get("lock"), contextlib.AbstractContextManager):
        raise ValueError(_MALFORMED)
    stop = threading.Event()
    cells: dict[str, object] = {"search": "", "last": None, "recovery": _context(s).paths.cache_dir / f"recovery-{os.getpid()}.json"}
    worker = threading.Thread(target=lambda: _checkpoint(s, cells, stop), daemon=True)
    with _lock(s):
        app = cast(Application[object], s["app"])
        for entry in _entries(s):
            buffer = cast(Buffer, entry["buffer"])
            buffer.completer = _completer(s)
            buffer.complete_while_typing = to_filter(True)
        _load(s)
        handlers = cast(dict[str, Callable[[], None]], s["handlers"])
        handlers["code_editor.new_buffer"] = lambda: _new(s, "")
        handlers["code_editor.close_buffer"] = lambda: _close(s)
        handlers["code_editor.next_buffer"] = lambda: _next(s)
        handlers["code_editor.format_buffer"] = lambda: _format(s)
        handlers["code_editor.toggle_comment"] = lambda: _comment(s)
        handlers["code_editor.save_buffer"] = lambda: _input(s, InputPurpose_SaveFile())
        handlers["code_editor.load_buffer"] = lambda: _input(s, InputPurpose_OpenFile())
        handlers["code_editor.find"] = lambda: _input(s, InputPurpose_Find())
        handlers["code_editor.find_next"] = lambda: _find(s, cells)
        handlers["code_editor.goto_line"] = lambda: _input(s, InputPurpose_GoToLine())
        handlers["code_editor.launch_external_editor"] = lambda: _external(s, app)
        handlers["code_editor.copy"] = lambda: _copy(s, False)
        handlers["code_editor.cut"] = lambda: _copy(s, True)
        handlers["code_editor.paste"] = lambda: _paste(s)
        handlers["code_editor.undo"] = lambda: _undo(s, False)
        handlers["code_editor.redo"] = lambda: _undo(s, True)
        handlers["code_editor.select_all"] = lambda: _select(s, "all")
        handlers["code_editor.select_line"] = lambda: _select(s, "line")
        handlers["code_editor.select_word"] = lambda: _select(s, "word")
        handlers["code_editor.scroll_up_one"] = lambda: _scroll(s, False)
        handlers["code_editor.scroll_down_one"] = lambda: _scroll(s, True)
        handlers["code_editor.cursor_page_up"] = lambda: _move(s, "page_up", False)
        handlers["code_editor.cursor_page_down"] = lambda: _move(s, "page_down", False)
        for op in _MOVES.split(","):
            _register_move(s, handlers, op)
        for op in _DELETES.split(","):
            _register_delete(s, handlers, op)
        dialog_key: Callable[[str, str], None] = lambda key, text: _input_key(s, cells, key, text)
        cast(dict[str, Callable[[str, str], None]], s["dialog_keys"])["input"] = dialog_key
        new_buffer: Callable[[str], None] = lambda text: _new(s, text)
        insert_text: Callable[[str], None] = lambda text: _insert(s, text)
        selection: Callable[[], tuple[str, int, int]] = lambda: _selection(s)
        s["new_buffer"] = new_buffer
        s["insert_text"] = insert_text
        s["selection"] = selection
        cast(list[Callable[[], None]], s["on_exit"]).append(lambda: _finish(s, cells, stop, worker, False))
        cast(list[Callable[[], None]], s["on_crash"]).append(lambda: _finish(s, cells, stop, worker, True))
    worker.start()
    _focus(s)
    _invalidate(s)
    return UNIT
