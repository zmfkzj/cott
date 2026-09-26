from cott_runtime import Nothing, Option, Some
from real.toolong.keys_types import KeyEvent, TerminalInput


def _named_key(name: str) -> str:
    if name == "escape":
        return "escape"
    if name == "c-i":
        return "tab"
    if name == "c-m" or name == "c-j":
        return "enter"
    if name == "c-h":
        return "backspace"
    if name == "s-tab":
        return "shift+tab"
    if name in ("up", "down", "left", "right", "home", "end", "pageup", "pagedown", "insert", "delete"):
        return name
    if name in ("c-left", "c-right", "c-up", "c-down", "c-home", "c-end"):
        return "ctrl+" + name[2:]
    if name == "s-left" or name == "s-right":
        return "shift+" + name[2:]
    if name in ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"):
        return name
    if name == "c-\\":
        return "ctrl+backslash"
    if len(name) == 3 and name.startswith("c-") and "a" <= name[2] <= "z":
        return "ctrl+" + name[2]
    return ""


def decode_key(input: TerminalInput) -> Option[KeyEvent]:
    name = input.name
    if len(name) == 1 and name.isprintable():
        if name == " ":
            return Some(value=KeyEvent(key="space", character=Some(value=name)))
        if name == "/":
            return Some(value=KeyEvent(key="slash", character=Some(value=name)))
        return Some(value=KeyEvent(key=name, character=Some(value=name)))
    key = _named_key(name)
    if key == "":
        return Nothing()
    return Some(value=KeyEvent(key=key, character=Nothing()))
