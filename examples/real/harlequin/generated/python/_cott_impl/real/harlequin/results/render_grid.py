import datetime
import decimal
from typing import Any, cast

from cott_runtime import CottList, U64
from wcwidth import wcswidth

from real.harlequin.results import format_number_text, is_id_column
from real.harlequin.results_types import GridFrame, NumberFormat, ResultsGrid
from real.harlequin.style_types import StyledLine, StyledSpan


def _width(text: str) -> int:
    measured = wcswidth(text)
    return len(text) if measured < 0 else measured


def _cut(text: str, limit: int) -> str:
    out: list[str] = []
    used = 0
    for char in text:
        size = _width(char)
        if used + size > limit:
            break
        out.append(char)
        used += size
    return "".join(out)


def _first_line(text: str) -> str:
    for index, char in enumerate(text):
        if char == "\r" or char == "\n":
            return text[:index] + "…⏎"
    return text


def _cell_text(value: object, id_column: bool, number_format: NumberFormat) -> str:
    if value is None:
        return "∅ null"
    if isinstance(value, bool):
        return "✓ True" if value else "X False"
    if isinstance(value, int):
        return str(value) if id_column else format_number_text(str(value), number_format)
    if isinstance(value, float):
        return format_number_text(format(value, "g"), number_format)
    if isinstance(value, decimal.Decimal):
        return format_number_text(format(value, "f"), number_format)
    if isinstance(value, (datetime.datetime, datetime.time)):
        text = value.isoformat(timespec="milliseconds")
        if text.endswith("+00:00"):
            text = text[: -len("+00:00")] + "Z"
        return text
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return str(value)
    if isinstance(value, str):
        return _first_line(value)
    if isinstance(value, bytes):
        shown = repr(value[:32])
        if len(value) > 32:
            return f"{shown} (+{len(value) - 32} bytes)"
        return shown
    return _first_line(str(value))


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool)


def _is_right(value: object) -> bool:
    return isinstance(value, (bool, int, float, decimal.Decimal, datetime.date, datetime.time, datetime.timedelta))


def _pad(text: str, content: int, align: str) -> str:
    size = _width(text)
    if size > content:
        text = _cut(text, content - 1) + "…"
        size = _width(text)
    gap = max(0, content - size)
    if align == "right":
        body = " " * gap + text
    elif align == "center":
        body = " " * (gap // 2) + text + " " * (gap - gap // 2)
    else:
        body = text + " " * gap
    return " " + body + " "


def _column_values(table: Any, start: int, count: int, column: int) -> list[object]:
    raw = cast(object, table.slice(start, count).column(column).to_pylist())
    if not isinstance(raw, list):
        return []
    return cast(list[object], raw)


def _cut_line(spans: list[StyledSpan], width: int) -> StyledLine:
    out: list[StyledSpan] = []
    remaining = width
    for span in spans:
        if remaining <= 0:
            break
        size = _width(span.text)
        if size <= remaining:
            out.append(span)
            remaining -= size
        else:
            text = _cut(span.text, remaining)
            if text:
                out.append(StyledSpan(style=span.style, text=text))
            remaining = 0
    return StyledLine(spans=CottList(values=out))


def render_grid(grid: ResultsGrid, width: U64, height: U64, focused: bool, number_format: NumberFormat) -> GridFrame:
    result = grid.result
    columns = list(result.columns)
    row_count = int(result.row_count)
    first_row = int(grid.first_row)
    first_column = int(grid.first_column)
    lines: list[StyledLine] = []
    if len(columns) == 0:
        if width > 0 and height > 0:
            lines.append(_cut_line([StyledSpan(style="class:hq.muted", text="Query returned no columns")], width))
        return GridFrame(lines=CottList(values=lines), first_row=first_row, first_column=first_column)
    handle = result.data
    table: Any = handle.unwrap() if handle.tag == "harlequin.arrow_table" else None
    ids = [is_id_column(column.name) for column in columns]
    headers = [column.name + " " + column.type_label if column.type_label else column.name for column in columns]
    cap = max(20, width // 2 - 2)
    sample_count = min(1000, row_count)
    widths: list[int] = []
    for index, header in enumerate(headers):
        widest = _width(header)
        if table is not None and sample_count > 0:
            for value in _column_values(table, 0, sample_count, index):
                widest = max(widest, _width(_cell_text(value, ids[index], number_format)))
        widths.append(max(1, min(widest, cap)))
    gutter_content = max(1, len(str(row_count)))
    gutter_total = gutter_content + 2
    cursor_row = int(grid.cursor.row)
    cursor_column = min(int(grid.cursor.column), len(columns) - 1)
    data_rows = int(height) - 1 if height > 0 else 0
    if data_rows > 0:
        if cursor_row < first_row:
            first_row = cursor_row
        elif cursor_row >= first_row + data_rows:
            first_row = cursor_row - data_rows + 1
    if cursor_column < first_column:
        first_column = cursor_column
    while first_column < cursor_column and gutter_total + sum(w + 2 for w in widths[first_column:cursor_column + 1]) > width:
        first_column += 1
    if width == 0 or height == 0:
        return GridFrame(lines=CottList(values=lines), first_row=first_row, first_column=first_column)
    drawn: list[int] = []
    start = gutter_total
    for index in range(first_column, len(columns)):
        if start >= width:
            break
        drawn.append(index)
        start += widths[index] + 2
    header_spans = [StyledSpan(style="class:hq.header", text=" " * gutter_total)]
    for index in drawn:
        header_spans.append(StyledSpan(style="class:hq.header", text=_pad(headers[index], widths[index], "left")))
    lines.append(_cut_line(header_spans, width))
    count = max(0, min(data_rows, row_count - first_row))
    top = min(grid.anchor.row, grid.cursor.row)
    bottom = max(grid.anchor.row, grid.cursor.row)
    left = min(grid.anchor.column, grid.cursor.column)
    right = max(grid.anchor.column, grid.cursor.column)
    multi = top != bottom or left != right
    values: dict[int, list[object]] = {}
    for index in drawn:
        values[index] = _column_values(table, first_row, count, index) if table is not None and count > 0 else []
    for offset in range(count):
        row = first_row + offset
        label = str(row + 1)
        spans = [StyledSpan(style="class:hq.rownumber", text=" " + " " * (gutter_content - len(label)) + label + " ")]
        for index in drawn:
            column_values = values[index]
            value = column_values[offset] if offset < len(column_values) else None
            text = _cell_text(value, ids[index], number_format)
            style = "class:hq.cell"
            if value is None:
                style += " class:hq.cell.null"
                align = "center"
            else:
                if _is_number(value):
                    style += " class:hq.cell.number"
                align = "right" if _is_right(value) else "left"
            if multi and top <= row <= bottom and left <= index <= right:
                style += " class:hq.selection"
            if focused and row == cursor_row and index == cursor_column:
                style += " class:hq.cursor"
            spans.append(StyledSpan(style=style, text=_pad(text, widths[index], align)))
        lines.append(_cut_line(spans, width))
    return GridFrame(lines=CottList(values=lines), first_row=first_row, first_column=first_column)
