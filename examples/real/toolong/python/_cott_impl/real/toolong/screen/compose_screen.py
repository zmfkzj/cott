from typing import cast

from rich.cells import cell_len, get_character_cell_size

from cott_runtime import CottList, Nothing, Opaque, Option, Some
from real.toolong.help import help_markdown, help_title
from real.toolong.model_types import Rect, ScreenRow, StyledRun, StyledText, TermColor, TermColor_Rgb
from real.toolong.screen import render_find_dialog, render_footer, render_goto, render_help_footer, render_log_lines, render_tabs, text_runs, theme_color
from real.toolong.screen_types import Cursor, Frame, FrameContent, ThemeColor, ThemeColor_Accent, ThemeColor_Error, ThemeColor_Panel, ThemeColor_Success, ThemeColor_Surface, ThemeColor_Text, ThemeColor_Warning
from real.toolong.view import footer_keys, viewer_layout
from real.toolong.view_types import Focus_FindInput, Focus_Lines, Focus_Panel, Focus_Tabs, Modal_Goto, Modal_Help, Notification, Severity_Error, Severity_Warning, TabView, ViewerState


def _c(color: ThemeColor) -> str:
    value: TermColor = theme_color(color)
    if isinstance(value, TermColor_Rgb):
        return f"#{value.red:02x}{value.green:02x}{value.blue:02x}"
    else:
        return "default"


def _style(fg: str, bg: str, bold: bool) -> str:
    return f"fg:{fg} bg:{bg}" + (" bold" if bold else "")


def _base() -> str:
    return _style(_c(ThemeColor_Text()), _c(ThemeColor_Surface()), False)


def _row(runs: list[StyledRun]) -> ScreenRow:
    merged: list[StyledRun] = []
    for run in runs:
        if run.text == "":
            continue
        if merged and merged[-1].style == run.style:
            merged[-1] = StyledRun(text=merged[-1].text + run.text, style=run.style)
        else:
            merged.append(run)
    return ScreenRow(runs=CottList(values=merged))


def _blank(width: int, style: str) -> ScreenRow:
    return _row([StyledRun(text=" " * width, style=style)])


def _cells(row: ScreenRow) -> list[tuple[str, str, str]]:
    cells: list[tuple[str, str, str]] = []
    for run in row.runs:
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


def _from_cells(cells: list[tuple[str, str, str]]) -> ScreenRow:
    count = len(cells)
    texts: list[str] = []
    styles: list[str] = []
    for index in range(count):
        text, style, kind = cells[index]
        if kind == "L" and (index + 1 >= count or cells[index + 1][2] != "R"):
            text = " "
        elif kind == "R" and (index == 0 or cells[index - 1][2] != "L"):
            text = " "
        if styles and styles[-1] == style:
            texts[-1] += text
        else:
            texts.append(text)
            styles.append(style)
    return _row([StyledRun(text=t, style=s) for t, s in zip(texts, styles)])


def _paste(rows: list[ScreenRow], x: int, y: int, placed: list[ScreenRow]) -> list[ScreenRow]:
    result = list(rows)
    for i in range(len(placed)):
        target = y + i
        if target >= len(result):
            break
        cells = _cells(result[target])
        width = len(cells)
        pasted = _cells(placed[i])
        for j in range(len(pasted)):
            column = x + j
            if column >= width:
                break
            cells[column] = pasted[j]
        result[target] = _from_cells(cells)
    return result


def _dim_code(code: str) -> str:
    tokens = code.split()
    colors = [t for t in tokens if t.startswith("fg:") or t.startswith("bg:")]
    attrs = set(t for t in tokens if not (t.startswith("fg:") or t.startswith("bg:")))
    attrs.add("dim")
    order = ["bold", "dim", "italic", "underline", "reverse"]
    return " ".join(colors + [a for a in order if a in attrs])


def _dim(rows: list[ScreenRow]) -> list[ScreenRow]:
    return [_row([StyledRun(text=run.text, style=_dim_code(run.style)) for run in row.runs]) for row in rows]


def _plain(text: str) -> StyledText:
    return StyledText(text=text, spans=CottList(values=[]))


def _panel_rows(tab: TabView, width: int, height: int, focused: bool, lines: tuple[StyledText, ...]) -> list[ScreenRow]:
    base = _base()
    border = _style(_c(ThemeColor_Accent()), _c(ThemeColor_Surface()), False)
    rows: list[ScreenRow] = []
    inner = max(0, width - 6)
    for r in range(height):
        if focused and width >= 2 and height >= 2 and (r == 0 or r == height - 1):
            left, right = ("┏", "┓") if r == 0 else ("┗", "┛")
            rows.append(_row([StyledRun(text=left + "━" * (width - 2) + right, style=border)]))
            continue
        if r == 0 or r == height - 1 or width < 2:
            rows.append(_blank(width, base))
            continue
        index = tab.panel_scroll_y + r - 1
        edge = StyledRun(text="┃", style=border) if focused else StyledRun(text=" ", style=base)
        if index < len(lines):
            body = [run for run in text_runs(lines[index], base, tab.panel_scroll_x, inner, base)]
        else:
            body = [StyledRun(text=" " * inner, style=base)]
        rows.append(_row([edge, StyledRun(text=" ", style=base)] + body + [StyledRun(text=" " * max(0, width - 3 - inner), style=base), edge]))
    return rows


def _with_panel(rows: list[ScreenRow], panel: Option[Rect], tab: TabView, focused: bool, lines: tuple[StyledText, ...]) -> list[ScreenRow]:
    if isinstance(panel, Some):
        p = panel.value
        return _paste(rows, p.x, p.y, _panel_rows(tab, p.width, p.height, focused, lines))
    else:
        return rows


