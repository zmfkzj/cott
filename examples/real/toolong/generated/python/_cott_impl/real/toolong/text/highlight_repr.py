import re
from typing import Final

from cott_runtime import CottList
from rich.color import Color, ColorType
from rich.default_styles import DEFAULT_STYLES
from rich.style import Style

from real.toolong.model_types import StyledSpan, StyledText
from real.toolong.text_types import LOG_HIGHLIGHT_PATTERN

_MAX_LENGTH: Final[int] = 10000
_ANSI_NAMES: Final[str] = "ansiblack ansired ansigreen ansiyellow ansiblue ansimagenta ansicyan ansigray ansibrightblack ansibrightred ansibrightgreen ansibrightyellow ansibrightblue ansibrightmagenta ansibrightcyan ansiwhite"


def _hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}"


def _indexed_code(index: int) -> str:
    if index < 16:
        return _ANSI_NAMES.split(" ")[index]
    if index < 232:
        levels = (0, 95, 135, 175, 215, 255)
        cube = index - 16
        return _hex(levels[cube // 36], levels[(cube // 6) % 6], levels[cube % 6])
    gray = 8 + 10 * (index - 232)
    return _hex(gray, gray, gray)


def _color_code(color: Color) -> str:
    if color.type == ColorType.DEFAULT:
        return "default"
    if color.type == ColorType.TRUECOLOR and color.triplet is not None:
        triplet = color.triplet
        return _hex(triplet.red, triplet.green, triplet.blue)
    number = color.number
    if number is None:
        return "default"
    else:
        return _indexed_code(number)


def _style_code(style: Style) -> str:
    tokens: list[str] = []
    if style.color is not None:
        tokens.append("fg:" + _color_code(style.color))
    if style.bgcolor is not None:
        tokens.append("bg:" + _color_code(style.bgcolor))
    flags = (("bold", style.bold), ("dim", style.dim), ("italic", style.italic), ("underline", style.underline), ("reverse", style.reverse))
    for name, flag in flags:
        if flag is True:
            tokens.append(name)
        elif flag is False:
            tokens.append("no" + name)
    return " ".join(tokens)


def highlight_repr(text: StyledText) -> StyledText:
    plain = text.text
    if len(plain) >= _MAX_LENGTH:
        return text
    spans: list[StyledSpan] = []
    for span in text.spans:
        spans.append(span)
    codes: dict[str, str] = {}
    for match in re.finditer(LOG_HIGHLIGHT_PATTERN, plain):
        for name in match.re.groupindex:
            start, end = match.span(name)
            if start != -1 and end > start:
                code = codes.get(name)
                if code is None:
                    code = _style_code(DEFAULT_STYLES["repr." + name])
                    codes[name] = code
                spans.append(StyledSpan(start=start, end=end, style=code))
    return StyledText(text=plain, spans=CottList(values=spans))
