from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_starts_with

from real.harlequin.ide_types import ConfirmModal, ConfirmOutcome, ConfirmOutcome_No, ConfirmOutcome_Stay, ConfirmOutcome_Yes, ConfirmStep, ContextMenu, ContextMenuOutcome, ContextMenuOutcome_Choose, ContextMenuOutcome_Close, ContextMenuOutcome_Stay, ContextMenuStep, DebugSection, InputModal, InputOutcome, InputOutcome_Cancel, InputOutcome_Complete, InputOutcome_Stay, InputOutcome_Submit, InputPurpose, InputPurpose_Find, InputPurpose_GoToLine, InputPurpose_OpenFile, InputPurpose_SaveFile, InputStep, LayoutState, Notification, Pane, Pane_Catalog, Pane_Editor, Pane_Results, Pane_RunBar, RunBar, RunBarStep, Severity, Severity_Error, Severity_Information, Severity_Warning, TextModal, TextModalOutcome, TextModalOutcome_Close, TextModalOutcome_Copy, TextModalOutcome_Stay, TextModalStep
from real.harlequin.adapters_types import TransactionMode
from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.keymap_types import FooterHint
from real.harlequin.style_types import StyledLine

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def initial_layout() -> LayoutState:
    """The layout at startup: focus Editor, sidebar shown, not full screen."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/initial_layout.py", "91167916f9602a002eb9ffce32cde899bfcfcd016d7c22e78c3d0dd6f6c4b17b", "initial_layout", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.initial_layout")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.initial_layout"
        if _error.span is None:
            _error.span = {"end_byte":3720,"end_column":1,"end_line":168,"start_byte":3468,"start_column":1,"start_line":158}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.initial_layout", phase="implementation-call", span={"end_byte":3720,"end_column":1,"end_line":168,"start_byte":3468,"start_column":1,"start_line":158}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.initial_layout", phase="implementation-call", span={"end_byte":3720,"end_column":1,"end_line":168,"start_byte":3468,"start_column":1,"start_line":158}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, LayoutState, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).focus == Pane_Editor())), "real.harlequin.ide.initial_layout", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.initial_layout", clause="ensures:1", phase="ensures", span={"end_byte":3637,"end_column":40,"end_line":163,"start_byte":3602,"start_column":5,"start_line":163}, expected="true", actual="false")
        if not (_cott_contract_condition((((not (_result).sidebar_hidden) and (not (_result).full_screen))), "real.harlequin.ide.initial_layout", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.initial_layout", clause="ensures:2", phase="ensures", span={"end_byte":3702,"end_column":65,"end_line":164,"start_byte":3642,"start_column":5,"start_line":164}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, LayoutState, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def layout_action(layout: LayoutState, action: str) -> LayoutState:
    """Apply a layout action, as Harlequin's app actions do:
"toggle_sidebar": flip sidebar_hidden; hiding it while the catalog has focus
moves focus to Editor. "toggle_full_screen": flip full_screen; entering full
screen while the catalog or run bar has focus moves focus to Editor.
"focus_query_editor", "focus_results_viewer": focus that pane (leaving full
screen when full screen shows the other pane). "focus_data_catalog": show the
sidebar, leave full screen and focus Catalog. "focus_next" /
"focus_previous": move to the next/previous pane in Tab order among the
visible ones (Catalog only when the sidebar is shown and not full screen;
in full screen only the full-screen pane, plus RunBar when that pane is the
Editor), wrapping. Any other action returns layout unchanged."""
    layout = _cott_normalize_f32_abi(layout, LayoutState, path="$.layout")
    action = _cott_normalize_f32_abi(action, str, path="$.action")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/layout_action.py", "d358e9e1818d59106fde31fd8d46eca5b9b2057043edbce85694849c71c31ede", "layout_action", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.layout_action")
        _result = _implementation(layout, action)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.layout_action"
        if _error.span is None:
            _error.span = {"end_byte":4644,"end_column":1,"end_line":185,"start_byte":3720,"start_column":1,"start_line":168}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.layout_action", phase="implementation-call", span={"end_byte":4644,"end_column":1,"end_line":185,"start_byte":3720,"start_column":1,"start_line":168}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.layout_action", phase="implementation-call", span={"end_byte":4644,"end_column":1,"end_line":185,"start_byte":3720,"start_column":1,"start_line":168}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, LayoutState, path="$.return")
    _result = _cott_wrap_async_protocol(_result, LayoutState, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def visible_panes(layout: LayoutState) -> CottList[Pane]:
    """The panes shown, in Tab order. Normally Catalog (unless sidebar_hidden),
Editor, RunBar, Results. In full screen: Editor and RunBar when focus is
Editor or RunBar, else Results only."""
    layout = _cott_normalize_f32_abi(layout, LayoutState, path="$.layout")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/visible_panes.py", "ed77275b5f4c4305cd35a67599206316adb93ccfddcbba15fa22bd0607c6382e", "visible_panes", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.visible_panes")
        _result = _implementation(layout)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.visible_panes"
        if _error.span is None:
            _error.span = {"end_byte":4958,"end_column":1,"end_line":196,"start_byte":4644,"start_column":1,"start_line":185}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.visible_panes", phase="implementation-call", span={"end_byte":4958,"end_column":1,"end_line":196,"start_byte":4644,"start_column":1,"start_line":185}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.visible_panes", phase="implementation-call", span={"end_byte":4958,"end_column":1,"end_line":196,"start_byte":4644,"start_column":1,"start_line":185}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[Pane], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) >= 1)), "real.harlequin.ide.visible_panes", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.visible_panes", clause="ensures:1", phase="ensures", span={"end_byte":4940,"end_column":28,"end_line":192,"start_byte":4917,"start_column":5,"start_line":192}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Pane], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def new_run_bar(limit: Option[U64]) -> RunBar:
    """The Run Query Bar at startup: with a configured limit the checkbox is checked
