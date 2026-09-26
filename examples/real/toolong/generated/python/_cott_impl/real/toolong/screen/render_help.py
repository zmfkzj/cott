from typing import Final

from rich.cells import get_character_cell_size

from cott_runtime import CottList, U64
from real.toolong.screen import text_runs, theme_color
from real.toolong.model_types import Rect, ScreenRow, StyledRun, StyledText, TermColor, TermColor_Rgb
from real.toolong.screen_types import ThemeColor_Accent, ThemeColor_Surface, ThemeColor_Text, ThemeColor_Thumb, ThemeColor_Track

_HELP_TITLE: Final[str] = " Help "
_FOOTER_TITLE: Final[str] = " ESCAPE to dismiss "


def _hex(color: TermColor) -> str:
    if isinstance(color, TermColor_Rgb):
        return f"#{color.red:02x}{color.green:02x}{color.blue:02x}"
    else:
        return "default"


def _code(fg: TermColor, bg: TermColor) -> str:
    return f"fg:{_hex(fg)} bg:{_hex(bg)}"


def _set(cells: list[tuple[str, str]], x: int, ch: str, style: str) -> None:
    if 0 <= x < len(cells):
        cells[x] = (ch, style)


def _edge(cells: list[tuple[str, str]], left: str, right: str, title: str, start: int, border: str, title_style: str) -> None:
    width = len(cells)
    for x in range(width):
        cells[x] = ("━", border)
    _set(cells, 0, left, border)
    _set(cells, width - 1, right, border)
    for k, ch in enumerate(title):
        if 1 <= start + k < width - 1:
            _set(cells, start + k, ch, title_style)


def _to_row(cells: list[tuple[str, str]]) -> ScreenRow:
    texts: list[str] = []
    styles: list[str] = []
    for ch, style in cells:
        if ch == "":
            continue
        if styles and styles[-1] == style:
            texts[-1] += ch
        else:
            texts.append(ch)
            styles.append(style)
    return ScreenRow(runs=CottList(values=[StyledRun(text=text, style=style) for text, style in zip(texts, styles)]))


def render_help(lines: CottList[StyledText], box: Rect, scroll: U64) -> CottList[ScreenRow]:
    width = box.width
    height = box.height
    surface = theme_color(ThemeColor_Surface())
    foreground = theme_color(ThemeColor_Text())
    base = _code(foreground, surface)
    border = _code(theme_color(ThemeColor_Accent()), surface)
    track = _code(foreground, theme_color(ThemeColor_Track()))
    thumb = _code(foreground, theme_color(ThemeColor_Thumb()))
    count = len(lines)
    inner = max(0, height - 2)
    content_width = max(0, width - 4)
    thumb_length = 0
    thumb_start = 0
    if inner > 0 and count > inner:
        thumb_length = max(1, inner * inner // count)
        thumb_start = (inner - thumb_length) * scroll // (count - inner)

    visible: dict[int, StyledText] = {}
    for index, line in enumerate(lines):
        if index >= scroll + inner:
            break
        if index >= scroll:
            visible[index - scroll] = line

    rows: list[ScreenRow] = []
    for y in range(height):
        cells: list[tuple[str, str]] = [(" ", base) for _ in range(width)]
        if y == 0:
            _edge(cells, "┏", "┓", _HELP_TITLE, 2, border, base)
        elif y == height - 1:
            _edge(cells, "┗", "┛", _FOOTER_TITLE, width - 2 - len(_FOOTER_TITLE), border, base)
        else:
            row = y - 1
            _set(cells, 0, "┃", border)
            _set(cells, width - 1, "┃", border)
            bar = thumb if thumb_length > 0 and thumb_start <= row < thumb_start + thumb_length else track
            for x in range(max(1, width - 3), width - 1):
                _set(cells, x, " ", bar)
            if content_width > 0 and row in visible:
                x = 1
                for run in text_runs(visible[row], base, 0, content_width, base):
                    for ch in run.text:
                        size = get_character_cell_size(ch)
                        if size <= 0:
                            continue
                        _set(cells, x, ch, run.style)
                        for extra in range(1, size):
                            _set(cells, x + extra, "", run.style)
                        x += size
        rows.append(_to_row(cells))
    return CottList(values=rows)
