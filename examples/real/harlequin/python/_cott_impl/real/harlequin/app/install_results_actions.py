import contextlib
import dataclasses
import threading
import typing
from collections.abc import Callable

from prompt_toolkit.application import Application

from cott_runtime import Err, Some, UNIT, Unit
from real.harlequin.app_types import IdeSession
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.export import export_dialog_key, new_export_dialog, write_result
from real.harlequin.export_types import (
    ExportDialog,
    ExportError,
    ExportError_InvalidOption,
    ExportError_PathIsDirectory,
    ExportError_UnknownFormat,
    ExportOutcome_Cancel,
    ExportOutcome_Export,
    ExportRequest,
)
from real.harlequin.ide import cell_modal, error_modal, text_modal_key
from real.harlequin.ide_types import LayoutState, Pane_Results, TextModal, TextModalOutcome_Close, TextModalOutcome_Copy
from real.harlequin.results import cursor_cell, move_grid, selection_text
from real.harlequin.results_types import (
    GridMotion,
    GridMotion_ColumnEnd,
    GridMotion_ColumnStart,
    GridMotion_Down,
    GridMotion_Left,
    GridMotion_NextCell,
    GridMotion_PageDown,
    GridMotion_PageUp,
    GridMotion_PreviousCell,
    GridMotion_Right,
    GridMotion_RowEnd,
    GridMotion_RowStart,
    GridMotion_SelectAll,
    GridMotion_TableEnd,
    GridMotion_TableStart,
    GridMotion_Up,
    ResultSet,
    ResultsGrid,
)
from real.harlequin.support import copy_to_clipboard


def _grid(shared: dict[str, object]) -> ResultsGrid | None:
    grids = typing.cast(list[ResultsGrid], shared["grids"])
    index = typing.cast(int, shared["result_index"])
    return grids[index] if 0 <= index < len(grids) else None


