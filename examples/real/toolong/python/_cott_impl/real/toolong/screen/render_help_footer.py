from cott_runtime import CottList, U16
from real.toolong.model_types import ScreenRow, StyledSpan, StyledText, TermColor, TermColor_Indexed, TermColor_Rgb
from real.toolong.screen import text_runs, theme_color
from real.toolong.screen_types import ThemeColor_Accent, ThemeColor_AccentDark, ThemeColor_Text
from real.toolong.view_types import FooterKey


def _hex(color: TermColor) -> str:
    if isinstance(color, TermColor_Rgb):
        return "#%02x%02x%02x" % (color.red, color.green, color.blue)
    elif isinstance(color, TermColor_Indexed):
        return "default"
    else:
        return "default"


def render_help_footer(keys: CottList[FooterKey], width: U16) -> ScreenRow:
    base = "fg:" + _hex(theme_color(ThemeColor_Text())) + " bg:" + _hex(theme_color(ThemeColor_Accent()))
    key_style = "bg:" + _hex(theme_color(ThemeColor_AccentDark())) + " bold"
    parts: list[str] = []
    spans: list[StyledSpan] = []
    position = 0
    for key in keys:
        key_text = " " + key.display + " "
        spans.append(StyledSpan(start=position, end=position + len(key_text), style=key_style))
        position += len(key_text)
        description = " " + key.description + " "
        position += len(description)
        parts.append(key_text)
        parts.append(description)
    text = StyledText(text="".join(parts), spans=CottList(values=spans))
    return ScreenRow(runs=text_runs(text, base, 0, width, base))
