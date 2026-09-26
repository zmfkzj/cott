from typing import Any, cast

from pygments.formatters.terminal256 import EscapeSequence, Terminal256Formatter, TerminalTrueColorFormatter
from pygments.style import _ansimap, ansicolors


def _colorformat(word: str) -> str | None:
    if word in ansicolors:
        return word
    if word.startswith("#"):
        digits = word[1:]
        if len(digits) == 6:
            return digits
        if len(digits) == 3:
            return digits[0] * 2 + digits[1] * 2 + digits[2] * 2
        return None
    if word == "transparent" or word.startswith("var") or word.startswith("calc"):
        return word
    return None


def _color256(formatter: Any, color: str) -> object:
    if color == "":
        return None
    if color in ansicolors:
        return color
    return cast(object, formatter._color_index(color))


def _color_true(formatter: Any, color: str) -> object:
    if color == "":
        return None
    value = color
    if value in ansicolors:
        value = str(cast(object, _ansimap[value]))
    return cast(object, formatter._color_tuple(value))


def style_text(text: str, definition: str, base: str, true_color: bool) -> str:
    color = ""
    bgcolor = ""
    bold = False
    italic = False
    underline = False
    for word in base.split() + definition.split():
        if word == "bold":
            bold = True
        elif word == "nobold":
            bold = False
        elif word == "italic":
            italic = True
        elif word == "noitalic":
            italic = False
        elif word == "underline":
            underline = True
        elif word == "nounderline":
            underline = False
        elif word.startswith("bg:"):
            formatted = _colorformat(word[3:])
            if formatted is not None:
                bgcolor = formatted
        elif word not in ("noinherit", "roman", "sans", "mono") and not word.startswith("border:"):
            formatted = _colorformat(word)
            if formatted is not None:
                color = formatted
    seq: Any
    if true_color:
        tformatter: Any = TerminalTrueColorFormatter()
        seq = EscapeSequence(fg=_color_true(tformatter, color), bg=_color_true(tformatter, bgcolor), bold=bold, underline=underline, italic=italic)
        on = str(cast(object, seq.true_color_string()))
    else:
        formatter: Any = Terminal256Formatter()
        seq = EscapeSequence(fg=_color256(formatter, color), bg=_color256(formatter, bgcolor), bold=bold, underline=underline, italic=italic)
        on = str(cast(object, seq.color_string()))
    off = str(cast(object, seq.reset_string()))
    return "\n".join(on + piece + off if piece else piece for piece in text.split("\n"))
