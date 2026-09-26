from cott_runtime import U16, U64, CottList
from wcwidth import wcwidth

from real.harlequin.style_types import StyledLine, StyledSpan


def _fit(text: str, remaining: int) -> tuple[str, int]:
    used = 0
    chars: list[str] = []
    for ch in text:
        w = wcwidth(ch)
        cw = w if w > 0 else 0
        if used + cw > remaining:
            break
        chars.append(ch)
        used += cw
    return "".join(chars), used


def render_tab_bar(labels: CottList[str], active: U64, width: U16) -> StyledLine:
    spans: list[StyledSpan] = []
    remaining = width
    index = 0
    for label in labels:
        if remaining <= 0:
            break
        text, used = _fit(f" {label} ", remaining)
        style = "class:hq.tab.active" if index == active else "class:hq.tab"
        if text:
            spans.append(StyledSpan(style=style, text=text))
            remaining -= used
        index += 1
    if remaining > 0:
        spans.append(StyledSpan(style="class:hq.tab", text=" " * remaining))
    return StyledLine(spans=CottList(values=spans))