and limit_text is its decimal text; otherwise unchecked with limit_text
"500". limit_cursor is at the end of limit_text; not running."""
    limit = _cott_normalize_f32_abi(limit, Option[U64], path="$.limit")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/new_run_bar.py", "bbcaae9e506bf31ae54175dbe675dc189727a864eb716ac8e3b2e9e0b264967a", "new_run_bar", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.new_run_bar")
        _result = _implementation(limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.new_run_bar"
        if _error.span is None:
            _error.span = {"end_byte":5297,"end_column":1,"end_line":207,"start_byte":4958,"start_column":1,"start_line":196}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.new_run_bar", phase="implementation-call", span={"end_byte":5297,"end_column":1,"end_line":207,"start_byte":4958,"start_column":1,"start_line":196}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.new_run_bar", phase="implementation-call", span={"end_byte":5297,"end_column":1,"end_line":207,"start_byte":4958,"start_column":1,"start_line":196}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, RunBar, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((not (_result).running)), "real.harlequin.ide.new_run_bar", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.new_run_bar", clause="ensures:1", phase="ensures", span={"end_byte":5279,"end_column":31,"end_line":203,"start_byte":5253,"start_column":5,"start_line":203}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, RunBar, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_bar_key(bar: RunBar, key: str, text: str) -> RunBarStep:
    """A key while the Run Query Bar has focus. "space" toggles the Limit checkbox
(a checked box requires a valid limit_text, otherwise it stays unchecked).
Digits insert at limit_cursor; "backspace"/"delete" edit; "left"/"right"/
"home"/"end" move the caret; after an edit the checkbox becomes checked when
limit_text is a nonempty whole number >= 0 and unchecked otherwise. "enter"
submits (submit true) when limit_text is valid and nonempty. Other keys do
nothing. submit is false unless stated."""
    bar = _cott_normalize_f32_abi(bar, RunBar, path="$.bar")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/run_bar_key.py", "7e14d26887faddbdbe1166957f6f15ae1e2836a006c223d0d7d913f87f932d9f", "run_bar_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.run_bar_key")
        _result = _implementation(bar, key, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.run_bar_key"
        if _error.span is None:
            _error.span = {"end_byte":5919,"end_column":1,"end_line":220,"start_byte":5297,"start_column":1,"start_line":207}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.run_bar_key", phase="implementation-call", span={"end_byte":5919,"end_column":1,"end_line":220,"start_byte":5297,"start_column":1,"start_line":207}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.run_bar_key", phase="implementation-call", span={"end_byte":5919,"end_column":1,"end_line":220,"start_byte":5297,"start_column":1,"start_line":207}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, RunBarStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, RunBarStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def effective_limit(bar: RunBar) -> Option[U64]:
    """The hard row limit a run uses: Some(int(limit_text)) when the checkbox is
checked and limit_text is a whole number >= 0, else Nothing."""
    bar = _cott_normalize_f32_abi(bar, RunBar, path="$.bar")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/effective_limit.py", "0699004ad61c51194910c20ab360fc1f7da295a5ab3f2184c0fefb099b625228", "effective_limit", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.effective_limit")
        _result = _implementation(bar)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.effective_limit"
        if _error.span is None:
            _error.span = {"end_byte":6147,"end_column":1,"end_line":228,"start_byte":5919,"start_column":1,"start_line":220}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.effective_limit", phase="implementation-call", span={"end_byte":6147,"end_column":1,"end_line":228,"start_byte":5919,"start_column":1,"start_line":220}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.effective_limit", phase="implementation-call", span={"end_byte":6147,"end_column":1,"end_line":228,"start_byte":5919,"start_column":1,"start_line":220}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[U64], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[U64], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_run_bar(bar: RunBar, transaction: Option[TransactionMode], can_cancel: bool, run_label: str, runnable: bool, focused: bool, width: U16) -> StyledLine:
    """The one-line Run Query Bar. Left: when transaction is Some, "[Tx: {label}]"
