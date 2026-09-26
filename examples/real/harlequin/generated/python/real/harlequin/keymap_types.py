from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""Which part of the IDE an action belongs to. App actions work from anywhere;
Editor actions apply while the query editor has focus; Catalog while the data
catalog has focus; ContextMenu while the catalog's context menu is open;
Results while the results viewer has focus; History while the query history
screen is open."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionScope_App:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionScope_Editor:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionScope_Catalog:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionScope_ContextMenu:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionScope_Results:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionScope_History:
    pass

ActionScope: TypeAlias = Union[ActionScope_App, ActionScope_Editor, ActionScope_Catalog, ActionScope_ContextMenu, ActionScope_Results, ActionScope_History]

"""One Harlequin action: its keymap name (the name a keymap binding uses), scope,
footer/help description, whether the footer shows it, whether its binding
is checked before the focused widget sees the key (priority), and its 0-based
row in the whole harlequin_actions table (position), which orders actions
across scopes."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActionSpec:
    __hash__ = None
    name: str
    scope: ActionScope
    description: str
    show: bool
    priority: bool
    position: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scope", _cott_validate_abi(self.scope, ActionScope, path="$.scope"))
        if not _cott_validated_construction():
            object.__setattr__(self, "description", _cott_validate_abi(self.description, str, path="$.description"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show", _cott_validate_abi(self.show, bool, path="$.show"))
        if not _cott_validated_construction():
            object.__setattr__(self, "priority", _cott_validate_abi(self.priority, bool, path="$.priority"))
        if not _cott_validated_construction():
            object.__setattr__(self, "position", _cott_validate_abi(self.position, U64, path="$.position"))

"""One keymap entry as written in a keymap or a config file: keys is a
comma-separated list of Textual key names (for example "ctrl+b,f9"), action is
an ActionSpec name, and key_display optionally overrides how the footer shows
the keys."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeyBinding:
    __hash__ = None
    keys: str
    action: str
    key_display: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "keys", _cott_validate_abi(self.keys, str, path="$.keys"))
        if not _cott_validated_construction():
            object.__setattr__(self, "action", _cott_validate_abi(self.action, str, path="$.action"))
        if not _cott_validated_construction():
            object.__setattr__(self, "key_display", _cott_validate_abi(self.key_display, Option[str], path="$.key_display"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeyMap:
    __hash__ = None
    name: str
    bindings: CottList[KeyBinding]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bindings", _cott_validate_abi(self.bindings, CottList[KeyBinding], path="$.bindings"))

"""One key, bound to one action, after keymaps are combined. key is a single
normalized Textual key name."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BoundKey:
    __hash__ = None
    key: str
    action: str
    scope: ActionScope
    description: str
    show: bool
    priority: bool
    key_display: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "action", _cott_validate_abi(self.action, str, path="$.action"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scope", _cott_validate_abi(self.scope, ActionScope, path="$.scope"))
        if not _cott_validated_construction():
            object.__setattr__(self, "description", _cott_validate_abi(self.description, str, path="$.description"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show", _cott_validate_abi(self.show, bool, path="$.show"))
        if not _cott_validated_construction():
            object.__setattr__(self, "priority", _cott_validate_abi(self.priority, bool, path="$.priority"))
        if not _cott_validated_construction():
            object.__setattr__(self, "key_display", _cott_validate_abi(self.key_display, Option[str], path="$.key_display"))

"""The ordered bound keys of any size, retained locally rather than crossing a
generated facade as a List. handle is an Opaque["harlequin.bound_keys"] whose
payload is a tuple of BoundKey values in insertion order, built with
cott_runtime.Opaque(tag="harlequin.bound_keys", value=tuple(...)). Consumers
check handle.tag and cast handle.unwrap() to tuple[BoundKey, ...] before
iterating. count is the number of bound keys (including the required Quit);
the handle and its tuple can be shared without copying the bindings."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BoundKeySet:
    __hash__ = None
    handle: Opaque[Literal["harlequin.bound_keys"]]
    count: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "handle", _cott_validate_abi(self.handle, Opaque[Literal["harlequin.bound_keys"]], path="$.handle"))
        if not _cott_validated_construction():
            object.__setattr__(self, "count", _cott_validate_abi(self.count, U64, path="$.count"))

"""One footer hint: the key text to show and the action description."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FooterHint:
    __hash__ = None
    key: str
    description: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "description", _cott_validate_abi(self.description, str, path="$.description"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeymapError_UnknownKeymap:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeymapError_UnknownAction:
    __hash__ = None
    keymap: str
    action: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeymapError_EmptyKey:
    __hash__ = None
    keymap: str
    action: str

KeymapError: TypeAlias = Union[KeymapError_UnknownKeymap, KeymapError_UnknownAction, KeymapError_EmptyKey]

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
"""How the footer and help screen print one Textual key name, following
Textual's key display: "ctrl+" becomes "^", "shift+" becomes "⇧", "alt+"
becomes "⌥", "enter" "⏎", "escape" "esc", "backspace" "⌫", "delete" "del",
"pageup" "pgup", "pagedown" "pgdn", "space" "space", "full_stop" ".",
"underscore" "_", "up" "↑", "down" "↓", "left" "←", "right" "→"; other
names print unchanged. Example: "ctrl+q" -> "^q", "shift+tab" -> "⇧tab"."""
"""Read the complete BoundKey tuple from bound.handle's opaque payload and return
the footer line for the current focus: the shown (show == true) bindings
of scope App and scope focus, App first, each in bound order. Several keys
bound to the same action produce one hint:
its key text is the first binding's key_display when it has one, otherwise
the key_label of each key joined by "/". Its description is the action
description."""
"""The key reference the help screen (F1) shows: read the BoundKey tuple
from bound.handle's opaque payload, then for each ActionScope in declaration order
that has bindings, a heading line with the scope name
(App -> "Application", Editor -> "Query Editor", Catalog -> "Data Catalog",
ContextMenu -> "Data Catalog Context Menu", Results -> "Results Viewer",
History -> "Query History"), then one line per action with bindings in that
scope, in bound order: the key_label of each of its keys joined by ", ",
padded with spaces to 24 characters, then the description; then an empty
line."""
__all__ = ["ActionScope", "ActionScope_App", "ActionScope_Catalog", "ActionScope_ContextMenu", "ActionScope_Editor", "ActionScope_History", "ActionScope_Results", "ActionSpec", "BoundKey", "BoundKeySet", "FooterHint", "KeyBinding", "KeyMap", "KeymapError", "KeymapError_EmptyKey", "KeymapError_UnknownAction", "KeymapError_UnknownKeymap"]
