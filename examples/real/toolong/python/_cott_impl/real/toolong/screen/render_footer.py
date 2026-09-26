from rich.cells import cell_len

from cott_runtime import CottList, U16
from real.toolong.model_types import ScreenRow, StyledSpan, StyledText, TermColor, TermColor_Rgb
from real.toolong.screen import paste_rows, text_runs, theme_color
from real.toolong.screen_types import ThemeColor_Success, ThemeColor_Surface, ThemeColor_TailBackground, ThemeColor_Text, ThemeColor_Warning
from real.toolong.view_types import FooterKey


def _hex(color: TermColor) -> str:
    if isinstance(color, TermColor_Rgb):
        return f"#{color.red:02x}{color.green:02x}{color.blue:02x}"
    else:
        return "default"


def _code(fg: TermColor, bg: TermColor, bold: bool) -> str:
    code = "fg:" + _hex(fg) + " bg:" + _hex(bg)
    return code + " bold" if bold else code


def _span(start: int, text: str, style: str, spans: list[StyledSpan]) -> int:
    end = start + len(text)
    spans.append(StyledSpan(start=start, end=end, style=style))
    return end


def render_footer(keys: CottList[FooterKey], width: U16, tail_badge: bool, meta: str) -> ScreenRow:
    surface = theme_color(ThemeColor_Surface())
    warning = theme_color(ThemeColor_Warning())
    success = theme_color(ThemeColor_Success())
    blank = _code(theme_color(ThemeColor_Text()), surface, False)
    key_style = _code(surface, warning, False)
    desc_style = _code(warning, surface, False)
    left_parts: list[str] = []
    left_spans: list[StyledSpan] = []
    pos = 0
    for key in keys:
        pos = _span(pos, key.display, key_style, left_spans)
        desc = " " + key.description + " "
        pos = _span(pos, desc, desc_style, left_spans)
        left_parts.append(key.display)
        left_parts.append(desc)
    left = StyledText(text="".join(left_parts), spans=CottList(values=left_spans))
    row = ScreenRow(runs=text_runs(left, blank, 0, width, blank))

    right_parts: list[str] = []
    right_spans: list[StyledSpan] = []
    pos = 0
    if tail_badge:
        right_parts.append("  TAIL ")
        pos = _span(1, " TAIL ", _code(success, theme_color(ThemeColor_TailBackground()), True), right_spans)
    meta_text = " " + meta + " "
    _span(pos, meta_text, _code(success, surface, False), right_spans)
    right_parts.append(meta_text)
    right_str = "".join(right_parts)
    right = StyledText(text=right_str, spans=CottList(values=right_spans))
    right_width = cell_len(right_str)
    visible = min(right_width, width)
    if visible == 0:
        return row
    right_row = ScreenRow(runs=text_runs(right, blank, right_width - visible, visible, blank))
    pasted = paste_rows(CottList(values=[row]), width - visible, 0, CottList(values=[right_row]))
    for result in pasted:
        return result
    return row
