from typing import Final

from cott_runtime import U64, CottList
from real.harlequin.ide_types import InputModal
from real.harlequin.style_types import StyledLine, StyledSpan

_MAX_COMPLETIONS: Final[int] = 8


def _line(style: str, text: str) -> StyledLine:
    return StyledLine(spans=CottList(values=[StyledSpan(style=style, text=text)]))


def render_input_modal(modal: InputModal, width: U64) -> CottList[StyledLine]:
    lines: list[StyledLine] = [_line("class:hq.dialog.title", modal.title)]
    spans: list[StyledSpan] = []
    value = modal.value
    if value == "":
        spans.append(StyledSpan(style="class:hq.cursor", text=" "))
        if modal.placeholder != "":
            spans.append(StyledSpan(style="class:hq.muted", text=modal.placeholder))
    else:
        cursor = min(modal.cursor, len(value))
        if cursor > 0:
            spans.append(StyledSpan(style="", text=value[:cursor]))
        caret = value[cursor] if cursor < len(value) else " "
        spans.append(StyledSpan(style="class:hq.cursor", text=caret))
        if cursor + 1 < len(value):
            spans.append(StyledSpan(style="", text=value[cursor + 1 :]))
    lines.append(StyledLine(spans=CottList(values=spans)))
    if modal.message != "":
        lines.append(_line("class:hq.error", modal.message))
    count = 0
    for completion in modal.completions:
        if count >= _MAX_COMPLETIONS:
            break
        lines.append(_line("class:hq.muted", completion[:width]))
        count += 1
    return CottList(values=lines)