then " [🡅]" when can_commit and " [⮌]" when can_rollback, then a space. Then
"[x] Limit " or "[ ] Limit " followed by the limit_text padded to 7 cells
(style "class:hq.input", with " class:hq.cursor" when focused), right-aligned
at the end: "[ Cancel Query ]" (class:hq.button.focused) when bar.running
and can_cancel, "[ Running... ]" (class:hq.loading) when running otherwise,
else "[ {run_label} ]" (class:hq.button, or class:hq.muted when not
runnable). Other text uses class:hq.status. width is the terminal's
16-bit column count (POSIX winsize.ws_col); the line is exactly width cells
(padded with spaces, or cut)."""
    bar = _cott_normalize_f32_abi(bar, RunBar, path="$.bar")
    transaction = _cott_normalize_f32_abi(transaction, Option[TransactionMode], path="$.transaction")
    can_cancel = _cott_normalize_f32_abi(can_cancel, bool, path="$.can_cancel")
    run_label = _cott_normalize_f32_abi(run_label, str, path="$.run_label")
    runnable = _cott_normalize_f32_abi(runnable, bool, path="$.runnable")
    focused = _cott_normalize_f32_abi(focused, bool, path="$.focused")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_run_bar.py", "8f581a558c1b03fe647e74cce7a19d7094c961060c2b8e0c71d515d1ad8bb455", "render_run_bar", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_run_bar")
        _result = _implementation(bar, transaction, can_cancel, run_label, runnable, focused, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_run_bar"
        if _error.span is None:
            _error.span = {"end_byte":7087,"end_column":1,"end_line":244,"start_byte":6147,"start_column":1,"start_line":228}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_run_bar", phase="implementation-call", span={"end_byte":7087,"end_column":1,"end_line":244,"start_byte":6147,"start_column":1,"start_line":228}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_run_bar", phase="implementation-call", span={"end_byte":7087,"end_column":1,"end_line":244,"start_byte":6147,"start_column":1,"start_line":228}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledLine, path="$.return")
    _result = _cott_wrap_async_protocol(_result, StyledLine, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_label(selection: str, valid: bool) -> str:
    """The Run button caption: "Run Selection" when selection (the selected editor
text) is not blank and valid (the adapter accepted it, or cannot validate),
else "Run Query"."""
    selection = _cott_normalize_f32_abi(selection, str, path="$.selection")
    valid = _cott_normalize_f32_abi(valid, bool, path="$.valid")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/run_label.py", "083173b0e29c140c1c1ec2e9608ee54d45089313e0615438ebae3bc2ceed2f35", "run_label", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.run_label")
        _result = _implementation(selection, valid)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.run_label"
        if _error.span is None:
            _error.span = {"end_byte":7356,"end_column":1,"end_line":253,"start_byte":7087,"start_column":1,"start_line":244}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.run_label", phase="implementation-call", span={"end_byte":7356,"end_column":1,"end_line":253,"start_byte":7087,"start_column":1,"start_line":244}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.run_label", phase="implementation-call", span={"end_byte":7356,"end_column":1,"end_line":253,"start_byte":7087,"start_column":1,"start_line":244}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_tab_bar(labels: CottList[str], active: U64, width: U16) -> StyledLine:
    """A tab strip: each label as " {label} " styled "class:hq.tab.active" for the
