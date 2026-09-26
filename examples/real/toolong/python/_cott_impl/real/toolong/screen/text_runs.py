from typing import Final

from rich.cells import get_character_cell_size

from cott_runtime import CottList, U16, U64
from real.toolong.model_types import StyledRun, StyledText

_ATTRS: Final[str] = "bold dim italic underline reverse"


def _parse(code: str) -> tuple[str, str, dict[str, bool]]:
    fg = ""
    bg = ""
    flags: dict[str, bool] = {}
    for token in code.split():
        if token.startswith("fg:"):
            fg = token[3:]
        elif token.startswith("bg:"):
            bg = token[3:]
        elif token.startswith("no"):
            flags[token[2:]] = False
        else:
            flags[token] = True
    return fg, bg, flags


def _resolve(base: str, layers: list[str]) -> str:
    base_fg, base_bg, base_flags = _parse(base)
    fg = base_fg
    bg = base_bg
    flags = dict(base_flags)
    for layer in layers:
        layer_fg, layer_bg, layer_flags = _parse(layer)
        if layer_fg:
            fg = base_fg if layer_fg == "default" else layer_fg
        if layer_bg:
            bg = base_bg if layer_bg == "default" else layer_bg
        flags.update(layer_flags)
    parts = ["fg:" + fg, "bg:" + bg]
    for name in _ATTRS.split():
        if flags.get(name, False):
            parts.append(name)
    return " ".join(parts)


def text_runs(text: StyledText, base: str, offset: U64, width: U16, fill: str) -> CottList[StyledRun]:
    if width == 0:
        return CottList(values=[])
    cache: dict[tuple[int, ...], str] = {}
    cells: list[tuple[str, str, str]] = []
    for index, ch in enumerate(text.text):
        size = get_character_cell_size(ch)
        if size <= 0:
            continue
        covering: list[int] = []
        layers: list[str] = []
        position = 0
        for span in text.spans:
            if span.start <= index < span.end:
                covering.append(position)
                layers.append(span.style)
            position += 1
        key = tuple(covering)
        if key not in cache:
            cache[key] = _resolve(base, layers)
        style = cache[key]
        if size == 1:
            cells.append((ch, style, "n"))
        else:
            cells.append((ch, style, "L"))
            cells.append(("", style, "R"))
    end = offset + width
    texts: list[str] = []
    styles: list[str] = []
    for column in range(offset, end):
        if column < len(cells):
            ch, style, kind = cells[column]
            if kind == "L" and column + 1 >= end:
                ch = " "
            elif kind == "R":
                if column == offset:
                    ch = " "
                else:
                    continue
        else:
            ch = " "
            style = fill
        if styles and styles[-1] == style:
            texts[-1] += ch
        else:
            texts.append(ch)
            styles.append(style)
    runs = [StyledRun(text=t, style=s) for t, s in zip(texts, styles) if t]
    return CottList(values=runs)
