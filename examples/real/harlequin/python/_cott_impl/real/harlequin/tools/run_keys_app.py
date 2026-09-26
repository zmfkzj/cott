import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

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

from cott_runtime import I64, CottList, Err, Some
from real.harlequin.config import write_keymap
from real.harlequin.keymap import key_label
from real.harlequin.keymap_types import KeyMap
from real.harlequin.tools import edit_row_keys, keymap_name_problem, keymap_rows, rows_to_keymap
from real.harlequin.tools_types import KeyRow

_INSTRUCTION: Final[str] = "The table below shows the active key bindings loaded from your config. Edit the key bindings, then quit to save them to a keymap."
_NAMED: Final[str] = "full_stop=. comma=, slash=/ underscore=_ minus=- plus=+ equals_sign== question_mark=? colon=: semicolon=; backslash=\\ left_square_bracket=[ right_square_bracket=] circumflex_accent=^ grave_accent=` apostrophe=' quotation_mark=\" number_sign=# dollar_sign=$ percent_sign=% ampersand=& asterisk=* exclamation_mark=! at=@ tilde=~ vertical_line=| less_than_sign=< greater_than_sign=> left_parenthesis=( right_parenthesis=) left_curly_bracket={ right_curly_bracket=}"
_CTRL: Final[str] = "c-@=ctrl+space c-_=ctrl+underscore c-\\=ctrl+backslash c-]=ctrl+right_square_bracket c-^=ctrl+circumflex_accent c-m=enter c-i=tab c-h=backspace"
_TABLE: Final[int] = 0
_EDIT: Final[int] = 1
_CAPTURE: Final[int] = 2
_QUIT: Final[int] = 3


def _textual(key: str) -> str:
    for entry in _CTRL.split(" "):
        name, _, value = entry.partition("=")
        if name == key:
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


def _table(rows: list[KeyRow], st: dict[str, int]) -> StyleAndTextTuples:
    width_a = max([len("Action")] + [len(row.title) for row in rows])
    width_k = max([len("Keys")] + [len(_keys_text(row)) for row in rows])
    out: StyleAndTextTuples = [("bold underline", f"{'Action':<{width_a}}  {'Keys':<{width_k}}  Key Display\n")]
    for index, row in enumerate(rows):
        style = "reverse" if index == st["idx"] else ""
        out.append((style, f"{row.title:<{width_a}}  {_keys_text(row):<{width_k}}  {_display_text(row)}\n"))
    return out


def _cursor(st: dict[str, int]) -> Point:
    return Point(x=0, y=st["idx"] + 1)


def _button(label: str, selected: bool) -> tuple[str, str]:
    return ("reverse bold" if selected else "", f"[ {label} ]")


def _editor_top(rows: list[KeyRow], st: dict[str, int], ekeys: list[str]) -> StyleAndTextTuples:
    row = rows[st["idx"]]
    focus = st["focus"]
    out: StyleAndTextTuples = [("bold", row.title + "\n"), ("", "Use the buttons below to replace, remove, or add bindings for this action.\n"), ("italic", "Enter: Select Button; Tab: Next Button\n\n")]
    for index, key in enumerate(ekeys):
        out.append(("", f"{key_label(key):<16} "))
        out.append(_button("Edit", focus == 2 * index))
        out.append(("", " "))
        out.append(_button("Remove", focus == 2 * index + 1))
        out.append(("", "\n"))
    out.append(_button("Add Key", focus == 2 * len(ekeys)))
    out.append(("", "\n"))
    if st["mode"] == _CAPTURE:
        out.append(("bold", "\nPress a key combination\n"))
    out.append(("", "\nKey Display:"))
    return out


def _editor_bottom(st: dict[str, int], ekeys: list[str]) -> StyleAndTextTuples:
    base = 2 * len(ekeys) + 2
    return [_button("Submit", st["focus"] == base), ("", " "), _button("Cancel", st["focus"] == base + 1)]


def _quit_top(msg: list[str]) -> StyleAndTextTuples:
    out: StyleAndTextTuples = [("bold", "You have unsaved changes to your keymap.\n")]
    if msg[0]:
        out.append(("fg:ansired", msg[0] + "\n"))
    out.append(("", "Keymap name:"))
    return out


def _quit_buttons(st: dict[str, int]) -> StyleAndTextTuples:
    focus = st["focus"]
    return [_button("Keep Editing", focus == 2), ("", " "), _button("Discard + Quit", focus == 3), ("", " "), _button("Save + Quit", focus == 4)]


def _sync_focus(st: dict[str, int], app: Application[None], ekeys: list[str], wins: dict[str, Window]) -> None:
    mode = st["mode"]
    focus = st["focus"]
    if mode == _EDIT and focus == 2 * len(ekeys) + 1:
        app.layout.focus(wins["display"])
    elif mode == _QUIT and focus == 0:
        app.layout.focus(wins["name"])
    elif mode == _QUIT and focus == 1:
        app.layout.focus(wins["path"])
    else:
        app.layout.focus(wins["sink"])
    app.invalidate()


