import typing
from typing import Final, Literal

from cott_runtime import CottList, Opaque, Some
from rich.cells import cell_len, get_character_cell_size

from real.toolong.screen import text_runs, theme_color
from real.toolong.text import highlight_find
from real.toolong.model_types import FindQuery, ScreenRow, StyledRun, StyledSpan, StyledText, TermColor, TermColor_Rgb
from real.toolong.screen_types import ThemeColor_Accent, ThemeColor_LineNumber, ThemeColor_Primary, ThemeColor_Surface, ThemeColor_Text, ThemeColor_Thumb, ThemeColor_Track, ThemeColor_Underline, ThemeColor_Warning
from real.toolong.view_types import TabView, ViewerLayout

_LOADING: Final[str] = "●●●●●"
_ATTRS: Final[str] = "bold dim italic underline reverse"


def _hex(color: TermColor) -> str:
    if isinstance(color, TermColor_Rgb):
        return "#%02x%02x%02x" % (color.red, color.green, color.blue)
    else:
        return "default"


def _code(fg: TermColor, bg: TermColor) -> str:
    return "fg:" + _hex(fg) + " bg:" + _hex(bg)


def _add_dim(code: str) -> str:
    tokens = code.split(" ")
    if "dim" in tokens:
        return code
    colors = [t for t in tokens if t.startswith("fg:") or t.startswith("bg:")]
    attrs = [a for a in _ATTRS.split(" ") if a in tokens or a == "dim"]
    return " ".join(colors + attrs)


def _plain(text: str, style: str) -> list[tuple[str, str, str]]:
    return [(ch, style, "n") for ch in text]


def _cells(runs: list[StyledRun]) -> list[tuple[str, str, str]]:
    cells: list[tuple[str, str, str]] = []
    for run in runs:
        for ch in run.text:
            size = get_character_cell_size(ch)
            if size <= 0:
                if cells:
                    prev = cells[-1]
                    cells[-1] = (prev[0] + ch, prev[1], prev[2])
            elif size == 1:
                cells.append((ch, run.style, "n"))
            else:
                cells.append((ch, run.style, "L"))
                cells.append(("", run.style, "R"))
    return cells


def _paste(grid: list[list[tuple[str, str, str]]], x: int, y: int, cells: list[tuple[str, str, str]]) -> None:
    if y < 0 or y >= len(grid):
        return
    row = grid[y]
    for j in range(len(cells)):
        column = x + j
        if column >= len(row):
            break
        if column >= 0:
            row[column] = cells[j]


def _row(cells: list[tuple[str, str, str]]) -> ScreenRow:
    count = len(cells)
    runs: list[StyledRun] = []
    for index in range(count):
        text, style, kind = cells[index]
        if kind == "L" and (index + 1 >= count or cells[index + 1][2] != "R"):
            text = " "
        elif kind == "R" and (index == 0 or cells[index - 1][2] != "L"):
            text = " "
        if text == "":
            continue
        if runs and runs[-1].style == style:
            runs[-1] = StyledRun(text=runs[-1].text + text, style=style)
        else:
            runs.append(StyledRun(text=text, style=style))
    return ScreenRow(runs=CottList(values=runs))


