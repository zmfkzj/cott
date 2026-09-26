from typing import Final

from cott_runtime import CottList, U64
from real.toolong.screen import text_runs
from real.toolong.model_types import Rect, ScreenRow, StyledRun, StyledText

_BASE: Final[str] = "fg:#e1e1e1 bg:#24292f"
_BORDER: Final[str] = "fg:#0178d4 bg:#24292f"
_TRACK: Final[str] = "fg:#e1e1e1 bg:#14191f"
_THUMB: Final[str] = "fg:#e1e1e1 bg:#23568b"


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


def render_panel(lines: CottList[StyledText], rect: Rect, scroll_x: U64, scroll_y: U64, focused: bool) -> CottList[ScreenRow]:
    w = rect.width
    h = rect.height
    if w < 6 or h < 3:
        return CottList(values=[_row([StyledRun(text=" " * w, style=_BASE)]) for _ in range(h)])
    border = _BORDER if focused else _BASE
    items = [line for line in lines]
    n = len(items)
    ch = h - 3
    cw = w - 6
    thumb_start = -1
    thumb_len = 0
    if n > ch and ch > 0:
        thumb_len = max(1, ch * ch // n)
        thumb_start = (ch - thumb_len) * scroll_y // (n - ch)
    rows: list[ScreenRow] = []
    for r in range(h):
        if r == 0 or r == h - 1:
            left, right = ("┏", "┓") if r == 0 else ("┗", "┛")
            text = left + "━" * (w - 2) + right if focused else " " * w
            rows.append(_row([StyledRun(text=text, style=border)]))
            continue
        side = "┃" if focused else " "
        runs = [StyledRun(text=side, style=border), StyledRun(text=" ", style=_BASE)]
        if r == 1:
            runs.append(StyledRun(text=" " * (w - 3), style=_BASE))
        else:
            i = r - 2
            idx = scroll_y + i
            line = items[idx] if idx < n else StyledText(text="", spans=CottList(values=[]))
            runs.extend(text_runs(line, _BASE, scroll_x, cw, _BASE))
            runs.append(StyledRun(text=" ", style=_BASE))
            on_thumb = thumb_start >= 0 and thumb_start <= i < thumb_start + thumb_len
            runs.append(StyledRun(text="  ", style=_THUMB if on_thumb else _TRACK))
        runs.append(StyledRun(text=side, style=border))
        rows.append(_row(runs))
    return CottList(values=rows)
