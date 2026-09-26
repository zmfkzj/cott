from cott_runtime import U16, CottList

from real.harlequin.keymap_types import FooterHint
from real.harlequin.style_types import StyledLine, StyledSpan


def render_footer(hints: CottList[FooterHint], width: U16) -> StyledLine:
    pieces: list[tuple[str, str]] = []
    for hint in hints:
        pieces.append(("class:hq.footer.key", f" {hint.key}"))
        pieces.append(("class:hq.footer.description", f" {hint.description} "))
    spans: list[StyledSpan] = []
    used = 0
    for style, text in pieces:
        remaining = width - used
        if remaining <= 0:
            break
        cut = text[:remaining]
        if cut:
            spans.append(StyledSpan(style=style, text=cut))
            used += len(cut)
    if used < width:
        spans.append(StyledSpan(style="class:hq.footer", text=" " * (width - used)))
    return StyledLine(spans=CottList(values=spans))
