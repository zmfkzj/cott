import contextlib
import threading
import typing
from collections.abc import Callable
from typing import Final, cast

from cott_runtime import UNIT, Err, Some, Unit
from prompt_toolkit.application import Application

from real.harlequin.app_types import IdeSession
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.export import export_dialog_key, new_export_dialog, write_result
from real.harlequin.export_types import ExportDialog, ExportError, ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_UnknownFormat, ExportOutcome_Cancel, ExportOutcome_Export, ExportRequest
from real.harlequin.ide import cell_modal, error_modal, text_modal_key
from real.harlequin.ide_types import TextModal, TextModalOutcome_Close, TextModalOutcome_Copy
from real.harlequin.results import cursor_cell, move_grid, selection_text
from real.harlequin.results_types import GridMotion, GridMotion_ColumnEnd, GridMotion_ColumnStart, GridMotion_Down, GridMotion_Left, GridMotion_NextCell, GridMotion_PageDown, GridMotion_PageUp, GridMotion_PreviousCell, GridMotion_Right, GridMotion_RowEnd, GridMotion_RowStart, GridMotion_SelectAll, GridMotion_TableEnd, GridMotion_TableStart, GridMotion_Up, ResultSet, ResultsGrid
from real.harlequin.support import copy_to_clipboard

_TAG: Final[str] = "harlequin.ide"
_PREFIX: Final[str] = "results_viewer."
_MOTIONS: Final[str] = "cursor_up,cursor_down,cursor_left,cursor_right,cursor_row_start,cursor_row_end,cursor_column_start,cursor_column_end,cursor_next_cell,cursor_previous_cell,cursor_page_up,cursor_page_down,cursor_table_start,cursor_table_end"
_SELECT_ALL: Final[int] = 14


def _motion(code: int) -> GridMotion:
    if code == 0:
        return GridMotion_Up()
    if code == 1:
        return GridMotion_Down()
    if code == 2:
        return GridMotion_Left()
    if code == 3:
        return GridMotion_Right()
    if code == 4:
        return GridMotion_RowStart()
    if code == 5:
        return GridMotion_RowEnd()
    if code == 6:
        return GridMotion_ColumnStart()
    if code == 7:
        return GridMotion_ColumnEnd()
    if code == 8:
        return GridMotion_NextCell()
    if code == 9:
        return GridMotion_PreviousCell()
    if code == 10:
        return GridMotion_PageUp()
    if code == 11:
        return GridMotion_PageDown()
    if code == 12:
        return GridMotion_TableStart()
    if code == 13:
        return GridMotion_TableEnd()
    return GridMotion_SelectAll()


def _lock(shared: dict[str, object]) -> contextlib.AbstractContextManager[object]:
    return cast(contextlib.AbstractContextManager[object], shared["lock"])


def _current_grid(shared: dict[str, object]) -> ResultsGrid | None:
    grids = cast(list[ResultsGrid], shared["grids"])
    index = cast(int, shared["result_index"])
    if 0 <= index < len(grids):
        return grids[index]
    return None


def _results_height(shared: dict[str, object]) -> int:
    app = cast(Application[object], shared["app"])
    info = app.layout.current_window.render_info
    if info is not None:
        return max(info.window_height, 1)
    return max(typing.cast(Callable[[], tuple[int, int]], shared["size"])()[1], 1)


def _move(shared: dict[str, object], code: int, extend: bool) -> None:
    page = _results_height(shared)
    with _lock(shared):
        grid = _current_grid(shared)
        if grid is None:
            return
        grids = cast(list[ResultsGrid], shared["grids"])
        grids[cast(int, shared["result_index"])] = move_grid(grid, _motion(code), extend, page)
    typing.cast(Callable[[], None], shared["invalidate"])()


def _cycle_tab(shared: dict[str, object], step: int) -> None:
    with _lock(shared):
        count = len(cast(list[ResultsGrid], shared["grids"]))
        if count == 0:
            return
        shared["result_index"] = (cast(int, shared["result_index"]) + step) % count
    typing.cast(Callable[[], None], shared["invalidate"])()


def _copy(shared: dict[str, object], text: str, notice: str) -> None:
    copied = copy_to_clipboard(text)
    with _lock(shared):
        if isinstance(copied, Err):
            typing.cast(Callable[[str | None, str, str], None], shared["notify"])(None, copied.error.message, "error")
        else:
            typing.cast(Callable[[str | None, str, str], None], shared["notify"])(None, notice, "information")
    typing.cast(Callable[[], None], shared["invalidate"])()


def _copy_selection(shared: dict[str, object]) -> None:
    with _lock(shared):
        grid = _current_grid(shared)
    if grid is None:
        return
    _copy(shared, selection_text(grid), "Selected data copied to clipboard.")


