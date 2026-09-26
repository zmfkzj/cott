from rich.cells import get_character_cell_size

from cott_runtime import CottList, U16, U32
from real.toolong.model_types import ScreenRow, StyledRun, TermColor, TermColor_Rgb
from real.toolong.screen import theme_color
from real.toolong.screen_types import (
    ThemeColor_Accent,
    ThemeColor_Muted,
    ThemeColor_Panel,
    ThemeColor_Surface,
    ThemeColor_Text,
    ThemeColor_Underline,
)


def _hex(color: TermColor) -> str:
    if isinstance(color, TermColor_Rgb):
        return f"#{color.red:02x}{color.green:02x}{color.blue:02x}"
    else:
        return "default"


def _code(fg: TermColor, bg: TermColor, bold: bool) -> str:
    code = "fg:" + _hex(fg) + " bg:" + _hex(bg)
    return code + " bold" if bold else code


def _put_title(cells: list[tuple[str, str]], start: int, title: str, style: str) -> int:
    col = start
    width = len(cells)
    for char in title:
        size = get_character_cell_size(char)
        if size <= 0:
            continue
        if col < width:
            if size == 1:
                cells[col] = (char, style)
            elif col + size <= width:
                cells[col] = (char, style)
                cells[col + 1] = ("", style)
            else:
                cells[col] = (" ", style)
        col += size
    return col


def _row(cells: list[tuple[str, str]]) -> ScreenRow:
    runs: list[StyledRun] = []
    texts: list[str] = []
    styles: list[str] = []
    for char, style in cells:
        if styles and styles[-1] == style:
            texts[-1] += char
        else:
            texts.append(char)
            styles.append(style)
    for text, style in zip(texts, styles):
        runs.append(StyledRun(text=text, style=style))
    return ScreenRow(runs=CottList(values=runs))


def render_tabs(titles: CottList[str], active: U32, width: U16, focused: bool) -> CottList[ScreenRow]:
    surface = theme_color(ThemeColor_Surface())
    text = theme_color(ThemeColor_Text())
    blank = _code(text, surface, False)
    selected = _code(text, surface, True)
    muted = _code(theme_color(ThemeColor_Muted()), surface, False)
    underline = _code(theme_color(ThemeColor_Underline()), surface, False)
    bar = theme_color(ThemeColor_Accent()) if focused else theme_color(ThemeColor_Panel())
    highlight = _code(bar, surface, False)

    row0 = [(" ", blank)] * width
    row1 = [(" ", blank)] * width
    row2 = [("━", underline)] * width
    col = 1
    index = 0
    for title in titles:
        start = col + 1
        is_active = index == active
        end = _put_title(row1, start, title, selected if is_active else muted)
        if is_active:
            for cell in range(start, min(end, width)):
                row2[cell] = ("━", highlight)
            if start - 1 < width:
                row2[start - 1] = ("╸", underline)
            if end < width:
                row2[end] = ("╺", underline)
        col = end + 2
        index += 1
    return CottList(values=[_row(row0), _row(row1), _row(row2)])
