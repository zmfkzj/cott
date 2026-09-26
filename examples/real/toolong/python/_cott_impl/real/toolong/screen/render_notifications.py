from typing import Final

from cott_runtime import CottList, U16
from real.toolong.model_types import ScreenRow, StyledRun, StyledText, TermColor, TermColor_Indexed, TermColor_Rgb
from real.toolong.screen import text_runs, theme_color
from real.toolong.screen_types import PlacedRows, ThemeColor_Error, ThemeColor_ErrorDark, ThemeColor_Panel, ThemeColor_Success, ThemeColor_SuccessDark, ThemeColor_Text, ThemeColor_Warning, ThemeColor_WarningDark
from real.toolong.text import wrap_text
from real.toolong.view_types import Notification, Severity_Information, Severity_Warning


_ANSI: Final[str] = "ansiblack ansired ansigreen ansiyellow ansiblue ansimagenta ansicyan ansigray ansibrightblack ansibrightred ansibrightgreen ansibrightyellow ansibrightblue ansibrightmagenta ansibrightcyan ansiwhite"


def _hex(color: TermColor) -> str:
    if isinstance(color, TermColor_Rgb):
        return "#%02x%02x%02x" % (color.red, color.green, color.blue)
    elif isinstance(color, TermColor_Indexed):
        index = color.index
        if index < 16:
            return _ANSI.split(" ")[index]
        if index < 232:
            levels = (0, 95, 135, 175, 215, 255)
            cube = index - 16
            return "#%02x%02x%02x" % (levels[cube // 36], levels[(cube // 6) % 6], levels[cube % 6])
        gray = 8 + 10 * (index - 232)
        return "#%02x%02x%02x" % (gray, gray, gray)
    else:
        return "default"


def _code(foreground: TermColor, background: TermColor, bold: bool) -> str:
    code = "fg:" + _hex(foreground) + " bg:" + _hex(background)
    if bold:
        code += " bold"
    return code


def _row(runs: list[StyledRun]) -> ScreenRow:
    merged: list[StyledRun] = []
    for run in runs:
        if not run.text:
            continue
        if merged and merged[-1].style == run.style:
            merged[-1] = StyledRun(text=merged[-1].text + run.text, style=run.style)
        else:
            merged.append(run)
    return ScreenRow(runs=CottList(values=merged))


def _toast(note: Notification, width: int) -> list[ScreenRow]:
    panel = theme_color(ThemeColor_Panel())
    text_color = theme_color(ThemeColor_Text())
    if isinstance(note.severity, Severity_Information):
        bar_color = theme_color(ThemeColor_Success())
        title_color = theme_color(ThemeColor_SuccessDark())
    elif isinstance(note.severity, Severity_Warning):
        bar_color = theme_color(ThemeColor_Warning())
        title_color = theme_color(ThemeColor_WarningDark())
    else:
        bar_color = theme_color(ThemeColor_Error())
        title_color = theme_color(ThemeColor_ErrorDark())
    plain = _code(text_color, panel, False)
    bar = StyledRun(text="▌", style=_code(bar_color, panel, False))
    content_width = max(0, width - 4)
    left = min(1, max(0, width - 2))
    right = max(0, width - 1 - left - content_width)
    blank = _row([bar, StyledRun(text=" " * (width - 1), style=plain)])
    rows: list[ScreenRow] = [blank]
    lines: list[tuple[StyledText, str]] = []
    if note.title:
        lines.append((StyledText(text=note.title, spans=CottList(values=[])), _code(title_color, panel, True)))
    for line in wrap_text(StyledText(text=note.message, spans=CottList(values=[])), content_width):
        lines.append((line, plain))
    for line, base in lines:
        if content_width > 0:
            content = [run for run in text_runs(line, base, 0, content_width, plain)]
            rows.append(_row([bar, StyledRun(text=" " * left, style=plain), *content, StyledRun(text=" " * right, style=plain)]))
        else:
            rows.append(blank)
    rows.append(blank)
    return rows


def render_notifications(notifications: CottList[Notification], width: U16, height: U16) -> CottList[PlacedRows]:
    toast_width = min(60, width // 2)
    if toast_width == 0:
        return CottList(values=[])
    x = width - 1 - toast_width
    bottom = height - 2
    placed: list[PlacedRows] = []
    notes = [note for note in notifications]
    for note in reversed(notes):
        rows = _toast(note, toast_width)
        top = bottom - len(rows) + 1
        if top < 0:
            break
        placed.append(PlacedRows(x=x, y=top, rows=CottList(values=rows)))
        bottom = top - 2
    placed.reverse()
    return CottList(values=placed)
