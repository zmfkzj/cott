import io
from typing import Final, Literal

from rich.color import Color, ColorType
from rich.console import Console
from rich.markdown import Markdown
from rich.style import Style

from cott_runtime import CottList, Opaque, U16
from real.toolong.help_types import HELP_MARKDOWN
from real.toolong.model_types import StyledSpan, StyledText

_ANSI_NAMES: Final[str] = "ansiblack ansired ansigreen ansiyellow ansiblue ansimagenta ansicyan ansigray ansibrightblack ansibrightred ansibrightgreen ansibrightyellow ansibrightblue ansibrightmagenta ansibrightcyan ansiwhite"


def _hex(red: int, green: int, blue: int) -> str:
    return "#%02x%02x%02x" % (red, green, blue)


def _cube_level(value: int) -> int:
    if value == 0:
        return 0
    else:
        return 55 + 40 * value


def _indexed_name(index: int) -> str:
    if index < 16:
        return _ANSI_NAMES.split(" ")[index]
    if index < 232:
        cube = index - 16
        return _hex(_cube_level(cube // 36), _cube_level((cube // 6) % 6), _cube_level(cube % 6))
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
        return _indexed_name(number)
    else:
        raise TypeError("rich palette color without a number")


def _flag_token(name: str, value: bool | None) -> list[str]:
    if value is True:
        return [name]
    if value is False:
        return ["no" + name]
    return []


def _style_code(style: Style) -> str:
    tokens: list[str] = []
    color = style.color
    if isinstance(color, Color):
        tokens.append("fg:" + _color_code(color))
    bgcolor = style.bgcolor
    if isinstance(bgcolor, Color):
        tokens.append("bg:" + _color_code(bgcolor))
    tokens.extend(_flag_token("bold", style.bold))
    tokens.extend(_flag_token("dim", style.dim))
    tokens.extend(_flag_token("italic", style.italic))
    tokens.extend(_flag_token("underline", style.underline))
    tokens.extend(_flag_token("reverse", style.reverse))
    return " ".join(tokens)


def help_markdown(width: U16) -> Opaque[Literal["toolong.help-markdown"]]:
    console = Console(width=max(1, width - 4), color_system="truecolor", force_terminal=True, file=io.StringIO())
    lines = console.render_lines(Markdown(HELP_MARKDOWN), pad=False)
    result: list[StyledText] = []
    for line in lines:
        raw = "".join(segment.text for segment in line)
        text = "  " + raw.rstrip(" ")
        limit = len(text)
        spans: list[StyledSpan] = []
        offset = 2
        for segment in line:
            start = offset
            offset += len(segment.text)
            style = segment.style
            if isinstance(style, Style):
                end = min(offset, limit)
                if start < end:
                    spans.append(StyledSpan(start=start, end=end, style=_style_code(style)))
        result.append(StyledText(text=text, spans=CottList(values=spans)))
    return Opaque(tag="toolong.help-markdown", value=tuple(result))
