from cott_runtime import U64, CottList

from real.harlequin.ide_types import TextModal
from real.harlequin.style_types import StyledLine, StyledSpan


def _line(style: str, text: str) -> StyledLine:
    return StyledLine(spans=CottList(values=[StyledSpan(style=style, text=text)]))


def _wrap(text: str, width: int) -> list[str]:
    out: list[str] = []
    for part in text.replace("\r", "").split("\n"):
        if width <= 0 or part == "":
            out.append("")
            continue
        start = 0
        while start < len(part):
            out.append(part[start : start + width])
            start += width
    return out


def render_text_modal(modal: TextModal, width: U64, height: U64) -> CottList[StyledLine]:
    rows = int(height)
    if rows <= 0:
        return CottList(values=[])
    w = int(width)
    top: list[StyledLine] = [_line("class:hq.dialog.title", modal.title.replace("\n", " ")[:w])]
    if rows == 1:
        return CottList(values=top)
    if modal.header != "":
        for piece in _wrap(modal.header, w):
            top.append(_line("class:hq.dialog", piece))
    top = top[: rows - 1]
    body_rows = rows - 1 - len(top)
    source = list(modal.lines)
    start = int(modal.scroll)
    body: list[StyledLine] = [
        _line("class:hq.text", text.replace("\n", " ")[:w]) for text in source[start : start + body_rows]
    ]
    footer = _line("class:hq.muted", modal.footer.replace("\n", " ")[:w])
    return CottList(values=top + body + [footer])