active index and "class:hq.tab" otherwise, separated by nothing, cut at
the terminal's 16-bit column width and padded with spaces to that width."""
    labels = _cott_normalize_f32_abi(labels, CottList[str], path="$.labels")
    active = _cott_normalize_f32_abi(active, U64, path="$.active")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_tab_bar.py", "21ade5a4b6dfc301f7bbb1637630310737fe40589c11fef2b22d461a05c5529f", "render_tab_bar", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_tab_bar")
        _result = _implementation(labels, active, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_tab_bar"
        if _error.span is None:
            _error.span = {"end_byte":7703,"end_column":1,"end_line":262,"start_byte":7356,"start_column":1,"start_line":253}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_tab_bar", phase="implementation-call", span={"end_byte":7703,"end_column":1,"end_line":262,"start_byte":7356,"start_column":1,"start_line":253}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_tab_bar", phase="implementation-call", span={"end_byte":7703,"end_column":1,"end_line":262,"start_byte":7356,"start_column":1,"start_line":253}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledLine, path="$.return")
    _result = _cott_wrap_async_protocol(_result, StyledLine, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_footer(hints: CottList[FooterHint], width: U16) -> StyledLine:
    """The footer: for each hint " {key}" styled "class:hq.footer.key" followed by
" {description} " styled "class:hq.footer.description", cut at the terminal's
16-bit column width and padded with spaces styled "class:hq.footer"."""
    hints = _cott_normalize_f32_abi(hints, CottList[FooterHint], path="$.hints")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_footer.py", "b520dab68eca76d4575829264c4ef44e0758ae9764259b4437d72fb258ba7065", "render_footer", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_footer")
        _result = _implementation(hints, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_footer"
        if _error.span is None:
            _error.span = {"end_byte":8044,"end_column":1,"end_line":271,"start_byte":7703,"start_column":1,"start_line":262}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_footer", phase="implementation-call", span={"end_byte":8044,"end_column":1,"end_line":271,"start_byte":7703,"start_column":1,"start_line":262}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_footer", phase="implementation-call", span={"end_byte":8044,"end_column":1,"end_line":271,"start_byte":7703,"start_column":1,"start_line":262}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledLine, path="$.return")
    _result = _cott_wrap_async_protocol(_result, StyledLine, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def notify(title: Option[str], message: str, severity: Severity, now_ms: U64) -> Notification:
    """A notification shown for 5 seconds (10 seconds for Error), as Harlequin's
toasts: expires_at_ms is now_ms + 5000 or + 10000, saturated at the U64
maximum 18446744073709551615. Saturation preserves the timestamp's ABI
when the caller supplies a monotonic clock reading near its upper bound."""
    title = _cott_normalize_f32_abi(title, Option[str], path="$.title")
    message = _cott_normalize_f32_abi(message, str, path="$.message")
    severity = _cott_normalize_f32_abi(severity, Severity, path="$.severity")
    now_ms = _cott_normalize_f32_abi(now_ms, U64, path="$.now_ms")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/notify.py", "c3368d5895e859b23adef482704513a252b7ef5c9f6a462a8fe4967b46941d80", "notify", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.notify")
        _result = _implementation(title, message, severity, now_ms)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.notify"
        if _error.span is None:
            _error.span = {"end_byte":8563,"end_column":1,"end_line":284,"start_byte":8044,"start_column":1,"start_line":271}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.notify", phase="implementation-call", span={"end_byte":8563,"end_column":1,"end_line":284,"start_byte":8044,"start_column":1,"start_line":271}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.notify", phase="implementation-call", span={"end_byte":8563,"end_column":1,"end_line":284,"start_byte":8044,"start_column":1,"start_line":271}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Notification, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).message == message)), "real.harlequin.ide.notify", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.notify", clause="ensures:1", phase="ensures", span={"end_byte":8502,"end_column":38,"end_line":279,"start_byte":8469,"start_column":5,"start_line":279}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).expires_at_ms >= now_ms)), "real.harlequin.ide.notify", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.notify", clause="ensures:2", phase="ensures", span={"end_byte":8545,"end_column":43,"end_line":280,"start_byte":8507,"start_column":5,"start_line":280}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Notification, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_notifications(notifications: CottList[Notification], now_ms: U64, width: U64) -> CottList[StyledLine]:
    """The unexpired notifications (expires_at_ms > now_ms), newest last, each as
its title line (when Some, bold via class:hq.dialog.title) and its message
lines, every line prefixed with "▌ " and styled "class:hq.notification" (or
"class:hq.notification.error" for Error, "class:hq.warning" prefix for
Warning), wrapped at width - 2 cells, with a blank line between
notifications. At most the last 3 notifications are shown."""
    notifications = _cott_normalize_f32_abi(notifications, CottList[Notification], path="$.notifications")
    now_ms = _cott_normalize_f32_abi(now_ms, U64, path="$.now_ms")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_notifications.py", "d45e0e91c9d65833aa100e1ec4eb7485b09045e762ab630edb7b832151dda52f", "render_notifications", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_notifications")
        _result = _implementation(notifications, now_ms, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_notifications"
        if _error.span is None:
            _error.span = {"end_byte":9151,"end_column":1,"end_line":296,"start_byte":8563,"start_column":1,"start_line":284}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_notifications", phase="implementation-call", span={"end_byte":9151,"end_column":1,"end_line":296,"start_byte":8563,"start_column":1,"start_line":284}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_notifications", phase="implementation-call", span={"end_byte":9151,"end_column":1,"end_line":296,"start_byte":8563,"start_column":1,"start_line":284}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def text_modal(title: str, header: str, body: str, footer: str, copy_notice: str) -> TextModal:
    """A copyable text dialog showing body (split into lines on LF), scrolled to
the top, whose copy_text is body. It closes on any key other than scroll
keys and "c"."""
    title = _cott_normalize_f32_abi(title, str, path="$.title")
    header = _cott_normalize_f32_abi(header, str, path="$.header")
    body = _cott_normalize_f32_abi(body, str, path="$.body")
    footer = _cott_normalize_f32_abi(footer, str, path="$.footer")
    copy_notice = _cott_normalize_f32_abi(copy_notice, str, path="$.copy_notice")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/text_modal.py", "32977ba5ac09ee186bd15d9ec1b3df46358df51f1b77d832f76d088aecf2e109", "text_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.text_modal")
        _result = _implementation(title, header, body, footer, copy_notice)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.text_modal"
        if _error.span is None:
            _error.span = {"end_byte":9508,"end_column":1,"end_line":307,"start_byte":9151,"start_column":1,"start_line":296}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.text_modal", phase="implementation-call", span={"end_byte":9508,"end_column":1,"end_line":307,"start_byte":9151,"start_column":1,"start_line":296}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.text_modal", phase="implementation-call", span={"end_byte":9508,"end_column":1,"end_line":307,"start_byte":9151,"start_column":1,"start_line":296}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextModal, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((((_result).scroll == 0) and (_result).copyable)), "real.harlequin.ide.text_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.text_modal", clause="ensures:1", phase="ensures", span={"end_byte":9490,"end_column":51,"end_line":303,"start_byte":9444,"start_column":5,"start_line":303}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TextModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def cell_modal(column: str, value: str) -> TextModal:
    """The View Cell dialog: title column (or "Cell Contents" when column is ""),
header "", body value, footer "Arrows/PgUp/PgDn scroll. Click text or press c
to copy. Any other key closes.", copy notice "Cell value copied to
clipboard."."""
    column = _cott_normalize_f32_abi(column, str, path="$.column")
    value = _cott_normalize_f32_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/cell_modal.py", "8cb1468ec28ee937b64387c1b108fb3ffe1b7230c9098a8058a1d1c7041818e0", "cell_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.cell_modal")
        _result = _implementation(column, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.cell_modal"
        if _error.span is None:
            _error.span = {"end_byte":9876,"end_column":1,"end_line":319,"start_byte":9508,"start_column":1,"start_line":307}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.cell_modal", phase="implementation-call", span={"end_byte":9876,"end_column":1,"end_line":319,"start_byte":9508,"start_column":1,"start_line":307}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.cell_modal", phase="implementation-call", span={"end_byte":9876,"end_column":1,"end_line":319,"start_byte":9508,"start_column":1,"start_line":307}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextModal, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((_result).copyable), "real.harlequin.ide.cell_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.cell_modal", clause="ensures:1", phase="ensures", span={"end_byte":9858,"end_column":28,"end_line":315,"start_byte":9835,"start_column":5,"start_line":315}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TextModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def error_modal(title: str, header: str, message: str) -> TextModal:
    """An error dialog (Query Error, Export Data Error, Catalog Error, ...): the
given title and header, body message, footer "Arrows/PgUp/PgDn scroll. Click
text or press c to copy. Any other key closes.", copy notice "Error copied to
clipboard."."""
    title = _cott_normalize_f32_abi(title, str, path="$.title")
    header = _cott_normalize_f32_abi(header, str, path="$.header")
    message = _cott_normalize_f32_abi(message, str, path="$.message")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/error_modal.py", "a83a8ccea1b9fac822fd5d0acf5a2f331b11da61acff5c667b32048221fa252a", "error_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.error_modal")
        _result = _implementation(title, header, message)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.error_modal"
        if _error.span is None:
            _error.span = {"end_byte":10302,"end_column":1,"end_line":331,"start_byte":9876,"start_column":1,"start_line":319}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.error_modal", phase="implementation-call", span={"end_byte":10302,"end_column":1,"end_line":331,"start_byte":9876,"start_column":1,"start_line":319}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.error_modal", phase="implementation-call", span={"end_byte":10302,"end_column":1,"end_line":331,"start_byte":9876,"start_column":1,"start_line":319}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextModal, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((((_result).title == title) and ((_result).header == header))), "real.harlequin.ide.error_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.error_modal", clause="ensures:1", phase="ensures", span={"end_byte":10284,"end_column":62,"end_line":327,"start_byte":10227,"start_column":5,"start_line":327}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TextModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def help_modal(key_lines: CottList[str]) -> TextModal:
    """The help screen (F1): title "Harlequin Help", header "Welcome to Harlequin!
This screen contains a small subset of the online docs, available at
https://harlequin.sh/docs/getting-started", body = the key reference lines
(key_lines, from real.harlequin.keymap.help_lines), a blank line, then the
lines of help_markdown(); footer "Scroll with arrows. Press any other key to
continue."; not copyable; closes on any non-scroll key."""
    key_lines = _cott_normalize_f32_abi(key_lines, CottList[str], path="$.key_lines")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/help_modal.py", "93d7a8eef68cd16dd2abdf0dbffaa4e3d22635b3615d4e20a9832f2c3d825740", "help_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.help_modal")
        _result = _implementation(key_lines)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.help_modal"
        if _error.span is None:
            _error.span = {"end_byte":10874,"end_column":1,"end_line":345,"start_byte":10302,"start_column":1,"start_line":331}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.help_modal", phase="implementation-call", span={"end_byte":10874,"end_column":1,"end_line":345,"start_byte":10302,"start_column":1,"start_line":331}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.help_modal", phase="implementation-call", span={"end_byte":10874,"end_column":1,"end_line":345,"start_byte":10302,"start_column":1,"start_line":331}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextModal, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((not (_result).copyable)), "real.harlequin.ide.help_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.help_modal", clause="ensures:1", phase="ensures", span={"end_byte":10856,"end_column":32,"end_line":341,"start_byte":10829,"start_column":5,"start_line":341}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TextModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def help_markdown() -> str:
    """Harlequin's bundled help text (help_screen.md of Harlequin 2.15.0), exactly
these sections in order, as Markdown: "### Using Harlequin with DuckDB"
(default adapter; `harlequin "path/to/duck.db" "another_duck.db"`; no
arguments for in-memory; see the Troubleshooting page
https://harlequin.sh/docs/troubleshooting/duckdb-version-mismatch to control
the DuckDB version), "### Using Harlequin with SQLite and Other Adapters"
(`harlequin -a sqlite "path/to/sqlite.db" "another_sqlite.db"`, `harlequin -a
sqlite` for in-memory, other adapters listed at
https://harlequin.sh/docs/adapters), "### Getting Help" (`harlequin --help`,
https://harlequin.sh/docs/troubleshooting/index, GitHub Issues
https://github.com/tconbeer/harlequin/issues for bugs, GitHub Discussions
https://github.com/tconbeer/harlequin/discussions for other issues), "###
Viewing Files" (`--show-files`/`-f` with an absolute path example
`harlequin --show-files /path/to/my/data` and `harlequin -f .`; remote
objects: https://harlequin.sh/docs/files/remote), "### Using Config Files"
(https://harlequin.sh/docs/config-file), "### Changing Key Bindings"
(keymaps from plug-ins or TOML config files,
https://harlequin.sh/docs/keymaps) and "### Managing Transactions"
(transaction modes, https://harlequin.sh/docs/transactions), each with the
upstream paragraphs and fenced bash examples."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/help_markdown.py", "5a6674928bceeaa0949250e2d304c70c70c1fc2439e25ba466ba7fbaa49c9b94", "help_markdown", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.help_markdown")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.help_markdown"
        if _error.span is None:
            _error.span = {"end_byte":12439,"end_column":1,"end_line":373,"start_byte":10874,"start_column":1,"start_line":345}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.help_markdown", phase="implementation-call", span={"end_byte":12439,"end_column":1,"end_line":373,"start_byte":10874,"start_column":1,"start_line":345}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.help_markdown", phase="implementation-call", span={"end_byte":12439,"end_column":1,"end_line":373,"start_byte":10874,"start_column":1,"start_line":345}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "### Using Harlequin with DuckDB")), "real.harlequin.ide.help_markdown", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.help_markdown", clause="ensures:1", phase="ensures", span={"end_byte":12421,"end_column":69,"end_line":369,"start_byte":12357,"start_column":5,"start_line":369}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def debug_modal(sections: CottList[DebugSection]) -> TextModal:
    """The debug screen (F12): title "Debug Information", header "Details about the
current Harlequin session, environment, and adapter.", body: for each section
a line "## {title}", its body lines and a blank line; footer "Tab/Shift Tab to
move focus, Enter to expand/collapse, Esc to close."; copyable (copy_text is
the body, notice "Copied to clipboard."); closes only on "escape"."""
    sections = _cott_normalize_f32_abi(sections, CottList[DebugSection], path="$.sections")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/debug_modal.py", "384dc391319f4df80a34e8ff47a68da1289b33ef32426fcd4efc3ebd16f73d5d", "debug_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.debug_modal")
        _result = _implementation(sections)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.debug_modal"
        if _error.span is None:
            _error.span = {"end_byte":12962,"end_column":1,"end_line":386,"start_byte":12439,"start_column":1,"start_line":373}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.debug_modal", phase="implementation-call", span={"end_byte":12962,"end_column":1,"end_line":386,"start_byte":12439,"start_column":1,"start_line":373}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.debug_modal", phase="implementation-call", span={"end_byte":12962,"end_column":1,"end_line":386,"start_byte":12439,"start_column":1,"start_line":373}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextModal, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((_result).copyable), "real.harlequin.ide.debug_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.debug_modal", clause="ensures:1", phase="ensures", span={"end_byte":12944,"end_column":28,"end_line":382,"start_byte":12921,"start_column":5,"start_line":382}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TextModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def text_modal_key(modal: TextModal, key: str, visible_lines: U64) -> TextModalStep:
    """A key in a text dialog: "up"/"down" scroll one line, "pageup"/"pagedown" by
max(visible_lines - 1, 1), "home"/"end" to the top/bottom, clamped so the
last page stays full (scroll <= max(lines.len - visible_lines, 0)); these
Stay. "c" when copyable is Copy(copy_text, copy_notice). "escape" is Close.
Any other key is Close when close_on_any_key, else Stay."""
    modal = _cott_normalize_f32_abi(modal, TextModal, path="$.modal")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    visible_lines = _cott_normalize_f32_abi(visible_lines, U64, path="$.visible_lines")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/text_modal_key.py", "6151617b36beff54d16a66de93e4aa0a2a21497279f8602781dc69d3a69afa28", "text_modal_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.text_modal_key")
        _result = _implementation(modal, key, visible_lines)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.text_modal_key"
        if _error.span is None:
            _error.span = {"end_byte":13460,"end_column":1,"end_line":397,"start_byte":12962,"start_column":1,"start_line":386}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.text_modal_key", phase="implementation-call", span={"end_byte":13460,"end_column":1,"end_line":397,"start_byte":12962,"start_column":1,"start_line":386}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.text_modal_key", phase="implementation-call", span={"end_byte":13460,"end_column":1,"end_line":397,"start_byte":12962,"start_column":1,"start_line":386}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextModalStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, TextModalStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_text_modal(modal: TextModal, width: U64, height: U64) -> CottList[StyledLine]:
    """Draw a text dialog of width x height cells: line 1 the title
(class:hq.dialog.title), then the header wrapped at width
(class:hq.dialog) when not "", then available body lines from scroll
(class:hq.text, cut at width), then the footer (class:hq.muted). Return
at most height actual-content lines; never pad the body with blank rows
to reach height. The terminal widget paints unused space. In particular,
when no header is present the result has at most the title, the existing
body lines and the footer, independent of height."""
    modal = _cott_normalize_f32_abi(modal, TextModal, path="$.modal")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    height = _cott_normalize_f32_abi(height, U64, path="$.height")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_text_modal.py", "5a83223c8e68c5cff238cfd6f93a0bcaedb32cd636d0035ab55c5f23adccf1ad", "render_text_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_text_modal")
        _result = _implementation(modal, width, height)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_text_modal"
        if _error.span is None:
            _error.span = {"end_byte":14244,"end_column":1,"end_line":414,"start_byte":13460,"start_column":1,"start_line":397}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_text_modal", phase="implementation-call", span={"end_byte":14244,"end_column":1,"end_line":414,"start_byte":13460,"start_column":1,"start_line":397}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_text_modal", phase="implementation-call", span={"end_byte":14244,"end_column":1,"end_line":414,"start_byte":13460,"start_column":1,"start_line":397}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= height)), "real.harlequin.ide.render_text_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.render_text_modal", clause="ensures:1", phase="ensures", span={"end_byte":14158,"end_column":33,"end_line":409,"start_byte":14130,"start_column":5,"start_line":409}, expected="true", actual="false")
        if not (_cott_contract_condition((((not ((modal).header == "")) or (len(_result) <= (len((modal).lines) + 2)))), "real.harlequin.ide.render_text_modal", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.render_text_modal", clause="ensures:2", phase="ensures", span={"end_byte":14226,"end_column":68,"end_line":410,"start_byte":14163,"start_column":5,"start_line":410}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def confirm_key(modal: ConfirmModal, key: str) -> ConfirmStep:
    """A key in a Yes/No dialog: "left"/"right"/"tab"/"shift+tab" toggle
yes_selected (Stay); "enter" answers the highlighted button; "y" is Yes; "n"
and "escape" are No; other keys Stay."""
    modal = _cott_normalize_f32_abi(modal, ConfirmModal, path="$.modal")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/confirm_key.py", "ac272d620bfc5f6518cbe104b2fdcd424f3ac6af795960421aec2e773d8d5081", "confirm_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.confirm_key")
        _result = _implementation(modal, key)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.confirm_key"
        if _error.span is None:
            _error.span = {"end_byte":14536,"end_column":1,"end_line":423,"start_byte":14244,"start_column":1,"start_line":414}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.confirm_key", phase="implementation-call", span={"end_byte":14536,"end_column":1,"end_line":423,"start_byte":14244,"start_column":1,"start_line":414}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.confirm_key", phase="implementation-call", span={"end_byte":14536,"end_column":1,"end_line":423,"start_byte":14244,"start_column":1,"start_line":414}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ConfirmStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, ConfirmStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_confirm(modal: ConfirmModal, width: U64) -> CottList[StyledLine]:
    """The prompt wrapped at width (class:hq.dialog), a blank line, then the buttons
"[ No ]" and "[ Yes ]" separated by two spaces, the highlighted one styled
class:hq.button.focused and the other class:hq.button."""
    modal = _cott_normalize_f32_abi(modal, ConfirmModal, path="$.modal")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_confirm.py", "8baf9aa91c8d689d7cafaa2ec121a567007ca129ebc096ef40e32c9da501b24e", "render_confirm", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_confirm")
        _result = _implementation(modal, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_confirm"
        if _error.span is None:
            _error.span = {"end_byte":14865,"end_column":1,"end_line":432,"start_byte":14536,"start_column":1,"start_line":423}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_confirm", phase="implementation-call", span={"end_byte":14865,"end_column":1,"end_line":432,"start_byte":14536,"start_column":1,"start_line":423}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_confirm", phase="implementation-call", span={"end_byte":14865,"end_column":1,"end_line":432,"start_byte":14536,"start_column":1,"start_line":423}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def input_modal(purpose: InputPurpose, value: str) -> InputModal:
    """An input dialog: Find has title "Find" and placeholder "Search text";
GoToLine "Go To Line" and "Line number"; OpenFile "Open Query" and
"/path/to/file.sql (tab autocompletes, enter opens, esc cancels)"; SaveFile
"Save Query" and "/path/to/file.sql (tab autocompletes, enter saves, esc
cancels)". value is the initial text with the caret at its end; message ""
and no completions."""
    purpose = _cott_normalize_f32_abi(purpose, InputPurpose, path="$.purpose")
    value = _cott_normalize_f32_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/input_modal.py", "8220a3aed570593e3eaf1014f76671e225a70c3e5bd522833e7c7cc8f6032dc8", "input_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.input_modal")
        _result = _implementation(purpose, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.input_modal"
        if _error.span is None:
            _error.span = {"end_byte":15437,"end_column":1,"end_line":446,"start_byte":14865,"start_column":1,"start_line":432}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.input_modal", phase="implementation-call", span={"end_byte":15437,"end_column":1,"end_line":446,"start_byte":14865,"start_column":1,"start_line":432}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.input_modal", phase="implementation-call", span={"end_byte":15437,"end_column":1,"end_line":446,"start_byte":14865,"start_column":1,"start_line":432}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, InputModal, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((((_result).purpose == purpose) and ((_result).value == value))), "real.harlequin.ide.input_modal", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.input_modal", clause="ensures:1", phase="ensures", span={"end_byte":15419,"end_column":64,"end_line":442,"start_byte":15360,"start_column":5,"start_line":442}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, InputModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def input_key(modal: InputModal, key: str, text: str) -> InputStep:
    """A key in an input dialog. Printable text inserts at cursor;
