from typing import Final

from cott_runtime import CottList, Nothing, Option, Some

_NAVIGATION: Final[str] = "up down left right home end insert delete pageup pagedown"
_NAMED_KEYS: Final[str] = "full_stop=. comma=, slash=/ underscore=_ minus=- plus=+ equals_sign== question_mark=? colon=: semicolon=; backslash=\\ left_square_bracket=[ right_square_bracket=] circumflex_accent=^ grave_accent=` apostrophe=' quotation_mark=\" number_sign=# dollar_sign=$ percent_sign=% ampersand=& asterisk=* exclamation_mark=! at=@ tilde=~ vertical_line=| less_than_sign=< greater_than_sign=> left_parenthesis=( right_parenthesis=) left_curly_bracket={ right_curly_bracket=}"
_CTRL_SPECIAL: Final[str] = "space=@ at=@ underscore=_ slash=_ backslash=\\ right_square_bracket=] circumflex_accent=^"


def _lookup(table: str, name: str) -> str | None:
    for entry in table.split(" "):
        key, _, value = entry.partition("=")
        if key == name:
            return value
    return None


def _is_function_key(name: str) -> bool:
    if len(name) < 2 or name[0] != "f" or not name[1:].isdigit() or name[1] == "0":
        return False
    return 1 <= int(name[1:]) <= 24


def _is_navigation(name: str) -> bool:
    return name in _NAVIGATION.split(" ")


def _is_letter(name: str) -> bool:
    return len(name) == 1 and "a" <= name.lower() <= "z" and name.isascii()


def _plain(name: str) -> str | None:
    if _is_navigation(name) or _is_function_key(name) or name == "escape":
        return name
    if name == "backspace":
        return "c-h"
    if name == "enter":
        return "c-m"
    if name == "tab":
        return "c-i"
    if name == "space":
        return " "
    mapped = _lookup(_NAMED_KEYS, name)
    if mapped is not None:
        return mapped
    if len(name) == 1:
        return name
    return None


def _single(key: str) -> str | None:
    if key.startswith("ctrl+shift+"):
        rest = key[len("ctrl+shift+"):]
        return "c-s-" + rest if _is_navigation(rest) else None
    if key.startswith("ctrl+"):
        rest = key[len("ctrl+"):]
        if _is_letter(rest):
            return "c-" + rest.lower()
        if len(rest) == 1 and rest.isdigit():
            return "c-" + rest
        special = _lookup(_CTRL_SPECIAL, rest)
        if special is not None:
            return "c-" + special
        if _is_navigation(rest) or _is_function_key(rest):
            return "c-" + rest
        return None
    if key.startswith("shift+"):
        rest = key[len("shift+"):]
        if _is_navigation(rest) or rest == "tab":
            return "s-" + rest
        if _is_letter(rest):
            return rest.upper()
        return None
    return _plain(key)


def terminal_key_sequence(key: str) -> Option[CottList[str]]:
    if key.startswith("alt+shift+"):
        rest = key[len("alt+shift+"):]
        if _is_letter(rest):
            return Some(value=CottList(values=["escape", rest.upper()]))
        inner = _single("shift+" + rest)
    elif key.startswith("alt+"):
        inner = _single(key[len("alt+"):])
    else:
        single = _single(key)
        if single is None:
            return Nothing()
        return Some(value=CottList(values=[single]))
    if inner is None:
        return Nothing()
    return Some(value=CottList(values=["escape", inner]))