def _page_rows(shared: dict[str, object]) -> int:
    layout = typing.cast(LayoutState, shared["layout"])
    if isinstance(layout.focus, Pane_Results):
        window = typing.cast(Application[object], shared["app"]).layout.current_window
        rendered = window.render_info
        if rendered is not None:
            return rendered.window_height
    height = typing.cast(Callable[[], tuple[int, int]], shared["size"])()[1]
    if layout.full_screen and isinstance(layout.focus, Pane_Results):
        return max(height - 3, 1)
    return max((height - 4) // 2, 1)


def _move(shared: dict[str, object], motion: GridMotion, extend: bool) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        grid = _grid(shared)
        if grid is None:
            return
        index = typing.cast(int, shared["result_index"])
        typing.cast(list[ResultsGrid], shared["grids"])[index] = move_grid(grid, motion, extend, _page_rows(shared))
        typing.cast(Callable[[], None], shared["invalidate"])()


def _register_motion(shared: dict[str, object], handlers: dict[str, Callable[[], None]], motion: GridMotion, cursor_name: str, select_name: str) -> None:
    handlers["results_viewer." + cursor_name] = lambda: _move(shared, motion, False)
    if select_name:
        handlers["results_viewer." + select_name] = lambda: _move(shared, motion, True)


def _select_cursor(shared: dict[str, object]) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        grid = _grid(shared)
        if grid is None or grid.anchor == grid.cursor:
            return
        typing.cast(list[ResultsGrid], shared["grids"])[typing.cast(int, shared["result_index"])] = dataclasses.replace(grid, anchor=grid.cursor)
        typing.cast(Callable[[], None], shared["invalidate"])()


def _cycle(shared: dict[str, object], direction: int) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        count = len(typing.cast(list[ResultsGrid], shared["grids"]))
        if count == 0:
            return
        shared["result_index"] = (typing.cast(int, shared["result_index"]) + direction) % count
        typing.cast(Callable[[], None], shared["invalidate"])()


def _copy(shared: dict[str, object], text: str, notice: str) -> None:
    copied = copy_to_clipboard(text)
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        if isinstance(copied, Err):
            typing.cast(Callable[[str | None, str, str], None], shared["notify"])(None, copied.error.message, "error")
        else:
            typing.cast(Callable[[str | None, str, str], None], shared["notify"])(None, notice, "information")
        typing.cast(Callable[[], None], shared["invalidate"])()


def _copy_selection(shared: dict[str, object]) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        grid = _grid(shared)
        if grid is None:
            return
        text = selection_text(grid)
    _copy(shared, text, "Selected data copied to clipboard.")


def _view_cell(shared: dict[str, object]) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        grid = _grid(shared)
        if grid is None:
            return
        cell = cursor_cell(grid)
        if isinstance(cell, Some):
            typing.cast(Callable[[str, object], None], shared["open_dialog"])("text", cell_modal(cell.value.column, cell.value.text))
            typing.cast(Callable[[], None], shared["invalidate"])()


def _text_key(shared: dict[str, object], key: str) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        raw = shared["dialog"]
        if not isinstance(raw, tuple):
            return
        dialog = typing.cast(tuple[object, ...], raw)
        if len(dialog) != 2 or dialog[0] != "text" or not isinstance(dialog[1], TextModal):
            return
        visible_lines = max(typing.cast(Callable[[], tuple[int, int]], shared["size"])()[1] - 2, 1)
        step = text_modal_key(dialog[1], key, visible_lines)
        outcome = step.outcome
        if isinstance(outcome, TextModalOutcome_Close):
            typing.cast(Callable[[], None], shared["close_dialog"])()
        else:
            shared["dialog"] = ("text", step.modal)
        if not isinstance(outcome, TextModalOutcome_Copy):
            typing.cast(Callable[[], None], shared["invalidate"])()
    if isinstance(outcome, TextModalOutcome_Copy):
        _copy(shared, outcome.text, outcome.notice)


def _show_exporter(shared: dict[str, object]) -> None:
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        if not typing.cast(list[ResultSet], shared["results"]):
            return
        settings = typing.cast(HarlequinSettings, shared["settings"])
        typing.cast(Callable[[str, object], None], shared["open_dialog"])("export", new_export_dialog(settings.export_path))
        typing.cast(Callable[[], None], shared["invalidate"])()


def _error_text(error: ExportError) -> str:
    if isinstance(error, ExportError_UnknownFormat):
        return f"Unknown export format: {error.name}"
    if isinstance(error, ExportError_InvalidOption):
        return f"{error.name}: {error.message}"
    if isinstance(error, ExportError_PathIsDirectory):
        return f"Path is a directory: {error.path}"
    return error.message


def _export_worker(shared: dict[str, object], result: ResultSet, request: ExportRequest) -> None:
    written = write_result(result, request)
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        if isinstance(written, Err):
            typing.cast(Callable[[str, object], None], shared["open_dialog"])(
                "text", error_modal("Export Data Error", "Harlequin encountered an error while exporting your data.", _error_text(written.error))
            )
        else:
            typing.cast(Callable[[str | None, str, str], None], shared["notify"])(None, f"Data exported to {written.value.path}.", "information")
        typing.cast(Callable[[], None], shared["invalidate"])()


def _export_key(shared: dict[str, object], key: str, text: str) -> None:
    job: tuple[ResultSet, ExportRequest] | None = None
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        raw = shared["dialog"]
        if not isinstance(raw, tuple):
            return
        dialog = typing.cast(tuple[object, ...], raw)
        if len(dialog) != 2 or dialog[0] != "export" or not isinstance(dialog[1], ExportDialog):
            return
        step = export_dialog_key(dialog[1], key, text)
        outcome = step.outcome
        if isinstance(outcome, ExportOutcome_Cancel):
            typing.cast(Callable[[], None], shared["close_dialog"])()
        elif isinstance(outcome, ExportOutcome_Export):
            results = typing.cast(list[ResultSet], shared["results"])
            index = typing.cast(int, shared["result_index"])
            if 0 <= index < len(results):
                job = (results[index], outcome.request)
            typing.cast(Callable[[], None], shared["close_dialog"])()
        else:
            shared["dialog"] = ("export", step.dialog)
        typing.cast(Callable[[], None], shared["invalidate"])()
    if job is not None:
        result, request = job
        threading.Thread(target=lambda: _export_worker(shared, result, request), daemon=True).start()


def install_results_actions(session: IdeSession) -> Unit:
    handle = session.handle
    if handle.tag != "harlequin.ide":
        raise ValueError("The IDE handle is malformed.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        raise ValueError("The IDE handle is malformed.")
    shared = typing.cast(dict[str, object], raw)
    with typing.cast(contextlib.AbstractContextManager[object], shared["lock"]):
        handlers = typing.cast(dict[str, Callable[[], None]], shared["handlers"])
        dialog_keys = typing.cast(dict[str, Callable[[str, str], None]], shared["dialog_keys"])
        motions: tuple[tuple[GridMotion, str, str], ...] = (
            (GridMotion_Up(), "cursor_up", "select_up"),
            (GridMotion_Down(), "cursor_down", "select_down"),
            (GridMotion_Left(), "cursor_left", "select_left"),
            (GridMotion_Right(), "cursor_right", "select_right"),
            (GridMotion_RowStart(), "cursor_row_start", "select_row_start"),
            (GridMotion_RowEnd(), "cursor_row_end", "select_row_end"),
            (GridMotion_ColumnStart(), "cursor_column_start", "select_column_start"),
            (GridMotion_ColumnEnd(), "cursor_column_end", "select_column_end"),
            (GridMotion_NextCell(), "cursor_next_cell", ""),
            (GridMotion_PreviousCell(), "cursor_previous_cell", ""),
            (GridMotion_PageUp(), "cursor_page_up", "select_page_up"),
            (GridMotion_PageDown(), "cursor_page_down", "select_page_down"),
            (GridMotion_TableStart(), "cursor_table_start", "select_table_start"),
            (GridMotion_TableEnd(), "cursor_table_end", "select_table_end"),
        )
        for motion, cursor_name, select_name in motions:
            _register_motion(shared, handlers, motion, cursor_name, select_name)
        handlers["results_viewer.select_all"] = lambda: _move(shared, GridMotion_SelectAll(), True)
        handlers["results_viewer.select_cursor"] = lambda: _select_cursor(shared)
        handlers["results_viewer.next_tab"] = lambda: _cycle(shared, 1)
        handlers["results_viewer.previous_tab"] = lambda: _cycle(shared, -1)
        handlers["results_viewer.copy_selection"] = lambda: _copy_selection(shared)
        handlers["results_viewer.view_cell"] = lambda: _view_cell(shared)
        handlers["show_data_exporter"] = lambda: _show_exporter(shared)
        text_keys: Callable[[str, str], None] = lambda key, text: _text_key(shared, key)
        export_keys: Callable[[str, str], None] = lambda key, text: _export_key(shared, key, text)
        dialog_keys["text"] = text_keys
        dialog_keys["export"] = export_keys
    return UNIT
