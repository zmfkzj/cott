import datetime
import decimal
from typing import Any, cast

import pyarrow
from cott_runtime import CottList, U64
from wcwidth import wcswidth

from real.harlequin.results import format_number_text, is_id_column
from real.harlequin.results_types import GridFrame, NumberFormat, ResultsGrid
from real.harlequin.style_types import StyledLine, StyledSpan


def _width(text: str) -> int:
    size = wcswidth(text)
    return len(text) if size < 0 else size


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
        digits = str(value)
        return digits if id_column else format_number_text(digits, number_format)
    if isinstance(value, float):
        return format_number_text(format(value, "g"), number_format)
    if isinstance(value, decimal.Decimal):
        return format_number_text(format(value, "f"), number_format)
    if isinstance(value, (datetime.datetime, datetime.time)):
        text = value.isoformat(timespec="milliseconds")
        return text[:-6] + "Z" if text.endswith("+00:00") else text
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return str(value)
    if isinstance(value, str):
        return _first_line(value)
    if isinstance(value, bytes):
        shown = repr(value[:32])
        return f"{shown} (+{len(value) - 32} bytes)" if len(value) > 32 else shown
    return _first_line(str(value))


def _pad(text: str, content: int, align: str) -> str:
    size = _width(text)
    if size > content:
        text = _cut(text, content - 1) + "…"
        size = _width(text)
    gap = content - size
    if align == "right":
        body = " " * gap + text
    elif align == "center":
        body = " " * (gap // 2) + text + " " * (gap - gap // 2)
    else:
        body = text + " " * gap
    return " " + body + " "


def _cut_line(spans: list[StyledSpan], width: int) -> StyledLine:
    visible: list[StyledSpan] = []
    remaining = width
    for span in spans:
        if remaining <= 0:
            break
        size = _width(span.text)
        if size <= remaining:
            visible.append(span)
            remaining -= size
        else:
            text = _cut(span.text, remaining)
            if text:
                visible.append(StyledSpan(style=span.style, text=text))
            break
    return StyledLine(spans=CottList(values=visible))


def _table_rows(table: Any, start: int, count: int) -> list[dict[str, object]]:
    raw = cast(object, table.slice(start, count).to_pylist())
    if not isinstance(raw, list):
        raise TypeError("Arrow table returned non-list rows")
    for row in cast(list[object], raw):
        if not isinstance(row, dict):
            raise TypeError("Arrow table returned a non-record row")
    return cast(list[dict[str, object]], raw)


def render_grid(grid: ResultsGrid, width: U64, height: U64, focused: bool, number_format: NumberFormat) -> GridFrame:
    result = grid.result
    columns = result.columns
    row_count = result.row_count
    first_row = grid.first_row
    first_column = grid.first_column
    lines: list[StyledLine] = []
    if not columns:
        if width > 0 and height > 0:
            lines.append(_cut_line([StyledSpan(style="class:hq.muted", text="Query returned no columns")], width))
        return GridFrame(lines=CottList(values=lines), first_row=first_row, first_column=first_column)

    if result.data.tag != "harlequin.arrow_table":
        raise TypeError("expected a harlequin.arrow_table holding a pyarrow.Table")
    raw_table = result.data.unwrap()
    if not isinstance(raw_table, pyarrow.Table):
        raise TypeError("expected a harlequin.arrow_table holding a pyarrow.Table")
    table: Any = raw_table
    ids = [is_id_column(column.name) for column in columns]
    headers = [
        _first_line(column.name) + (" " + _first_line(column.type_label) if column.type_label else "")
        for column in columns
    ]
    cap = max(20, width // 2 - 2)
    sample_count = min(1000, row_count)
    samples = _table_rows(table, 0, sample_count) if sample_count else []
    widths: list[int] = []
    for index, header in enumerate(headers):
        widest = _width(header)
        for row in samples:
            widest = max(widest, _width(_cell_text(row.get(columns[index].name), ids[index], number_format)))
        widths.append(max(1, min(widest, cap)))

    gutter_content = max(1, len(str(row_count)))
    gutter_total = gutter_content + 2
    cursor_row = grid.cursor.row
    cursor_column = min(grid.cursor.column, len(columns) - 1)
    data_rows = max(0, height - 1)
    if data_rows:
        if cursor_row < first_row:
            first_row = cursor_row
        elif cursor_row >= first_row + data_rows:
            first_row = cursor_row - data_rows + 1
    if cursor_column < first_column:
        first_column = cursor_column
    cursor_end = gutter_total + sum(widths[index] + 2 for index in range(first_column, cursor_column + 1))
    while first_column < cursor_column and cursor_end > width:
        cursor_end -= widths[first_column] + 2
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
    rows = _table_rows(table, first_row, count) if count else []
    top = min(grid.anchor.row, grid.cursor.row)
    bottom = max(grid.anchor.row, grid.cursor.row)
    left = min(grid.anchor.column, grid.cursor.column)
    right = max(grid.anchor.column, grid.cursor.column)
    multi = top != bottom or left != right
    for offset, row in enumerate(rows):
        row_number = first_row + offset
        label = str(row_number + 1)
        spans = [StyledSpan(style="class:hq.rownumber", text=" " + " " * (gutter_content - len(label)) + label + " ")]
        for index in drawn:
            value = row.get(columns[index].name)
            text = _cell_text(value, ids[index], number_format)
            style = "class:hq.cell"
            if value is None:
                style += " class:hq.cell.null"
                align = "center"
            else:
                if isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool):
                    style += " class:hq.cell.number"
                align = "right" if isinstance(value, (bool, int, float, decimal.Decimal, datetime.date, datetime.time, datetime.timedelta)) else "left"
            if multi and top <= row_number <= bottom and left <= index <= right:
                style += " class:hq.selection"
            if focused and row_number == cursor_row and index == cursor_column:
                style += " class:hq.cursor"
            spans.append(StyledSpan(style=style, text=_pad(text, widths[index], align)))
        lines.append(_cut_line(spans, width))
    return GridFrame(lines=CottList(values=lines), first_row=first_row, first_column=first_column)
