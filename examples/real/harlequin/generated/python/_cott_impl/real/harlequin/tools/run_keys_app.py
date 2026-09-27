import sys
from pathlib import Path
from typing import Callable, Final

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import ConditionalContainer, HSplit, Layout, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D

from cott_runtime import CottList, Err, I64, Some
from real.harlequin.config import write_keymap
from real.harlequin.keymap import key_label
from real.harlequin.keymap_types import KeyMap
from real.harlequin.tools import edit_row_keys, keymap_name_problem, keymap_rows, rows_to_keymap
from real.harlequin.tools_types import KeyRow

_INSTRUCTION: Final[str] = "The table below shows the active key bindings loaded from your config. Edit the key bindings, then quit to save them to a keymap."
_NAMED: Final[str] = "full_stop=. comma=, slash=/ underscore=_ minus=- plus=+ equals_sign== question_mark=? colon=: semicolon=; backslash=\\ left_square_bracket=[ right_square_bracket=] circumflex_accent=^ grave_accent=` apostrophe=' quotation_mark=\" number_sign=# dollar_sign=$ percent_sign=% ampersand=& asterisk=* exclamation_mark=! at=@ tilde=~ vertical_line=| less_than_sign=< greater_than_sign=> left_parenthesis=( right_parenthesis=) left_curly_bracket={ right_curly_bracket=}"
_CONTROL: Final[str] = "c-@=ctrl+space c-_=ctrl+underscore c-\\=ctrl+backslash c-]=ctrl+right_square_bracket c-^=ctrl+circumflex_accent c-m=enter c-i=tab c-h=backspace"
_TABLE: Final[int] = 0
_EDIT: Final[int] = 1
_CAPTURE: Final[int] = 2
_QUIT: Final[int] = 3


def _textual(key: str) -> str:
    for entry in _CONTROL.split(" "):
        name, _, value = entry.partition("=")
        if key == name:
            return value
    if key == " ":
        return "space"
    if key.startswith("c-s-"):
        return "ctrl+shift+" + key[4:]
    if key.startswith("s-"):
        return "shift+" + key[2:]
    if key.startswith("c-") and len(key) > 2:
        return "ctrl+" + key[2:]
    if len(key) == 1:
        if key.isascii() and key.isupper():
            return "shift+" + key.lower()
        for entry in _NAMED.split(" "):
            name, _, value = entry.partition("=")
            if value == key:
                return name
    return key


def _keys_text(row: KeyRow) -> str:
    return ", ".join(key_label(key) for key in row.keys)


def _display_text(row: KeyRow) -> str:
    display = row.key_display
    return display.value if isinstance(display, Some) else ""


def _header(active: CottList[str]) -> StyleAndTextTuples:
    return [("bold", _INSTRUCTION + "\n"), ("", "Loaded Keymaps: " + ", ".join(active) + "\n")]


def _table(rows: list[KeyRow], state: dict[str, int]) -> StyleAndTextTuples:
    action_width = max([len("Action")] + [len(row.title) for row in rows])
    keys_width = max([len("Keys")] + [len(_keys_text(row)) for row in rows])
    result: StyleAndTextTuples = [("bold underline", f"{'Action':<{action_width}}  {'Keys':<{keys_width}}  Key Display\n")]
    for index, row in enumerate(rows):
        result.append(("reverse" if index == state["idx"] else "", f"{row.title:<{action_width}}  {_keys_text(row):<{keys_width}}  {_display_text(row)}\n"))
    return result


def _table_cursor(state: dict[str, int]) -> Point:
    return Point(x=0, y=state["idx"] + 1)


def _button(label: str, selected: bool) -> tuple[str, str]:
    return ("reverse bold" if selected else "", f"[ {label} ]")


def _editor_top(rows: list[KeyRow], state: dict[str, int], keys: list[str]) -> StyleAndTextTuples:
    result: StyleAndTextTuples = [
        ("bold", rows[state["idx"]].title + "\n"),
        ("", "Use the buttons below to replace, remove, or add bindings for this action.\n"),
        ("italic", "Enter: Select Button; Tab: Next Button\n\n"),
    ]
    for index, key in enumerate(keys):
        result.append(("", f"{key_label(key):<16} "))
        result.append(_button("Edit", state["focus"] == 2 * index))
        result.append(("", " "))
        result.append(_button("Remove", state["focus"] == 2 * index + 1))
        result.append(("", "\n"))
    result.append(_button("Add Key", state["focus"] == 2 * len(keys)))
    result.append(("", "\n"))
    if state["mode"] == _CAPTURE:
        result.append(("bold", "\nPress a key combination\n"))
    return result