def _toasts(rows: list[ScreenRow], notes: list[Notification], width: int, bottom: int) -> list[ScreenRow]:
    y = bottom
    tw = min(50, width)
    cw = max(0, tw - 4)
    panel = _c(ThemeColor_Panel())
    for note in reversed(notes):
        if isinstance(note.severity, Severity_Error):
            color = _c(ThemeColor_Error())
        elif isinstance(note.severity, Severity_Warning):
            color = _c(ThemeColor_Warning())
        else:
            color = _c(ThemeColor_Success())
        edge = StyledRun(text="▌", style=_style(color, panel, False))
        body_style = _style(_c(ThemeColor_Text()), panel, False)
        texts: list[tuple[str, str]] = []
        if note.title != "":
            texts.append((note.title, _style(color, panel, True)))
        texts.append((note.message, body_style))
        content: list[ScreenRow] = [_row([edge, StyledRun(text=" " * max(0, tw - 1), style=body_style)])]
        for text, style in texts:
            inner = [run for run in text_runs(_plain(text), style, 0, cw, style)]
            content.append(_row([edge, StyledRun(text="  ", style=body_style)] + inner + [StyledRun(text=" " * max(0, tw - 3 - cw), style=body_style)]))
        content.append(_row([edge, StyledRun(text=" " * max(0, tw - 1), style=body_style)]))
        top = y - len(content)
        if tw < 2 or top < 0:
            break
        rows = _paste(rows, max(0, width - tw - 1), top, content)
        y = top
    return rows


def compose_screen(viewer: ViewerState, content: FrameContent) -> Frame:
    width = viewer.width
    height = viewer.height
    base = _base()
    rows = [_blank(width, base) for _ in range(height)]
    layout = viewer_layout(viewer)
    keys = footer_keys(viewer)
    tabs = [tab for tab in viewer.tabs]
    footer_y = layout.footer.y
    cursor: Option[Cursor] = Nothing()
    find_cursor: Option[Cursor] = Nothing()
    tail_badge = False
    if tabs and viewer.active < len(tabs):
        tab = tabs[viewer.active]
        tail_badge = tab.tail and tab.can_tail
        if len(tabs) > 1:
            rows = _paste(rows, 0, 0, [r for r in render_tabs(CottList(values=[t.title for t in tabs]), viewer.active, width, isinstance(viewer.focus, Focus_Tabs))])
        find = layout.find
        if isinstance(find, Some):
            view = render_find_dialog(tab, width, viewer.focus, viewer.suggestion)
            rows = _paste(rows, find.value.x, find.value.y, [r for r in view.rows])
            vc = view.cursor
            if isinstance(vc, Some) and isinstance(viewer.focus, Focus_FindInput):
                find_cursor = Some(value=Cursor(x=find.value.x + vc.value.x, y=find.value.y + vc.value.y))
            else:
                find_cursor = Nothing()
        else:
            find_cursor = Nothing()
        box = layout.lines_box
        log_rows = cast(tuple[ScreenRow, ...], render_log_lines(tab, layout, isinstance(viewer.focus, Focus_Lines), content.lines).unwrap())
        rows = _paste(rows, box.x, box.y, list(log_rows))
        panel_lines = cast(tuple[StyledText, ...], content.panel.unwrap())
        rows = _with_panel(rows, layout.panel, tab, isinstance(viewer.focus, Focus_Panel), panel_lines)
        if not tab.tail and tab.pending_lines > 0 and footer_y > 0:
            label = f" +{tab.pending_lines:,} lines "
            x = max(0, box.x + (box.width - cell_len(label)) // 2)
            rows = _paste(rows, x, footer_y - 1, [_row([StyledRun(text=label, style=_style(_c(ThemeColor_Success()), _c(ThemeColor_Panel()), True))])])
    if height > 0:
        rows = _paste(rows, 0, footer_y, [render_footer(keys, width, tail_badge, content.meta)])
    modal = viewer.modal
    if isinstance(modal, Modal_Help):
        rows = _dim(rows)
        bw = max(0, width - 16)
        bh = max(0, height - 9)
        cw = max(0, bw - 4)
        markdown = cast(tuple[StyledText, ...], help_markdown(cw).unwrap())
        lines = [line for line in help_title(cw)] + list(markdown)
        boxed: list[ScreenRow] = []
        for r in range(bh):
            index = modal.scroll + r - 1
            if 0 < r < bh - 1 and index < len(lines):
                boxed.append(_row([StyledRun(text="  ", style=base)] + [run for run in text_runs(lines[index], base, 0, cw, base)] + [StyledRun(text=" " * max(0, bw - 2 - cw), style=base)]))
            else:
                boxed.append(_blank(bw, base))
        rows = _paste(rows, 8, 4, boxed)
        if height > 0:
            rows = _paste(rows, 0, footer_y, [render_help_footer(keys, width)])
    elif isinstance(modal, Modal_Goto):
        rows = _dim(rows)
        placed = render_goto(modal.input, width, height)
        rows = _paste(rows, placed.x, placed.y, [r for r in placed.rows])
        first = max(0, modal.input.cursor - 9)
        before = modal.input.value[first:modal.input.cursor]
        cursor = Some(value=Cursor(x=placed.x + 3 + cell_len(before), y=placed.y + 1))
    else:
        cursor = find_cursor
    rows = _toasts(rows, [note for note in viewer.notifications], width, footer_y)
    return Frame(rows=Opaque(tag="screen_rows", value=tuple(rows)), cursor=cursor)