"backspace"/"delete" edit; "left"/"right"/"home"/"end" move the caret (all
clear message and completions, Stay). "escape" is Cancel. "tab" for OpenFile
and SaveFile is Complete(value) (the caller supplies completions with
apply_completions); for other purposes Stay. "enter": an empty value sets
message "Please enter a value." (Stay); for GoToLine a value that is not a
whole number >= 1 sets message "Please enter a line number." (Stay);
otherwise Submit(value)."""
    modal = _cott_normalize_f32_abi(modal, InputModal, path="$.modal")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/input_key.py", "48abc11d888a3aa13364aaa8973fad8ac604f0f0c008e95bc631906939a499e5", "input_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.input_key")
        _result = _implementation(modal, key, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.input_key"
        if _error.span is None:
            _error.span = {"end_byte":16098,"end_column":1,"end_line":460,"start_byte":15437,"start_column":1,"start_line":446}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.input_key", phase="implementation-call", span={"end_byte":16098,"end_column":1,"end_line":460,"start_byte":15437,"start_column":1,"start_line":446}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.input_key", phase="implementation-call", span={"end_byte":16098,"end_column":1,"end_line":460,"start_byte":15437,"start_column":1,"start_line":446}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, InputStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, InputStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def apply_completions(modal: InputModal, completions: CottList[str]) -> InputModal:
    """After a Tab in a path input: with exactly one completion, value becomes it
