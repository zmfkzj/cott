from typing import Final

from wcwidth import wcwidth

from cott_runtime import U16, CottList
from real.harlequin.ide_types import ContextMenu
from real.harlequin.style_types import StyledLine, StyledSpan

_MAX_ROWS: Final[int] = 10


def _columns(text: str) -> int:
    return sum(max(wcwidth(char), 0) for char in text)


def render_context_menu(menu: ContextMenu, width: U16) -> CottList[StyledLine]:
    items: list[str] = [item for item in menu.items]
    count = len(items)
    selected = menu.selected
    start = 0
    if count > _MAX_ROWS:
        start = min(max(0, selected - (_MAX_ROWS - 1)), count - _MAX_ROWS)
    lines: list[StyledLine] = []
    for index in range(start, min(count, start + _MAX_ROWS)):
        text = f" {items[index]} ".replace("\n", " ")
        text = text + " " * max(0, width - _columns(text))
        style = "class:hq.dialog class:hq.cursor" if index == selected else "class:hq.dialog"
        lines.append(StyledLine(spans=CottList(values=[StyledSpan(style=style, text=text)])))
    return CottList(values=lines)
