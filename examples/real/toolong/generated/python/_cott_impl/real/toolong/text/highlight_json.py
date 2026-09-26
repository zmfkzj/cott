from typing import Final

from rich.color import Color, ColorType
from rich.default_styles import DEFAULT_STYLES
from rich.highlighter import JSONHighlighter
from rich.style import Style
from rich.text import Text

from cott_runtime import CottList
from real.toolong.model_types import StyledSpan, StyledText

# rich.Text strips BEL, BS, VT, FF and CR. Substitutes keep offsets and match every
# JSONHighlighter pattern identically: CR -> space (non-word, "." matches, JSON
# whitespace); the others -> NUL (non-word, "." matches, not JSON whitespace).
_STRIPPED_OTHER: Final[str] = "\x07\x08\x0b\x0c"
_CARRIAGE_RETURN: Final[str] = "\r"
_ANSI_NAMES: Final[str] = "ansiblack ansired ansigreen ansiyellow ansiblue ansimagenta ansicyan ansigray ansibrightblack ansibrightred ansibrightgreen ansibrightyellow ansibrightblue ansibrightmagenta ansibrightcyan ansiwhite"
_CUBE_LEVELS: Final[str] = "0 95 135 175 215 255"


def _protect(plain: str) -> str:
    protected = plain.replace(_CARRIAGE_RETURN, " ")
    for code in _STRIPPED_OTHER:
        protected = protected.replace(code, "\x00")
    return protected


def _hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}"


def _color_code(color: Color) -> str:
    if color.type == ColorType.DEFAULT:
        return "default"
    if color.type == ColorType.TRUECOLOR and color.triplet is not None:
        return _hex(color.triplet.red, color.triplet.green, color.triplet.blue)
    number = color.number if color.number is not None else 0
    if number < 16:
        return _ANSI_NAMES.split(" ")[number]
    if number < 232:
        levels = [int(level) for level in _CUBE_LEVELS.split(" ")]
        cube = number - 16
        return _hex(levels[cube // 36], levels[(cube // 6) % 6], levels[cube % 6])
    gray = 8 + 10 * (number - 232)
    return _hex(gray, gray, gray)


def _style_code(style: str | Style) -> str:
    resolved: Style = DEFAULT_STYLES[style] if isinstance(style, str) else style
    tokens: list[str] = []
    if resolved.color is not None:
        tokens.append("fg:" + _color_code(resolved.color))
    if resolved.bgcolor is not None:
        tokens.append("bg:" + _color_code(resolved.bgcolor))
    flags: list[tuple[str, bool | None]] = [
        ("bold", resolved.bold),
        ("dim", resolved.dim),
        ("italic", resolved.italic),
        ("underline", resolved.underline),
        ("reverse", resolved.reverse),
    ]
    for name, flag in flags:
        if flag is True:
            tokens.append(name)
        elif flag is False:
            tokens.append("no" + name)
    return " ".join(tokens)


def highlight_json(text: StyledText) -> StyledText:
    rich_text = Text(_protect(text.text))
    JSONHighlighter().highlight(rich_text)
    spans: list[StyledSpan] = [span for span in text.spans]
    for span in rich_text.spans:
        spans.append(StyledSpan(start=span.start, end=span.end, style=_style_code(span.style)))
    return StyledText(text=text.text, spans=CottList(values=spans))