and the caret moves to its end; with several, value becomes their longest
common prefix when that is longer than value, and completions lists them;
with none, message becomes "No matching files." ."""
    modal = _cott_normalize_f32_abi(modal, InputModal, path="$.modal")
    completions = _cott_normalize_f32_abi(completions, CottList[str], path="$.completions")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/apply_completions.py", "b1b3d8187a1e47ee9f0de3729d97d03e4d9244a4f17febccc3305ae77ae221fe", "apply_completions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.apply_completions")
        _result = _implementation(modal, completions)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.apply_completions"
        if _error.span is None:
            _error.span = {"end_byte":16503,"end_column":1,"end_line":470,"start_byte":16098,"start_column":1,"start_line":460}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.apply_completions", phase="implementation-call", span={"end_byte":16503,"end_column":1,"end_line":470,"start_byte":16098,"start_column":1,"start_line":460}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.apply_completions", phase="implementation-call", span={"end_byte":16503,"end_column":1,"end_line":470,"start_byte":16098,"start_column":1,"start_line":460}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, InputModal, path="$.return")
    _result = _cott_wrap_async_protocol(_result, InputModal, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_input_modal(modal: InputModal, width: U64) -> CottList[StyledLine]:
    """The title (class:hq.dialog.title), the input line showing value (or the
placeholder in class:hq.muted when empty) with the caret cell styled
class:hq.cursor, the message (class:hq.error) when not "", then up to 8
completions (class:hq.muted), cut at width."""
    modal = _cott_normalize_f32_abi(modal, InputModal, path="$.modal")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_input_modal.py", "ea35ca40fdf8375a7410318cf5a8f89d7dadab7e51d406d8e6745db330ecb53e", "render_input_modal", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_input_modal")
        _result = _implementation(modal, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_input_modal"
        if _error.span is None:
            _error.span = {"end_byte":16887,"end_column":1,"end_line":480,"start_byte":16503,"start_column":1,"start_line":470}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_input_modal", phase="implementation-call", span={"end_byte":16887,"end_column":1,"end_line":480,"start_byte":16503,"start_column":1,"start_line":470}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_input_modal", phase="implementation-call", span={"end_byte":16887,"end_column":1,"end_line":480,"start_byte":16503,"start_column":1,"start_line":470}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def context_menu(entry: CatalogEntry, interactions: CottList[str]) -> ContextMenu:
    """The context menu for entry: items "Insert Name at Cursor" followed by
