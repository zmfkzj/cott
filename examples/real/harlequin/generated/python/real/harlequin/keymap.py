from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_unique_by

from real.harlequin.keymap_types import ActionScope, ActionScope_App, ActionScope_Catalog, ActionScope_ContextMenu, ActionScope_Editor, ActionScope_History, ActionScope_Results, ActionSpec, BoundKey, BoundKeySet, FooterHint, KeyBinding, KeyMap, KeymapError, KeymapError_EmptyKey, KeymapError_UnknownAction, KeymapError_UnknownKeymap

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def harlequin_actions(scope: ActionScope) -> CottList[ActionSpec]:
    """The actions of the given scope, in table order: the rows of the table below
whose scope column names scope, each with position = its 0-based row index
in the whole table (quit is 0, the last History action is 116). The table
lists every action Harlequin 2.15.0 binds, in upstream order (15 App, 53
Editor, 11 Catalog, 1 ContextMenu, 34 Results, 3 History). Columns: name |
scope | description | show ("show" means true, "-" false) | priority
("priority" means true, "-" false). Actions are returned per scope so that
no single value crosses the facade boundary with all 117 specs.
quit | App | Quit | show | priority
help | App | Help | show | -
focus_next | App | Focus Next | - | -
focus_previous | App | Focus Previous | - | -
focus_query_editor | App | Focus Query Editor | - | -
focus_results_viewer | App | Focus Results Viewer | - | -
focus_data_catalog | App | Focus Data Catalog | - | -
toggle_sidebar | App | Toggle Sidebar | - | -
toggle_full_screen | App | Toggle Full Screen | - | -
show_debug_info | App | Debug Info | - | -
show_query_history | App | History | show | -
show_data_exporter | App | Export Data | - | -
refresh_catalog | App | Refresh Data Catalog | - | -
run_query | App | Run Query | - | -
cancel_query | App | Cancel Query | - | -
code_editor.new_buffer | Editor | New Buffer | - | -
code_editor.close_buffer | Editor | Close Buffer | - | -
code_editor.next_buffer | Editor | Next Buffer | - | -
code_editor.run_query | Editor | Run Query | show | -
code_editor.format_buffer | Editor | Format Query | show | -
code_editor.save_buffer | Editor | Save Query | show | -
code_editor.load_buffer | Editor | Open Query | show | -
code_editor.launch_external_editor | Editor | Launch External Editor | - | -
code_editor.find | Editor | Find | show | -
code_editor.find_next | Editor | Find Next | show | -
code_editor.goto_line | Editor | Go To Line | show | -
code_editor.cursor_up | Editor | Cursor Up | - | -
code_editor.cursor_down | Editor | Cursor Down | - | -
code_editor.cursor_left | Editor | Cursor Left | - | -
code_editor.cursor_right | Editor | Cursor Right | - | -
code_editor.cursor_word_left | Editor | Cursor Word Left | - | -
code_editor.cursor_word_right | Editor | Cursor Word Right | - | -
code_editor.cursor_line_start | Editor | Cursor Line Start | - | -
code_editor.cursor_line_end | Editor | Cursor Line End | - | -
code_editor.cursor_doc_start | Editor | Cursor Doc Start | - | -
code_editor.cursor_doc_end | Editor | Cursor Doc End | - | -
code_editor.cursor_page_up | Editor | Cursor Page Up | - | -
code_editor.cursor_page_down | Editor | Cursor Page Down | - | -
code_editor.select_up | Editor | Select Up | - | -
code_editor.select_down | Editor | Select Down | - | -
code_editor.select_left | Editor | Select Left | - | -
code_editor.select_right | Editor | Select Right | - | -
code_editor.select_word_left | Editor | Select Word Left | - | -
code_editor.select_word_right | Editor | Select Word Right | - | -
code_editor.select_line_start | Editor | Select Line Start | - | -
code_editor.select_line_end | Editor | Select Line End | - | -
code_editor.select_doc_start | Editor | Select Doc Start | - | -
code_editor.select_doc_end | Editor | Select Doc End | - | -
code_editor.select_word | Editor | Select Word | - | -
code_editor.select_line | Editor | Select Line | - | -
code_editor.select_all | Editor | Select All | - | -
code_editor.scroll_up_one | Editor | Scroll Up One | - | -
code_editor.scroll_down_one | Editor | Scroll Down One | - | -
code_editor.toggle_comment | Editor | Toggle Comment | - | -
code_editor.cut | Editor | Cut | - | -
code_editor.copy | Editor | Copy | - | -
code_editor.paste | Editor | Paste | - | -
code_editor.undo | Editor | Undo | - | -
code_editor.redo | Editor | Redo | - | -
code_editor.delete_left | Editor | Delete Left | - | -
code_editor.delete_right | Editor | Delete Right | - | -
code_editor.delete_word_left | Editor | Delete Word Left | - | -
code_editor.delete_word_right | Editor | Delete Word Right | - | -
code_editor.delete_line | Editor | Delete Line | - | -
code_editor.delete_to_start_of_line | Editor | Delete To Start Of Line | - | -
code_editor.delete_to_end_of_line | Editor | Delete To End Of Line | - | -
code_editor.focus_results_viewer | Editor | Focus Results Viewer | - | -
code_editor.focus_data_catalog | Editor | Focus Data Catalog | - | -
data_catalog.previous_tab | Catalog | Previous Tab | - | -
data_catalog.next_tab | Catalog | Next Tab | - | -
data_catalog.insert_name | Catalog | Insert Name | show | -
data_catalog.copy_name | Catalog | Copy Name | - | -
data_catalog.select_cursor | Catalog | Select Cursor | - | -
data_catalog.toggle_node | Catalog | Toggle Node | - | -
data_catalog.cursor_up | Catalog | Cursor Up | - | -
data_catalog.cursor_down | Catalog | Cursor Down | - | -
data_catalog.focus_query_editor | Catalog | Focus Query Editor | - | -
data_catalog.focus_results_viewer | Catalog | Focus Results Viewer | - | -
data_catalog.show_context_menu | Catalog | Show Context Menu | show | -
data_catalog.hide_context_menu | ContextMenu | Hide Context Menu | - | -
results_viewer.previous_tab | Results | Previous Tab | - | -
results_viewer.next_tab | Results | Next Tab | - | -
results_viewer.copy_selection | Results | Copy Selection | - | -
results_viewer.view_cell | Results | View Cell | - | -
results_viewer.select_cursor | Results | Select Cursor | - | -
results_viewer.cursor_up | Results | Cursor Up | - | -
results_viewer.cursor_down | Results | Cursor Down | - | -
results_viewer.cursor_left | Results | Cursor Left | - | -
results_viewer.cursor_right | Results | Cursor Right | - | -
results_viewer.cursor_row_start | Results | Cursor Row Start | - | -
results_viewer.cursor_row_end | Results | Cursor Row End | - | -
results_viewer.cursor_column_start | Results | Cursor Column Start | - | -
results_viewer.cursor_column_end | Results | Cursor Column End | - | -
results_viewer.cursor_next_cell | Results | Cursor Next Cell | - | -
results_viewer.cursor_previous_cell | Results | Cursor Previous Cell | - | -
results_viewer.cursor_page_up | Results | Cursor Page Up | - | -
results_viewer.cursor_page_down | Results | Cursor Page Down | - | -
results_viewer.cursor_table_start | Results | Cursor Table Start | - | -
results_viewer.cursor_table_end | Results | Cursor Table End | - | -
results_viewer.select_up | Results | Select Up | - | -
results_viewer.select_down | Results | Select Down | - | -
results_viewer.select_left | Results | Select Left | - | -
results_viewer.select_right | Results | Select Right | - | -
results_viewer.select_row_start | Results | Select Row Start | - | -
results_viewer.select_row_end | Results | Select Row End | - | -
results_viewer.select_column_start | Results | Select Column Start | - | -
results_viewer.select_column_end | Results | Select Column End | - | -
results_viewer.select_page_up | Results | Select Page Up | - | -
results_viewer.select_page_down | Results | Select Page Down | - | -
results_viewer.select_table_start | Results | Select Table Start | - | -
results_viewer.select_table_end | Results | Select Table End | - | -
results_viewer.select_all | Results | Select All | - | -
results_viewer.focus_query_editor | Results | Focus Query Editor | - | -
results_viewer.focus_data_catalog | Results | Focus Data Catalog | - | -
history_screen.select_query | History | Select Query | show | priority
history_screen.toggle_filters | History | Filter | show | -
history_screen.cancel | History | Cancel | show | -"""
    scope = _cott_normalize_f32_abi(scope, ActionScope, path="$.scope")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/harlequin_actions.py", "5801f928c9529d81bbb7029ea9b15a3214d219d14af589829f4ff2b3dc0a806b", "harlequin_actions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.harlequin_actions")
        _result = _implementation(scope)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.harlequin_actions"
        if _error.span is None:
            _error.span = {"end_byte":10661,"end_column":1,"end_line":220,"start_byte":2441,"start_column":1,"start_line":86}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.harlequin_actions", phase="implementation-call", span={"end_byte":10661,"end_column":1,"end_line":220,"start_byte":2441,"start_column":1,"start_line":86}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.harlequin_actions", phase="implementation-call", span={"end_byte":10661,"end_column":1,"end_line":220,"start_byte":2441,"start_column":1,"start_line":86}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ActionSpec], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_unique_by(_result, "name")), "real.harlequin.keymap.harlequin_actions", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.keymap.harlequin_actions", clause="ensures:1", phase="ensures", span={"end_byte":10592,"end_column":47,"end_line":215,"start_byte":10550,"start_column":5,"start_line":215}, expected="true", actual="false")
        if not (_cott_contract_condition((_cott_unique_by(_result, "position")), "real.harlequin.keymap.harlequin_actions", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.keymap.harlequin_actions", clause="ensures:2", phase="ensures", span={"end_byte":10643,"end_column":51,"end_line":216,"start_byte":10597,"start_column":5,"start_line":216}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[ActionSpec], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def builtin_keymaps() -> CottList[KeyMap]:
    """The keymaps that ship with Harlequin: exactly one, named "vscode" (the
default keymap, from Harlequin's bundled harlequin_vscode plug-in), with
these bindings in this order. Columns: keys | action | key_display ("-"
means Nothing).
ctrl+q | quit | -
f1 | help | -
f2 | focus_query_editor | -
f5 | focus_results_viewer | -
f6 | focus_data_catalog | -
f8 | show_query_history | -
ctrl+b,f9 | toggle_sidebar | -
f10 | toggle_full_screen | -
f12 | show_debug_info | -
ctrl+e | show_data_exporter | -
ctrl+r | refresh_catalog | -
tab | focus_next | -
shift+tab | focus_previous | -
ctrl+n | code_editor.new_buffer | -
ctrl+w | code_editor.close_buffer | -
ctrl+k | code_editor.next_buffer | -
ctrl+enter,ctrl+j | code_editor.run_query | ^⏎ or ^j
f4 | code_editor.format_buffer | -
ctrl+s | code_editor.save_buffer | -
ctrl+o | code_editor.load_buffer | -
alt+e | code_editor.launch_external_editor | -
ctrl+f | code_editor.find | -
f3 | code_editor.find_next | -
ctrl+g | code_editor.goto_line | -
up | code_editor.cursor_up | -
down | code_editor.cursor_down | -
left | code_editor.cursor_left | -
right | code_editor.cursor_right | -
ctrl+left | code_editor.cursor_word_left | -
ctrl+right | code_editor.cursor_word_right | -
home | code_editor.cursor_line_start | -
end | code_editor.cursor_line_end | -
ctrl+home | code_editor.cursor_doc_start | -
ctrl+end | code_editor.cursor_doc_end | -
pageup | code_editor.cursor_page_up | -
pagedown | code_editor.cursor_page_down | -
shift+up | code_editor.select_up | -
shift+down | code_editor.select_down | -
shift+left | code_editor.select_left | -
shift+right | code_editor.select_right | -
ctrl+shift+left | code_editor.select_word_left | -
ctrl+shift+right | code_editor.select_word_right | -
shift+home | code_editor.select_line_start | -
shift+end | code_editor.select_line_end | -
ctrl+shift+home | code_editor.select_doc_start | -
ctrl+shift+end | code_editor.select_doc_end | -
ctrl+a | code_editor.select_all | -
ctrl+up | code_editor.scroll_up_one | -
ctrl+down | code_editor.scroll_down_one | -
ctrl+underscore | code_editor.toggle_comment | -
ctrl+x | code_editor.cut | -
ctrl+c | code_editor.copy | -
ctrl+u,ctrl+v,shift+insert | code_editor.paste | -
ctrl+z | code_editor.undo | -
ctrl+y | code_editor.redo | -
backspace | code_editor.delete_left | -
delete | code_editor.delete_right | -
shift+delete | code_editor.delete_line | -
j | data_catalog.previous_tab | -
k | data_catalog.next_tab | -
ctrl+enter,ctrl+j | data_catalog.insert_name | ^⏎ or ^j
ctrl+c | data_catalog.copy_name | -
enter | data_catalog.select_cursor | -
space | data_catalog.toggle_node | -
up | data_catalog.cursor_up | -
down | data_catalog.cursor_down | -
full_stop | data_catalog.show_context_menu | -
escape | data_catalog.hide_context_menu | -
j | results_viewer.previous_tab | -
k | results_viewer.next_tab | -
ctrl+c | results_viewer.copy_selection | -
enter | results_viewer.select_cursor | -
space | results_viewer.view_cell | -
up | results_viewer.cursor_up | -
down | results_viewer.cursor_down | -
left | results_viewer.cursor_left | -
right | results_viewer.cursor_right | -
ctrl+left | results_viewer.cursor_row_start | -
ctrl+right | results_viewer.cursor_row_end | -
ctrl+up,home | results_viewer.cursor_column_start | -
ctrl+down,end | results_viewer.cursor_column_end | -
tab | results_viewer.cursor_next_cell | -
shift+tab | results_viewer.cursor_previous_cell | -
pageup | results_viewer.cursor_page_up | -
pagedown | results_viewer.cursor_page_down | -
ctrl+home | results_viewer.cursor_table_start | -
ctrl+end | results_viewer.cursor_table_end | -
shift+up | results_viewer.select_up | -
shift+down | results_viewer.select_down | -
shift+left | results_viewer.select_left | -
shift+right | results_viewer.select_right | -
ctrl+shift+left | results_viewer.select_row_start | -
ctrl+shift+right | results_viewer.select_row_end | -
ctrl+shift+up,shift+home | results_viewer.select_column_start | -
ctrl+shift+down,shift+end | results_viewer.select_column_end | -
shift+pageup | results_viewer.select_page_up | -
shift+pagedown | results_viewer.select_page_down | -
ctrl+shift+home | results_viewer.select_table_start | -
ctrl+shift+end | results_viewer.select_table_end | -
ctrl+a | results_viewer.select_all | -
enter | history_screen.select_query | -
escape | history_screen.cancel | -
ctrl+f | history_screen.toggle_filters | -"""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/builtin_keymaps.py", "7da62b0fa6061f9f96b04090998a3fd2a85795c8425f441a222baeac81b04aeb", "builtin_keymaps", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.builtin_keymaps")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.builtin_keymaps"
        if _error.span is None:
            _error.span = {"end_byte":15579,"end_column":1,"end_line":335,"start_byte":10661,"start_column":1,"start_line":220}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.builtin_keymaps", phase="implementation-call", span={"end_byte":15579,"end_column":1,"end_line":335,"start_byte":10661,"start_column":1,"start_line":220}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.builtin_keymaps", phase="implementation-call", span={"end_byte":15579,"end_column":1,"end_line":335,"start_byte":10661,"start_column":1,"start_line":220}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[KeyMap], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 1)), "real.harlequin.keymap.builtin_keymaps", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.keymap.builtin_keymaps", clause="ensures:1", phase="ensures", span={"end_byte":15561,"end_column":28,"end_line":331,"start_byte":15538,"start_column":5,"start_line":331}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[KeyMap], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def bind_keymaps(available: CottList[KeyMap], names: CottList[str]) -> Result[BoundKeySet, KeymapError]:
    """Combine the keymaps named by names, in order, into the key bindings the IDE
installs, the way Harlequin binds them. available is every known keymap
(builtin_keymaps followed by keymaps defined in config files; when two share
a name the later one in available wins).
For each name in order: a name with no keymap in available is
UnknownKeymap(name). For each binding of that keymap in order: an action that
is not the name of an action of harlequin_actions(scope) for any scope is UnknownAction(keymap name, action); each
comma-separated key, with surrounding spaces removed, is one BoundKey whose
scope, description, show and priority come from the ActionSpec and whose
key_display is the binding's; an empty key is EmptyKey(keymap name, action).
Key names are normalized to lower case.
A later BoundKey with the same (scope, key) as an earlier one replaces it in
place (Textual rebinding semantics), so the last keymap listed wins.
After all keymaps, if no binding named the action "quit", add
BoundKey(key "ctrl+q", action "quit", scope App, description "Quit", show
true, priority true, key_display Nothing) at the end.
The result keeps first-insertion order in BoundKeySet.handle's tuple
payload with opaque tag "harlequin.bound_keys"; count is its tuple length."""
    available = _cott_normalize_f32_abi(available, CottList[KeyMap], path="$.available")
    names = _cott_normalize_f32_abi(names, CottList[str], path="$.names")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/bind_keymaps.py", "ffcf736a49d0278cb9c2c26aa0d142615d6e4596915d84fd975bf1da7807606d", "bind_keymaps", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.bind_keymaps")
        _result = _implementation(available, names)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.bind_keymaps"
        if _error.span is None:
            _error.span = {"end_byte":17204,"end_column":1,"end_line":365,"start_byte":15579,"start_column":1,"start_line":335}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.bind_keymaps", phase="implementation-call", span={"end_byte":17204,"end_column":1,"end_line":365,"start_byte":15579,"start_column":1,"start_line":335}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.bind_keymaps", phase="implementation-call", span={"end_byte":17204,"end_column":1,"end_line":365,"start_byte":15579,"start_column":1,"start_line":335}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[BoundKeySet, KeymapError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.keymap.bind_keymaps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (KeymapError_UnknownKeymap, KeymapError_UnknownAction, KeymapError_EmptyKey,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.keymap.bind_keymaps", phase="error", span={"end_byte":17204,"end_column":1,"end_line":365,"start_byte":15579,"start_column":1,"start_line":335}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.keymap.bind_keymaps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.keymap.bind_keymaps", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is KeymapError_UnknownKeymap:
            _cott_contract_condition(True, "real.harlequin.keymap.bind_keymaps", "error:2")
        if type(_result) is Err and type(_result.error) is KeymapError_UnknownAction:
            _cott_contract_condition(True, "real.harlequin.keymap.bind_keymaps", "error:3")
        if type(_result) is Err and type(_result.error) is KeymapError_EmptyKey:
            _cott_contract_condition(True, "real.harlequin.keymap.bind_keymaps", "error:4")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                bound = _cott_match_value.value
                return (_cott_contract_condition((((bound).count > 0)), "real.harlequin.keymap.bind_keymaps", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.keymap.bind_keymaps", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.keymap.bind_keymaps", clause="ensures:1", phase="ensures", span={"end_byte":17082,"end_column":48,"end_line":357,"start_byte":17039,"start_column":5,"start_line":357}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[BoundKeySet, KeymapError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def terminal_key_sequence(key: str) -> Option[CottList[str]]:
    """Translate one normalized Textual key name into the prompt_toolkit key
sequence that a terminal delivers for it, or Nothing when a terminal cannot
report that key distinctly (the binding is then not installed).
Rules, applied to the whole name:
- Named keys map to themselves: up, down, left, right, home, end, insert,
  delete, pageup, pagedown, escape, f1 through f24. "backspace" -> "c-h",
  "enter" -> "c-m", "tab" -> "c-i", "space" -> " ", "full_stop" -> ".",
  "comma" -> ",", "slash" -> "/", "underscore" -> "_", "minus" -> "-",
  "plus" -> "+", "equals_sign" -> "=", "question_mark" -> "?",
  "colon" -> ":", "semicolon" -> ";", "backslash" -> "\\\\",
  "left_square_bracket" -> "[", "right_square_bracket" -> "]",
  "circumflex_accent" -> "^", "grave_accent" -> "`", "apostrophe" -> "'",
  "quotation_mark" -> "\\"", "number_sign" -> "#", "dollar_sign" -> "$",
  "percent_sign" -> "%", "ampersand" -> "&", "asterisk" -> "*",
  "exclamation_mark" -> "!", "at" -> "@", "tilde" -> "~",
  "vertical_line" -> "|", "less_than_sign" -> "<", "greater_than_sign" -> ">",
  "left_parenthesis" -> "(", "right_parenthesis" -> ")",
  "left_curly_bracket" -> "{", "right_curly_bracket" -> "}"; any other single
  character maps to itself.
- "ctrl+<letter>" -> "c-<letter>"; "ctrl+space" and "ctrl+at" -> "c-@";
  "ctrl+underscore" and "ctrl+slash" -> "c-_"; "ctrl+backslash" -> "c-\\\\";
  "ctrl+right_square_bracket" -> "c-]"; "ctrl+circumflex_accent" -> "c-^";
  "ctrl+<digit>" -> "c-<digit>"; "ctrl+" followed by up, down, left, right,
  home, end, insert, delete, pageup, pagedown or f1..f24 -> "c-" + that name.
- "shift+" followed by up, down, left, right, home, end, insert, delete,
  pageup, pagedown -> "s-" + that name; "shift+tab" -> "s-tab"; "shift+" a
  letter -> the upper-case letter.
- "ctrl+shift+" followed by up, down, left, right, home, end, insert,
  delete, pageup, pagedown -> "c-s-" + that name.
- "alt+X" or "alt+shift+X" -> ["escape"] followed by the translation of X
  (upper-cased for alt+shift+letter); "escape" alone is one key.
- Everything else, including "ctrl+enter", "ctrl+shift+<letter>" and
  "ctrl+tab", is Nothing because terminals do not distinguish it.
A translation is a one-element list except for alt combinations."""
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/terminal_key_sequence.py", "ff2f2ca7370acdb9d658bb88c71696330fcc8ed90ac562e6f7546ede7bf7c147", "terminal_key_sequence", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.terminal_key_sequence")
        _result = _implementation(key)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.terminal_key_sequence"
        if _error.span is None:
            _error.span = {"end_byte":19737,"end_column":1,"end_line":407,"start_byte":17204,"start_column":1,"start_line":365}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.terminal_key_sequence", phase="implementation-call", span={"end_byte":19737,"end_column":1,"end_line":407,"start_byte":17204,"start_column":1,"start_line":365}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.terminal_key_sequence", phase="implementation-call", span={"end_byte":19737,"end_column":1,"end_line":407,"start_byte":17204,"start_column":1,"start_line":365}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[CottList[str]], path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Some and True:
                sequence = _cott_match_value.value
                return (_cott_contract_condition(((len(sequence) > 0)), "real.harlequin.keymap.terminal_key_sequence", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.keymap.terminal_key_sequence", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.keymap.terminal_key_sequence", clause="ensures:1", phase="ensures", span={"end_byte":19719,"end_column":54,"end_line":403,"start_byte":19670,"start_column":5,"start_line":403}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[CottList[str]], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def key_label(key: str) -> str:
    """How the footer and help screen print one Textual key name, following
Textual's key display: "ctrl+" becomes "^", "shift+" becomes "⇧", "alt+"
becomes "⌥", "enter" "⏎", "escape" "esc", "backspace" "⌫", "delete" "del",
"pageup" "pgup", "pagedown" "pgdn", "space" "space", "full_stop" ".",
"underscore" "_", "up" "↑", "down" "↓", "left" "←", "right" "→"; other
names print unchanged. Example: "ctrl+q" -> "^q", "shift+tab" -> "⇧tab"."""
    key = _cott_normalize_f32_abi(key, str, path="$.key")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/key_label.py", "8e0cbf11349dcfea3a39975db72a645e0e5b248e4c5ce46bc0012880d019a674", "key_label", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.key_label")
        _result = _implementation(key)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.key_label"
        if _error.span is None:
            _error.span = {"end_byte":20278,"end_column":1,"end_line":419,"start_byte":19737,"start_column":1,"start_line":407}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.key_label", phase="implementation-call", span={"end_byte":20278,"end_column":1,"end_line":419,"start_byte":19737,"start_column":1,"start_line":407}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.key_label", phase="implementation-call", span={"end_byte":20278,"end_column":1,"end_line":419,"start_byte":19737,"start_column":1,"start_line":407}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def footer_hints(bound: BoundKeySet, focus: ActionScope) -> CottList[FooterHint]:
    """Read the complete BoundKey tuple from bound.handle's opaque payload and return
the footer line for the current focus: the shown (show == true) bindings
of scope App and scope focus, App first, each in bound order. Several keys
bound to the same action produce one hint:
its key text is the first binding's key_display when it has one, otherwise
the key_label of each key joined by "/". Its description is the action
description."""
    bound = _cott_normalize_f32_abi(bound, BoundKeySet, path="$.bound")
    focus = _cott_normalize_f32_abi(focus, ActionScope, path="$.focus")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/footer_hints.py", "f2c5f4b0e3035245581c7677cd75a3428ac85edd783c102f2d0f489b7f6e7c6b", "footer_hints", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.footer_hints")
        _result = _implementation(bound, focus)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.footer_hints"
        if _error.span is None:
            _error.span = {"end_byte":20849,"end_column":1,"end_line":432,"start_byte":20278,"start_column":1,"start_line":419}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.footer_hints", phase="implementation-call", span={"end_byte":20849,"end_column":1,"end_line":432,"start_byte":20278,"start_column":1,"start_line":419}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.footer_hints", phase="implementation-call", span={"end_byte":20849,"end_column":1,"end_line":432,"start_byte":20278,"start_column":1,"start_line":419}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[FooterHint], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[FooterHint], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def help_lines(bound: BoundKeySet) -> CottList[str]:
    """The key reference the help screen (F1) shows: read the BoundKey tuple
from bound.handle's opaque payload, then for each ActionScope in declaration order
that has bindings, a heading line with the scope name
(App -> "Application", Editor -> "Query Editor", Catalog -> "Data Catalog",
ContextMenu -> "Data Catalog Context Menu", Results -> "Results Viewer",
History -> "Query History"), then one line per action with bindings in that
scope, in bound order: the key_label of each of its keys joined by ", ",
padded with spaces to 24 characters, then the description; then an empty
line."""
    bound = _cott_normalize_f32_abi(bound, BoundKeySet, path="$.bound")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/keymap/help_lines.py", "3fe330d0d52674a9387108b13e1ec076cf81f834801d6e50048b61db12c03d0b", "help_lines", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.keymap.help_lines")
        _result = _implementation(bound)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.keymap.help_lines"
        if _error.span is None:
            _error.span = {"end_byte":21554,"end_column":1,"end_line":447,"start_byte":20849,"start_column":1,"start_line":432}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.keymap.help_lines", phase="implementation-call", span={"end_byte":21554,"end_column":1,"end_line":447,"start_byte":20849,"start_column":1,"start_line":432}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.keymap.help_lines", phase="implementation-call", span={"end_byte":21554,"end_column":1,"end_line":447,"start_byte":20849,"start_column":1,"start_line":432}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["ActionScope", "ActionScope_App", "ActionScope_Catalog", "ActionScope_ContextMenu", "ActionScope_Editor", "ActionScope_History", "ActionScope_Results", "ActionSpec", "BoundKey", "BoundKeySet", "FooterHint", "KeyBinding", "KeyMap", "KeymapError", "KeymapError_EmptyKey", "KeymapError_UnknownAction", "KeymapError_UnknownKeymap", "bind_keymaps", "builtin_keymaps", "footer_hints", "harlequin_actions", "help_lines", "key_label", "terminal_key_sequence"]