def _move(st: dict[str, int], rows: list[KeyRow], delta: int, app: Application[None]) -> None:
    st["idx"] = max(0, min(len(rows) - 1, st["idx"] + delta))
    app.invalidate()


def _open_editor(st: dict[str, int], rows: list[KeyRow], ekeys: list[str], display: Buffer, app: Application[None], wins: dict[str, Window]) -> None:
    if not rows:
        return
    row = rows[st["idx"]]
    ekeys.clear()
    ekeys.extend(row.keys)
    display.document = Document(_display_text(row))
    st["mode"] = _EDIT
    st["focus"] = 0
    _sync_focus(st, app, ekeys, wins)


def _cycle(st: dict[str, int], count: int, delta: int, app: Application[None], ekeys: list[str], wins: dict[str, Window]) -> None:
    st["focus"] = (st["focus"] + delta) % count
    _sync_focus(st, app, ekeys, wins)


def _cycle_editor(st: dict[str, int], delta: int, app: Application[None], ekeys: list[str], wins: dict[str, Window]) -> None:
    _cycle(st, 2 * len(ekeys) + 4, delta, app, ekeys, wins)


def _editor_enter(st: dict[str, int], rows: list[KeyRow], ekeys: list[str], display: Buffer, app: Application[None], wins: dict[str, Window]) -> None:
    focus = st["focus"]
    count = len(ekeys)
    if focus < 2 * count:
        if focus % 2 == 0:
            st["target"] = focus // 2
            st["mode"] = _CAPTURE
        else:
            ekeys.pop(focus // 2)
            st["focus"] = min(focus - 1, 2 * len(ekeys)) if focus > 0 else 0
    elif focus == 2 * count:
        st["target"] = -1
        st["mode"] = _CAPTURE
    elif focus == 2 * count + 1:
        st["focus"] = focus + 1
    elif focus == 2 * count + 2:
        old = rows[st["idx"]]
        new = edit_row_keys(old, CottList(values=list(ekeys)), display.text)
        if list(new.keys) != list(old.keys) or _display_text(new) != _display_text(old):
            st["changed"] = 1
        rows[st["idx"]] = new
        st["mode"] = _TABLE
    else:
        st["mode"] = _TABLE
    _sync_focus(st, app, ekeys, wins)


def _capture(st: dict[str, int], ekeys: list[str], event: KeyPressEvent, wins: dict[str, Window]) -> None:
    parts: list[str] = []
    for press in event.key_sequence:
        raw = press.key
        parts.append(raw.value if isinstance(raw, Keys) else raw)
    key = _textual(parts[-1])
    if len(parts) == 2 and parts[0] == "escape":
        key = "alt+" + key
    if st["target"] < 0:
        ekeys.append(key)
        st["focus"] = 2 * len(ekeys)
    else:
        ekeys[st["target"]] = key
    st["mode"] = _EDIT
    _sync_focus(st, event.app, ekeys, wins)


def _request_quit(st: dict[str, int], app: Application[None], ekeys: list[str], wins: dict[str, Window], msg: list[str]) -> None:
    if st["changed"] == 0:
        app.exit()
        return
    msg[0] = ""
    st["mode"] = _QUIT
    st["focus"] = 0
    _sync_focus(st, app, ekeys, wins)


def _quit_enter(st: dict[str, int], app: Application[None], ekeys: list[str], wins: dict[str, Window], msg: list[str], name: Buffer, path: Buffer, builtin_names: CottList[str]) -> None:
    focus = st["focus"]
    if focus < 2:
        st["focus"] = focus + 1
    elif focus == 2:
        st["mode"] = _TABLE
    elif focus == 3:
        app.exit()
        return
    else:
        problem = keymap_name_problem(name.text, builtin_names)
        if isinstance(problem, Some):
            msg[0] = f"Keymap name: {problem.value}"
            st["focus"] = 0
        elif not path.text.strip():
            msg[0] = "File path: Cannot be empty"
            st["focus"] = 1
        elif Path(path.text).expanduser().is_dir():
            msg[0] = "File path: Must not be a directory"
            st["focus"] = 1
        else:
            st["result"] = 1
            app.exit()
            return
    _sync_focus(st, app, ekeys, wins)


def _mode_is(st: dict[str, int], modes: tuple[int, ...]) -> bool:
    return st["mode"] in modes


def _bind(kb: KeyBindings, keys: tuple[str | Keys, ...], filt: Condition, eager: bool, handler: Callable[[KeyPressEvent], None]) -> None:
    kb.add(*keys, filter=filt, eager=eager)(handler)


def run_keys_app(save_path: Path, active: CottList[str], builtin_names: CottList[str], available: CottList[KeyMap]) -> I64:
    rows: list[KeyRow] = list(keymap_rows(available, active))
    st: dict[str, int] = {"idx": 0, "mode": _TABLE, "focus": 0, "target": -1, "changed": 0, "result": 0}
    ekeys: list[str] = []
    msg: list[str] = [""]
    last_name = ""
    for entry in active:
        last_name = entry
    display = Buffer(multiline=False)
    name_buf = Buffer(multiline=False, document=Document(last_name))
    path_buf = Buffer(multiline=False, document=Document(str(save_path)))
    wins: dict[str, Window] = {
        "sink": Window(FormattedTextControl(lambda: _header(active), focusable=True), height=3),
        "table": Window(FormattedTextControl(lambda: _table(rows, st), get_cursor_position=lambda: _cursor(st)), height=D(weight=1)),
        "display": Window(BufferControl(display), height=1, style="underline"),
        "name": Window(BufferControl(name_buf), height=1, style="underline"),
        "path": Window(BufferControl(path_buf), height=1, style="underline"),
    }
    editor = HSplit([
        Window(FormattedTextControl(lambda: _editor_top(rows, st, ekeys)), wrap_lines=True),
        wins["display"],
        Window(FormattedTextControl(lambda: _editor_bottom(st, ekeys)), height=1),
        Window(height=D(weight=1)),
    ])
    quit_dialog = HSplit([
        Window(FormattedTextControl(lambda: _quit_top(msg)), wrap_lines=True),
        wins["name"],
        Window(FormattedTextControl([("", "File path:")]), height=1),
        wins["path"],
        Window(FormattedTextControl(lambda: _quit_buttons(st)), height=1),
        Window(height=D(weight=1)),
    ])
    in_table = Condition(lambda: _mode_is(st, (_TABLE,)))
    in_editor = Condition(lambda: _mode_is(st, (_EDIT, _CAPTURE)))
    in_edit = Condition(lambda: _mode_is(st, (_EDIT,)))
    can_quit = Condition(lambda: _mode_is(st, (_TABLE, _EDIT)))
    in_capture = Condition(lambda: _mode_is(st, (_CAPTURE,)))
    in_quit = Condition(lambda: _mode_is(st, (_QUIT,)))
    root = HSplit([
        wins["sink"],
        ConditionalContainer(wins["table"], filter=in_table),
        ConditionalContainer(editor, filter=in_editor),
        ConditionalContainer(quit_dialog, filter=in_quit),
        Window(FormattedTextControl([("reverse", " ^q Quit  ⏎ Edit ")]), height=1),
    ])
    kb = KeyBindings()
    app: Application[None] = Application(layout=Layout(root, focused_element=wins["sink"]), key_bindings=kb, full_screen=True)
    _bind(kb, ("up",), in_table, False, lambda event: _move(st, rows, -1, app))
    _bind(kb, ("down",), in_table, False, lambda event: _move(st, rows, 1, app))
    _bind(kb, ("pageup",), in_table, False, lambda event: _move(st, rows, -10, app))
    _bind(kb, ("pagedown",), in_table, False, lambda event: _move(st, rows, 10, app))
    _bind(kb, ("home",), in_table, False, lambda event: _move(st, rows, -len(rows), app))
    _bind(kb, ("end",), in_table, False, lambda event: _move(st, rows, len(rows), app))
    _bind(kb, ("enter",), in_table, False, lambda event: _open_editor(st, rows, ekeys, display, app, wins))
    _bind(kb, ("c-q",), can_quit, False, lambda event: _request_quit(st, app, ekeys, wins, msg))
    _bind(kb, ("tab",), in_edit, True, lambda event: _cycle_editor(st, 1, app, ekeys, wins))
    _bind(kb, ("s-tab",), in_edit, True, lambda event: _cycle_editor(st, -1, app, ekeys, wins))
    _bind(kb, ("down",), in_edit, True, lambda event: _cycle_editor(st, 1, app, ekeys, wins))
    _bind(kb, ("up",), in_edit, True, lambda event: _cycle_editor(st, -1, app, ekeys, wins))
    _bind(kb, ("enter",), in_edit, True, lambda event: _editor_enter(st, rows, ekeys, display, app, wins))
    _bind(kb, (Keys.Any,), in_capture, False, lambda event: _capture(st, ekeys, event, wins))
    _bind(kb, ("escape", Keys.Any), in_capture, False, lambda event: _capture(st, ekeys, event, wins))
    _bind(kb, ("tab",), in_quit, True, lambda event: _cycle(st, 5, 1, app, ekeys, wins))
    _bind(kb, ("s-tab",), in_quit, True, lambda event: _cycle(st, 5, -1, app, ekeys, wins))
    _bind(kb, ("enter",), in_quit, True, lambda event: _quit_enter(st, app, ekeys, wins, msg, name_buf, path_buf, builtin_names))
    app.run()
    if st["result"] != 1:
        return 0
    name = name_buf.text
    target = Path(path_buf.text).expanduser()
    written = write_keymap(target, rows_to_keymap(name, CottList(values=rows)))
    if isinstance(written, Err):
        print(written.error.title, file=sys.stderr)
        print(written.error.message, file=sys.stderr)
        return 2
    print("Keymap successfully created")
    print(f"Keymap {name} written to file at {target}")
    print(f"Use it with: harlequin --keymap-name {name}")
    print(f"or in a profile: keymap_name=['{name}']")
    return 0