interactions (from real.harlequin.adapters.catalog_interactions), selected 0."""
    entry = _cott_normalize_f32_abi(entry, CatalogEntry, path="$.entry")
    interactions = _cott_normalize_f32_abi(interactions, CottList[str], path="$.interactions")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/context_menu.py", "333ed55154b222e2f30b6ffaf793394db28a788b6203374629228a9d92e080d0", "context_menu", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.context_menu")
        _result = _implementation(entry, interactions)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.context_menu"
        if _error.span is None:
            _error.span = {"end_byte":17245,"end_column":1,"end_line":491,"start_byte":16887,"start_column":1,"start_line":480}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.context_menu", phase="implementation-call", span={"end_byte":17245,"end_column":1,"end_line":491,"start_byte":16887,"start_column":1,"start_line":480}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.context_menu", phase="implementation-call", span={"end_byte":17245,"end_column":1,"end_line":491,"start_byte":16887,"start_column":1,"start_line":480}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ContextMenu, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).items) == (len(interactions) + 1))), "real.harlequin.ide.context_menu", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.context_menu", clause="ensures:1", phase="ensures", span={"end_byte":17194,"end_column":53,"end_line":486,"start_byte":17146,"start_column":5,"start_line":486}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).selected == 0)), "real.harlequin.ide.context_menu", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.context_menu", clause="ensures:2", phase="ensures", span={"end_byte":17227,"end_column":33,"end_line":487,"start_byte":17199,"start_column":5,"start_line":487}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ContextMenu, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def context_menu_key(menu: ContextMenu, key: str) -> ContextMenuStep:
    """"up"/"down" move the highlight (clamped); "enter" is Choose(items[selected]);