def _editor_cursor(state: dict[str, int], keys: list[str]) -> Point:
    if state["mode"] == _CAPTURE:
        return Point(x=0, y=6 + len(keys))
    return Point(x=0, y=4 + min(state["focus"] // 2, len(keys)))


def _editor_bottom(state: dict[str, int], keys: list[str]) -> StyleAndTextTuples:
    submit = 2 * len(keys) + 2
    return [_button("Submit", state["focus"] == submit), ("", " "), _button("Cancel", state["focus"] == submit + 1)]


def _quit_top(message: list[str]) -> StyleAndTextTuples:
    return [("bold", "You have unsaved changes to your keymap.\n"), ("fg:ansired", message[0] + "\n"), ("", "Keymap name:")]


def _quit_buttons(state: dict[str, int]) -> StyleAndTextTuples:
    return [
        _button("Keep Editing", state["focus"] == 2),
        ("", " "),
        _button("Discard + Quit", state["focus"] == 3),
        ("", " "),
        _button("Save + Quit", state["focus"] == 4),
    ]


def _sync_focus(state: dict[str, int], keys: list[str], windows: dict[str, Window], app: Application[None]) -> None:
    if state["mode"] == _EDIT and state["focus"] == 2 * len(keys) + 1:
        app.layout.focus(windows["display"])
    elif state["mode"] == _QUIT and state["focus"] == 0:
        app.layout.focus(windows["name"])
    elif state["mode"] == _QUIT and state["focus"] == 1:
        app.layout.focus(windows["path"])
    elif state["mode"] == _TABLE:
        app.layout.focus(windows["table"])
    elif state["mode"] == _EDIT or state["mode"] == _CAPTURE:
        app.layout.focus(windows["editor"])
    else:
        app.layout.focus(windows["sink"])
    app.invalidate()


def _move(state: dict[str, int], rows: list[KeyRow], delta: int, app: Application[None]) -> None:
    if rows:
        state["idx"] = max(0, min(len(rows) - 1, state["idx"] + delta))
        app.invalidate()


def _open_editor(state: dict[str, int], rows: list[KeyRow], keys: list[str], display: Buffer, windows: dict[str, Window], app: Application[None]) -> None:
    if not rows:
        return
    row = rows[state["idx"]]
    keys.clear()
    keys.extend(row.keys)
    display.document = Document(_display_text(row))
    state["mode"] = _EDIT
    state["focus"] = 0
    _sync_focus(state, keys, windows, app)


def _cycle(state: dict[str, int], count: int, delta: int, keys: list[str], windows: dict[str, Window], app: Application[None]) -> None:
    state["focus"] = (state["focus"] + delta) % count
    _sync_focus(state, keys, windows, app)


def _editor_enter(state: dict[str, int], rows: list[KeyRow], keys: list[str], display: Buffer, windows: dict[str, Window], app: Application[None]) -> None:
    focus = state["focus"]
    count = len(keys)
    if focus < 2 * count:
        if focus % 2 == 0:
            state["target"] = focus // 2
            state["mode"] = _CAPTURE
        else:
            keys.pop(focus // 2)
            state["focus"] = min(focus - 1, 2 * len(keys))
    elif focus == 2 * count:
        state["target"] = -1
        state["mode"] = _CAPTURE
    elif focus == 2 * count + 1:
        state["focus"] = focus + 1
    elif focus == 2 * count + 2:
        rows[state["idx"]] = edit_row_keys(rows[state["idx"]], CottList(values=list(keys)), display.text)
        state["mode"] = _TABLE
    else:
        state["mode"] = _TABLE
    _sync_focus(state, keys, windows, app)


def _capture(state: dict[str, int], keys: list[str], event: KeyPressEvent, windows: dict[str, Window], app: Application[None]) -> None:
    pressed: list[str] = []
    for press in event.key_sequence:
        raw = press.key
        pressed.append(raw.value if isinstance(raw, Keys) else raw)
    key = _textual(pressed[-1])
    if len(pressed) == 2 and pressed[0] == "escape":
        key = "alt+" + key
    if state["target"] < 0:
        keys.append(key)
        state["focus"] = 2 * len(keys)
    else:
        keys[state["target"]] = key
    state["mode"] = _EDIT
    _sync_focus(state, keys, windows, app)


def _has_changes(rows: list[KeyRow], initial: list[KeyRow]) -> bool:
    for current, original in zip(rows, initial):
        if current.action != original.action or current.title != original.title or list(current.keys) != list(original.keys) or _display_text(current) != _display_text(original):
            return True
    return False


def _request_quit(state: dict[str, int], rows: list[KeyRow], initial: list[KeyRow], keys: list[str], windows: dict[str, Window], message: list[str], app: Application[None]) -> None:
    if not _has_changes(rows, initial):
        app.exit()
        return
    state["resume"] = state["mode"]
    state["resume_focus"] = state["focus"]
    message[0] = ""
    state["mode"] = _QUIT
    state["focus"] = 0
    _sync_focus(state, keys, windows, app)


def _quit_enter(state: dict[str, int], keys: list[str], windows: dict[str, Window], message: list[str], name: Buffer, path: Buffer, builtin_names: CottList[str], app: Application[None]) -> None:
    focus = state["focus"]
    if focus < 2:
        state["focus"] = focus + 1
    elif focus == 2:
        state["mode"] = state["resume"]
        state["focus"] = state["resume_focus"]
    elif focus == 3:
        app.exit()
        return
    else:
        problem = keymap_name_problem(name.text, builtin_names)
        if isinstance(problem, Some):
            message[0] = "Keymap name: " + problem.value
            state["focus"] = 0
        elif Path(path.text).expanduser().is_dir():
            message[0] = "File path: Must not be a directory"
            state["focus"] = 1
        else:
            state["result"] = 1
            app.exit()
            return
    _sync_focus(state, keys, windows, app)


def _bind(bindings: KeyBindings, keys: tuple[str | Keys, ...], enabled: Condition, eager: bool, callback: Callable[[KeyPressEvent], None]) -> None:
    bindings.add(*keys, filter=enabled, eager=eager)(callback)


def run_keys_app(save_path: Path, active: CottList[str], builtin_names: CottList[str], available: CottList[KeyMap]) -> I64:
    rows: list[KeyRow] = list(keymap_rows(available, active))
    initial = list(rows)
    state: dict[str, int] = {"idx": 0, "mode": _TABLE, "focus": 0, "target": -1, "result": 0, "resume": _TABLE, "resume_focus": 0}
    keys: list[str] = []
    message: list[str] = [""]
    last_name = ""
    for entry in active:
        last_name = entry
    display = Buffer(multiline=False)
    name = Buffer(multiline=False, document=Document(last_name))
    path = Buffer(multiline=False, document=Document(str(save_path)))
    windows: dict[str, Window] = {
        "sink": Window(content=FormattedTextControl(lambda: _header(active), focusable=True), height=3, wrap_lines=True),
        "table": Window(content=FormattedTextControl(lambda: _table(rows, state), focusable=True, get_cursor_position=lambda: _table_cursor(state)), height=D(weight=1)),
        "display": Window(content=BufferControl(buffer=display), height=1, style="underline"),
        "name": Window(content=BufferControl(buffer=name), height=1, style="underline"),
        "path": Window(content=BufferControl(buffer=path), height=1, style="underline"),
    }
    windows["editor"] = Window(content=FormattedTextControl(lambda: _editor_top(rows, state, keys), focusable=True, get_cursor_position=lambda: _editor_cursor(state, keys)), height=D(weight=1))
    editor = HSplit([
        windows["editor"],
        Window(content=FormattedTextControl([("", "Key Display:")]), height=1),
        windows["display"],
        Window(content=FormattedTextControl(lambda: _editor_bottom(state, keys)), height=1),
    ])
    quit_dialog = HSplit([
        Window(content=FormattedTextControl(lambda: _quit_top(message)), height=3),
        windows["name"],
        Window(content=FormattedTextControl([("", "File path:")]), height=1),
        windows["path"],
        Window(content=FormattedTextControl(lambda: _quit_buttons(state)), height=1),
        Window(height=D(weight=1)),
    ])
    in_table = Condition(lambda: state["mode"] == _TABLE)
    in_editor = Condition(lambda: state["mode"] == _EDIT or state["mode"] == _CAPTURE)
    in_edit = Condition(lambda: state["mode"] == _EDIT)
    in_capture = Condition(lambda: state["mode"] == _CAPTURE)
    in_quit = Condition(lambda: state["mode"] == _QUIT)
    may_quit = Condition(lambda: state["mode"] == _TABLE or state["mode"] == _EDIT)
    root = HSplit([
        windows["sink"],
        ConditionalContainer(content=windows["table"], filter=in_table),
        ConditionalContainer(content=editor, filter=in_editor),
        ConditionalContainer(content=quit_dialog, filter=in_quit),
        Window(content=FormattedTextControl([("reverse", " ^q Quit  ⏎ Edit ")]), height=1),
    ])
    bindings = KeyBindings()
    app: Application[None] = Application(layout=Layout(root, focused_element=windows["table"]), key_bindings=bindings, full_screen=True)
    _bind(bindings, ("up",), in_table, False, lambda event: _move(state, rows, -1, app))
    _bind(bindings, ("down",), in_table, False, lambda event: _move(state, rows, 1, app))
    _bind(bindings, ("pageup",), in_table, False, lambda event: _move(state, rows, -10, app))
    _bind(bindings, ("pagedown",), in_table, False, lambda event: _move(state, rows, 10, app))
    _bind(bindings, ("home",), in_table, False, lambda event: _move(state, rows, -len(rows), app))
    _bind(bindings, ("end",), in_table, False, lambda event: _move(state, rows, len(rows), app))
    _bind(bindings, ("enter",), in_table, False, lambda event: _open_editor(state, rows, keys, display, windows, app))
    _bind(bindings, ("c-q",), may_quit, True, lambda event: _request_quit(state, rows, initial, keys, windows, message, app))
    _bind(bindings, ("tab",), in_edit, True, lambda event: _cycle(state, 2 * len(keys) + 4, 1, keys, windows, app))
    _bind(bindings, ("s-tab",), in_edit, True, lambda event: _cycle(state, 2 * len(keys) + 4, -1, keys, windows, app))
    _bind(bindings, ("down",), in_edit, True, lambda event: _cycle(state, 2 * len(keys) + 4, 1, keys, windows, app))
    _bind(bindings, ("up",), in_edit, True, lambda event: _cycle(state, 2 * len(keys) + 4, -1, keys, windows, app))
    _bind(bindings, ("enter",), in_edit, True, lambda event: _editor_enter(state, rows, keys, display, windows, app))
    _bind(bindings, (Keys.Any,), in_capture, False, lambda event: _capture(state, keys, event, windows, app))
    _bind(bindings, ("escape", Keys.Any), in_capture, False, lambda event: _capture(state, keys, event, windows, app))
    _bind(bindings, ("tab",), in_quit, True, lambda event: _cycle(state, 5, 1, keys, windows, app))
    _bind(bindings, ("s-tab",), in_quit, True, lambda event: _cycle(state, 5, -1, keys, windows, app))
    _bind(bindings, ("enter",), in_quit, True, lambda event: _quit_enter(state, keys, windows, message, name, path, builtin_names, app))
    app.run()
    if state["result"] != 1:
        return 0
    keymap_name = name.text
    target = Path(path.text).expanduser()
    written = write_keymap(target, rows_to_keymap(keymap_name, CottList(values=rows)))
    if isinstance(written, Err):
        print(written.error.title, file=sys.stderr)
        print(written.error.message, file=sys.stderr)
        return 2
    print("Keymap successfully created")
    print(f"Keymap {keymap_name} written to file at {target}")
    print(f"Use it with: harlequin --keymap-name {keymap_name}")
    print(f"or in a profile: keymap_name=['{keymap_name}']")
    return 0
