from typing import Final

from rich.color import Color, ColorType
from rich.style import Style
from rich.text import Text

from cott_runtime import CottList
from real.toolong.model_types import StyledSpan, StyledText

_ANSI_NAMES: Final[str] = "ansiblack ansired ansigreen ansiyellow ansiblue ansimagenta ansicyan ansigray ansibrightblack ansibrightred ansibrightgreen ansibrightyellow ansibrightblue ansibrightmagenta ansibrightcyan ansiwhite"
_CUBE_LEVELS: Final[str] = "0 95 135 175 215 255"


def _hex(red: int, green: int, blue: int) -> str:
    return "#%02x%02x%02x" % (red, green, blue)


def _indexed_code(index: int) -> str:
    if index < 16:
        return _ANSI_NAMES.split(" ")[index]
    if index < 232:
        levels = [int(level) for level in _CUBE_LEVELS.split(" ")]
        offset = index - 16
        return _hex(levels[offset // 36], levels[(offset // 6) % 6], levels[offset % 6])
    gray = 8 + 10 * (index - 232)
    return _hex(gray, gray, gray)


def _color_code(color: Color) -> str:
    if color.type == ColorType.DEFAULT:
        return "default"
    if color.type == ColorType.TRUECOLOR:
        triplet = color.get_truecolor()
        return _hex(triplet.red, triplet.green, triplet.blue)
    number = color.number
    if isinstance(number, int):
        return _indexed_code(number)
    else:
        raise TypeError("rich palette color without a number")


def _style_code(style: Style) -> str:
    tokens: list[str] = []
    color = style.color
    if isinstance(color, Color):
        tokens.append("fg:" + _color_code(color))
    bgcolor = style.bgcolor
    if isinstance(bgcolor, Color):
        tokens.append("bg:" + _color_code(bgcolor))
    flags: list[tuple[str, bool | None]] = [("bold", style.bold), ("dim", style.dim), ("italic", style.italic), ("underline", style.underline), ("reverse", style.reverse)]
    for name, value in flags:
        if value is True:
            tokens.append(name)
        elif value is False:
            tokens.append("no" + name)
    return " ".join(tokens)


def _span_style(raw_style: str | Style) -> Style:
    if isinstance(raw_style, Style):
        return raw_style
    else:
        return Style.parse(raw_style)


def decode_ansi(line: str) -> StyledText:
    rich_text = Text.from_ansi(line)
    spans: list[StyledSpan] = []
    for span in rich_text.spans:
        spans.append(StyledSpan(start=span.start, end=span.end, style=_style_code(_span_style(span.style))))
    return StyledText(text=rich_text.plain, spans=CottList(values=spans))