"escape" (and "full_stop") is Close; other keys Stay."""
    menu = _cott_normalize_f32_abi(menu, ContextMenu, path="$.menu")
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/context_menu_key.py", "564a0b461baf02cad8f335ec4ca71e3c20cb0c8ae55948d0b1c54beb96d01918", "context_menu_key", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.context_menu_key")
        _result = _implementation(menu, key)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.context_menu_key"
        if _error.span is None:
            _error.span = {"end_byte":17491,"end_column":1,"end_line":499,"start_byte":17245,"start_column":1,"start_line":491}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.context_menu_key", phase="implementation-call", span={"end_byte":17491,"end_column":1,"end_line":499,"start_byte":17245,"start_column":1,"start_line":491}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.context_menu_key", phase="implementation-call", span={"end_byte":17491,"end_column":1,"end_line":499,"start_byte":17245,"start_column":1,"start_line":491}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ContextMenuStep, path="$.return")
    _result = _cott_wrap_async_protocol(_result, ContextMenuStep, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_context_menu(menu: ContextMenu, width: U16) -> CottList[StyledLine]:
    """At most 10 item lines, scrolled so selected is visible, each " {item} " padded
to the terminal's 16-bit column width (class:hq.dialog, plus
" class:hq.cursor" on the highlighted item)."""
    menu = _cott_normalize_f32_abi(menu, ContextMenu, path="$.menu")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/ide/render_context_menu.py", "ded6ff5dffd083cc86cdcf09095038b7468b794b48df0a8fe8771c5472b3cd01", "render_context_menu", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.ide.render_context_menu")
        _result = _implementation(menu, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.ide.render_context_menu"
        if _error.span is None:
            _error.span = {"end_byte":17830,"end_column":1,"end_line":510,"start_byte":17491,"start_column":1,"start_line":499}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.ide.render_context_menu", phase="implementation-call", span={"end_byte":17830,"end_column":1,"end_line":510,"start_byte":17491,"start_column":1,"start_line":499}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.ide.render_context_menu", phase="implementation-call", span={"end_byte":17830,"end_column":1,"end_line":510,"start_byte":17491,"start_column":1,"start_line":499}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledLine], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= 10)), "real.harlequin.ide.render_context_menu", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.ide.render_context_menu", clause="ensures:1", phase="ensures", span={"end_byte":17812,"end_column":29,"end_line":506,"start_byte":17788,"start_column":5,"start_line":506}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledLine], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["ConfirmModal", "ConfirmOutcome", "ConfirmOutcome_No", "ConfirmOutcome_Stay", "ConfirmOutcome_Yes", "ConfirmStep", "ContextMenu", "ContextMenuOutcome", "ContextMenuOutcome_Choose", "ContextMenuOutcome_Close", "ContextMenuOutcome_Stay", "ContextMenuStep", "DebugSection", "InputModal", "InputOutcome", "InputOutcome_Cancel", "InputOutcome_Complete", "InputOutcome_Stay", "InputOutcome_Submit", "InputPurpose", "InputPurpose_Find", "InputPurpose_GoToLine", "InputPurpose_OpenFile", "InputPurpose_SaveFile", "InputStep", "LayoutState", "Notification", "Pane", "Pane_Catalog", "Pane_Editor", "Pane_Results", "Pane_RunBar", "RunBar", "RunBarStep", "Severity", "Severity_Error", "Severity_Information", "Severity_Warning", "TextModal", "TextModalOutcome", "TextModalOutcome_Close", "TextModalOutcome_Copy", "TextModalOutcome_Stay", "TextModalStep", "apply_completions", "cell_modal", "confirm_key", "context_menu", "context_menu_key", "debug_modal", "effective_limit", "error_modal", "help_markdown", "help_modal", "initial_layout", "input_key", "input_modal", "layout_action", "new_run_bar", "notify", "render_confirm", "render_context_menu", "render_footer", "render_input_modal", "render_notifications", "render_run_bar", "render_tab_bar", "render_text_modal", "run_bar_key", "run_label", "text_modal", "text_modal_key", "visible_panes"]