def _view_cell(shared: dict[str, object]) -> None:
    with _lock(shared):
        grid = _current_grid(shared)
    if grid is None:
        return
    cell = cursor_cell(grid)
    if isinstance(cell, Some):
        typing.cast(Callable[[str, object], None], shared["open_dialog"])("text", cell_modal(cell.value.column, cell.value.text))
        typing.cast(Callable[[], None], shared["invalidate"])()


def _text_key(shared: dict[str, object], key: str) -> None:
    with _lock(shared):
        dialog = shared["dialog"]
    if not isinstance(dialog, tuple):
        return
    pair = cast(tuple[object, object], dialog)
    model = pair[1]
    if pair[0] != "text" or not isinstance(model, TextModal):
        return
    visible = max(typing.cast(Callable[[], tuple[int, int]], shared["size"])()[1] - 2, 1)
    step = text_modal_key(model, key, visible)
    outcome = step.outcome
    if isinstance(outcome, TextModalOutcome_Close):
        typing.cast(Callable[[], None], shared["close_dialog"])()
        typing.cast(Callable[[], None], shared["invalidate"])()
        return
    with _lock(shared):
        shared["dialog"] = ("text", step.modal)
    if isinstance(outcome, TextModalOutcome_Copy):
        _copy(shared, outcome.text, outcome.notice)
    typing.cast(Callable[[], None], shared["invalidate"])()


def _show_exporter(shared: dict[str, object]) -> None:
    with _lock(shared):
        count = len(cast(list[ResultSet], shared["results"]))
        settings = cast(HarlequinSettings, shared["settings"])
    if count == 0:
        return
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
    if isinstance(written, Err):
        modal = error_modal("Export Data Error", "Harlequin encountered an error while exporting your data.", _error_text(written.error))
        with _lock(shared):
            typing.cast(Callable[[str, object], None], shared["open_dialog"])("text", modal)
    else:
        with _lock(shared):
            typing.cast(Callable[[str | None, str, str], None], shared["notify"])(None, f"Data exported to {written.value.path}.", "information")
    typing.cast(Callable[[], None], shared["invalidate"])()


def _export_key(shared: dict[str, object], key: str, text: str) -> None:
    with _lock(shared):
        dialog = shared["dialog"]
    if not isinstance(dialog, tuple):
        return
    pair = cast(tuple[object, object], dialog)
    model = pair[1]
    if pair[0] != "export" or not isinstance(model, ExportDialog):
        return
    step = export_dialog_key(model, key, text)
    outcome = step.outcome
    if isinstance(outcome, ExportOutcome_Cancel):
        typing.cast(Callable[[], None], shared["close_dialog"])()
        typing.cast(Callable[[], None], shared["invalidate"])()
        return
    if isinstance(outcome, ExportOutcome_Export):
        with _lock(shared):
            results = cast(list[ResultSet], shared["results"])
            index = cast(int, shared["result_index"])
            result = results[index] if 0 <= index < len(results) else None
        typing.cast(Callable[[], None], shared["close_dialog"])()
        if result is not None:
            request = outcome.request
            threading.Thread(target=lambda: _export_worker(shared, result, request), daemon=True).start()
        typing.cast(Callable[[], None], shared["invalidate"])()
        return
    with _lock(shared):
        shared["dialog"] = ("export", step.dialog)
    typing.cast(Callable[[], None], shared["invalidate"])()


def _register_motion(shared: dict[str, object], handlers: dict[str, Callable[[], None]], name: str, code: int) -> None:
    handlers[_PREFIX + name] = lambda: _move(shared, code, False)
    if name not in ("cursor_next_cell", "cursor_previous_cell"):
        handlers[_PREFIX + "select_" + name.removeprefix("cursor_")] = lambda: _move(shared, code, True)


def install_results_actions(session: IdeSession) -> Unit:
    handle = session.handle
    if handle.tag != _TAG:
        raise ValueError("The IDE handle is malformed.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        raise ValueError("The IDE handle is malformed.")
    shared = cast(dict[str, object], raw)
    with _lock(shared):
        handlers = cast(dict[str, Callable[[], None]], shared["handlers"])
        dialog_keys = cast(dict[str, Callable[[str, str], None]], shared["dialog_keys"])
        for code, name in enumerate(_MOTIONS.split(",")):
            _register_motion(shared, handlers, name, code)
        handlers[_PREFIX + "select_all"] = lambda: _move(shared, _SELECT_ALL, False)
        handlers[_PREFIX + "next_tab"] = lambda: _cycle_tab(shared, 1)
        handlers[_PREFIX + "previous_tab"] = lambda: _cycle_tab(shared, -1)
        handlers[_PREFIX + "copy_selection"] = lambda: _copy_selection(shared)
        handlers[_PREFIX + "view_cell"] = lambda: _view_cell(shared)
        handlers["show_data_exporter"] = lambda: _show_exporter(shared)
        dialog_keys["text"] = lambda key, text: _text_key(shared, key)
        dialog_keys["export"] = lambda key, text: _export_key(shared, key, text)
    return UNIT
