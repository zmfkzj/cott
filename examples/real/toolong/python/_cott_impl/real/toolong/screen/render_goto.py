from typing import Final

from cott_runtime import CottList, U16
from real.toolong.keys_types import TextInput
from real.toolong.model_types import ScreenRow, StyledRun, StyledText, TermColor_Rgb
from real.toolong.screen import text_runs, theme_color
from real.toolong.screen_types import PlacedRows, ThemeColor, ThemeColor_Accent, ThemeColor_Muted, ThemeColor_Surface, ThemeColor_Text

_BOX: Final[int] = 16
_AREA: Final[int] = 10
_PLACEHOLDER: Final[str] = "Enter line number"


def _hex(color: ThemeColor) -> str:
    value = theme_color(color)
    if isinstance(value, TermColor_Rgb):
        return f"#{value.red:02x}{value.green:02x}{value.blue:02x}"
    else:
        return "default"


def _style(color: ThemeColor) -> str:
    return "fg:" + _hex(color) + " bg:" + _hex(ThemeColor_Surface())


def _merge(runs: list[StyledRun]) -> ScreenRow:
    out: list[StyledRun] = []
    for run in runs:
        if not run.text:
            continue
        if out and out[-1].style == run.style:
            out[-1] = StyledRun(text=out[-1].text + run.text, style=run.style)
        else:
            out.append(run)
    return ScreenRow(runs=CottList(values=out))


def render_goto(input: TextInput, width: U16, height: U16) -> PlacedRows:
    border = _style(ThemeColor_Accent())
    text = _style(ThemeColor_Text())
    muted = _style(ThemeColor_Muted())
    area: list[StyledRun] = []
    if len(input.value) == 0:
        for run in text_runs(StyledText(text=_PLACEHOLDER, spans=CottList(values=[])), muted, 0, _AREA, text):
            area.append(run)
    else:
        start = max(0, input.cursor - (_AREA - 1))
        for run in text_runs(StyledText(text=input.value[start:], spans=CottList(values=[])), text, 0, _AREA, text):
            area.append(run)
    top = _merge([StyledRun(text="▊" + "▔" * (_BOX - 2) + "▎", style=border)])
    middle = _merge([StyledRun(text="▊", style=border), StyledRun(text="  ", style=text)] + area + [StyledRun(text="  ", style=text), StyledRun(text="▎", style=border)])
    bottom = _merge([StyledRun(text="▊" + "▁" * (_BOX - 2) + "▎", style=border)])
    return PlacedRows(x=max(0, width - 19), y=max(0, height - 6), rows=CottList(values=[top, middle, bottom]))