def _thumb(track: int, virtual: int, scroll: int) -> tuple[int, int]:
    if virtual <= track or track <= 0:
        return (0, 0)
    length = max(1, track * track // virtual)
    start = (track - length) * scroll // (virtual - track)
    start = max(0, min(start, track - length))
    return (start, length)


def _text_row(tab: TabView, layout: ViewerLayout, lines: tuple[StyledText, ...], r: int, base: str) -> list[StyledRun]:
    tw = layout.text.width
    th = layout.text.height
    primary = _hex(theme_color(ThemeColor_Primary()))
    blank = [StyledRun(text=" " * tw, style=base)] if tw > 0 else []
    if tab.loading:
        if r != th // 2 or tw <= 0:
            return blank
        start = (tw - 5) // 2
        offset = 0
        prefix = ""
        if start >= 0:
            prefix = " " * start
        else:
            offset = -start
        accent = "fg:" + _hex(theme_color(ThemeColor_Accent()))
        styled = StyledText(text=prefix + _LOADING, spans=CottList(values=[StyledSpan(start=len(prefix), end=len(prefix) + 5, style=accent)]))
        return [x for x in text_runs(styled, base, offset, tw, base)]
    index = tab.scroll_y + r
    if index >= tab.line_count or r >= len(lines):
        return blank
    text = lines[r]
    pointer = tab.pointer
    if isinstance(pointer, Some):
        is_pointer = pointer.value == index
    else:
        is_pointer = False
    if is_pointer:
        spans = [s for s in text.spans] + [StyledSpan(start=0, end=len(text.text), style="bg:" + primary + " bold")]
        text = StyledText(text=text.text, spans=CottList(values=spans))
    value = tab.find_input.value
    if tab.show_find and value != "":
        text = highlight_find(text, FindQuery(text=value, regex=tab.regex, case_sensitive=tab.case_sensitive))
    fill = "fg:" + _hex(theme_color(ThemeColor_Text())) + " bg:" + primary if is_pointer else base
    gutter = min(layout.gutter, tw)
    runs: list[StyledRun] = []
    if gutter > 0:
        gtext = ""
        gspans: list[StyledSpan] = []
        if tab.line_numbers:
            number = str(index + 1) + " "
            if is_pointer:
                nstyle = "fg:" + _hex(theme_color(ThemeColor_Warning())) + " bold"
            else:
                nstyle = "fg:" + _hex(theme_color(ThemeColor_LineNumber()))
            gspans.append(StyledSpan(start=0, end=len(number), style=nstyle))
            gtext = number
        gtext += "👉" if is_pointer else " "
        runs.extend(text_runs(StyledText(text=gtext, spans=CottList(values=gspans)), base, 0, gutter, base))
    rest = tw - gutter
    if rest > 0:
        runs.extend(text_runs(text, base, tab.scroll_x, rest, fill))
    return runs


def render_log_lines(tab: TabView, layout: ViewerLayout, focused: bool, lines: Opaque[Literal["styled_lines"]]) -> Opaque[Literal["screen_rows"]]:
    texts = typing.cast(tuple[StyledText, ...], lines.unwrap())
    w = layout.lines_box.width
    h = layout.lines_box.height
    tw = layout.text.width
    th = layout.text.height
    fg = theme_color(ThemeColor_Text())
    surface = theme_color(ThemeColor_Surface())
    base = _code(fg, surface)
    accent = _code(theme_color(ThemeColor_Accent()), surface)
    grid: list[list[tuple[str, str, str]]] = []
    for y in range(h):
        if focused and w >= 2 and h >= 2:
            if y == 0:
                grid.append(_plain("┏" + "━" * (w - 2) + "┓", accent))
            elif y == h - 1:
                grid.append(_plain("┗" + "━" * (w - 2) + "┛", accent))
            else:
                grid.append(_plain("┃", accent) + _plain(" " * (w - 2), base) + _plain("┃", accent))
        else:
            grid.append(_plain(" " * w, base))

    for r in range(th):
        runs = _text_row(tab, layout, texts, r, base)
        if tab.scan_tint:
            runs = [StyledRun(text=x.text, style=_add_dim(x.style)) for x in runs]
        _paste(grid, 1, 1 + r, _cells(runs))

    track = _code(fg, theme_color(ThemeColor_Track()))
    thumb = _code(fg, theme_color(ThemeColor_Thumb()))
    vstart, vlen = _thumb(th, tab.line_count, tab.scroll_y)
    for r in range(th):
        on = vlen > 0 and vstart <= r < vstart + vlen
        _paste(grid, 1 + tw, 1 + r, _plain("  ", thumb if on else track))

    virtual = tab.content_width + (layout.gutter if isinstance(tab.pointer, Some) or tab.line_numbers else 0)
    hstart, hlen = _thumb(tw, virtual, tab.scroll_x)
    hcells = _plain(" " * hstart, track) + _plain(" " * hlen, thumb) + _plain(" " * max(0, tw + 2 - hstart - hlen), track)
    _paste(grid, 1, 1 + th, hcells)

    bw = tw - 8
    if focused and tab.scan_message != "" and bw > 0:
        box = _code(fg, theme_color(ThemeColor_Primary()))
        primary = _hex(theme_color(ThemeColor_Primary()))
        message = tab.scan_message
        mleft = max(0, (bw - cell_len(message)) // 2)
        msg = StyledText(text=" " * mleft + message, spans=CottList(values=[]))
        msg_cells = _cells([x for x in text_runs(msg, box, 0, bw, box)])
        bar_w = min(32, bw - 4)
        if bar_w > 0:
            done = min(bar_w, max(0, round(tab.scan_progress * bar_w)))
            left = (bw - bar_w) // 2
            bar = (
                _plain(" " * left, box)
                + _plain("━" * done, "fg:" + _hex(theme_color(ThemeColor_Warning())) + " bg:" + primary)
                + _plain("━" * (bar_w - done), "fg:" + _hex(theme_color(ThemeColor_Underline())) + " bg:" + primary)
                + _plain(" " * (bw - left - bar_w), box)
            )
        else:
            bar = _plain(" " * bw, box)
        box_rows = [_plain(" " * bw, box), msg_cells, bar, _plain(" " * bw, box)]
        for i in range(4):
            if 2 + i < th:
                _paste(grid, 1 + 4, 1 + 2 + i, box_rows[i])
    return Opaque(tag="screen_rows", value=tuple(_row(cells) for cells in grid))
