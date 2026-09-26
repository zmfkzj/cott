import textwrap

from cott_runtime import U64, CottList
from real.harlequin.ide_types import ConfirmModal
from real.harlequin.style_types import StyledLine, StyledSpan


def _wrap_prompt(prompt: str, width: int) -> list[str]:
    wrap_width = max(1, width)
    lines: list[str] = []
    for paragraph in prompt.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=wrap_width)
        if wrapped:
            lines.extend(wrapped)
        else:
            lines.append("")
    return lines


def render_confirm(modal: ConfirmModal, width: U64) -> CottList[StyledLine]:
    result: list[StyledLine] = []
    for text in _wrap_prompt(modal.prompt, width):
        result.append(StyledLine(spans=CottList(values=[StyledSpan(style="class:hq.dialog", text=text)])))
    result.append(StyledLine(spans=CottList(values=[])))
    no_style = "class:hq.button" if modal.yes_selected else "class:hq.button.focused"
    yes_style = "class:hq.button.focused" if modal.yes_selected else "class:hq.button"
    result.append(
        StyledLine(
            spans=CottList(
                values=[
                    StyledSpan(style=no_style, text="[ No ]"),
                    StyledSpan(style="", text="  "),
                    StyledSpan(style=yes_style, text="[ Yes ]"),
                ]
            )
        )
    )
    return CottList(values=result)
