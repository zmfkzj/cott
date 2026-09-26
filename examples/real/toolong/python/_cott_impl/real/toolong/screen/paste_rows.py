from rich.cells import get_character_cell_size

from cott_runtime import CottList, U16
from real.toolong.model_types import ScreenRow, StyledRun


def _cells(row: ScreenRow) -> list[tuple[str, str, str]]:
    cells: list[tuple[str, str, str]] = []
    for run in row.runs:
        for ch in run.text:
            size = get_character_cell_size(ch)
            if size <= 0:
                if cells:
                    prev = cells[-1]
                    cells[-1] = (prev[0] + ch, prev[1], prev[2])
            elif size == 1:
                cells.append((ch, run.style, "n"))
            else:
                cells.append((ch, run.style, "L"))
                cells.append(("", run.style, "R"))
    return cells


def _row(cells: list[tuple[str, str, str]]) -> ScreenRow:
    count = len(cells)
    texts: list[str] = []
    styles: list[str] = []
    for index in range(count):
        text, style, kind = cells[index]
        if kind == "L" and (index + 1 >= count or cells[index + 1][2] != "R"):
            text = " "
        elif kind == "R" and (index == 0 or cells[index - 1][2] != "L"):
            text = " "
        if styles and styles[-1] == style:
            texts[-1] += text
        else:
            texts.append(text)
            styles.append(style)
    runs: list[StyledRun] = []
    for text, style in zip(texts, styles):
        if text:
            if runs and runs[-1].style == style:
                runs[-1] = StyledRun(text=runs[-1].text + text, style=style)
            else:
                runs.append(StyledRun(text=text, style=style))
    return ScreenRow(runs=CottList(values=runs))


def paste_rows(base: CottList[ScreenRow], x: U16, y: U16, rows: CottList[ScreenRow]) -> CottList[ScreenRow]:
    result: list[ScreenRow] = [row for row in base]
    index = 0
    for overlay in rows:
        target = y + index
        index += 1
        if target >= len(result):
            break
        cells = _cells(result[target])
        width = len(cells)
        pasted = _cells(overlay)
        for j in range(len(pasted)):
            column = x + j
            if column >= width:
                break
            cells[column] = pasted[j]
        result[target] = _row(cells)
    return CottList(values=result)
