from cott_runtime import U16
from real.pgcli_types import (
    RenderLayout,
    RenderLayout_Horizontal,
    RenderLayout_Vertical,
    RenderRequest,
    RenderedQuery,
)


def _single_line(value: str) -> str:
    return value.replace("\r\n", "↵").replace("\r", "↵").replace("\n", "↵")


def _prepare_data(request: RenderRequest) -> tuple[list[str], list[list[str]]]:
    columns: list[str] = []
    for column in request.columns:
        columns.append(column)

    rows: list[list[str]] = []
    for source_row in request.rows:
        row: list[str] = []
        column_index = 0
        for value in source_row:
            if column_index >= len(columns):
                break
            row.append(value)
            column_index += 1
        while len(row) < len(columns):
            row.append("")
        rows.append(row)
    return (columns, rows)


def _text_width(text: str) -> U16:
    widest = 0
    for line in text.split("\n"):
        if len(line) > widest:
            widest = len(line)
    if widest > 65535:
        return 65535
    return widest


def _horizontal_text(columns: list[str], rows: list[list[str]]) -> str:
    if len(columns) == 0:
        return ""

    widths: list[int] = []
    for column in columns:
        widths.append(len(_single_line(column)))
    for row in rows:
        column_index = 0
        while column_index < len(columns):
            cell_width = len(_single_line(row[column_index]))
            if cell_width > widths[column_index]:
                widths[column_index] = cell_width
            column_index += 1

    lines: list[str] = []
    header: list[str] = []
    column_index = 0
    while column_index < len(columns):
        header.append(_single_line(columns[column_index]).ljust(widths[column_index]))
        column_index += 1
    lines.append(" | ".join(header))

    separators: list[str] = []
    for width in widths:
        separators.append("-" * width)
    lines.append("-+-".join(separators))

    for row in rows:
        cells: list[str] = []
        column_index = 0
        while column_index < len(columns):
            cells.append(_single_line(row[column_index]).ljust(widths[column_index]))
            column_index += 1
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def _vertical_text(columns: list[str], rows: list[list[str]]) -> str:
    if len(columns) == 0 or len(rows) == 0:
        return ""

    name_width = 0
    for column in columns:
        column_width = len(_single_line(column))
        if column_width > name_width:
            name_width = column_width

    lines: list[str] = []
    row_index = 0
    while row_index < len(rows):
        if row_index > 0:
            lines.append("")
        lines.append("-[ RECORD " + str(row_index + 1) + " ]-")
        column_index = 0
        while column_index < len(columns):
            lines.append(
                _single_line(columns[column_index]).ljust(name_width)
                + " | "
                + _single_line(rows[row_index][column_index])
            )
            column_index += 1
        row_index += 1
    return "\n".join(lines)


def render_query(request: RenderRequest) -> RenderedQuery:
    columns, rows = _prepare_data(request)
    layout: RenderLayout = RenderLayout_Horizontal()
    text = _horizontal_text(columns, rows)
    width = _text_width(text)
    if request.vertical or width > request.terminal_width:
        text = _vertical_text(columns, rows)
        layout = RenderLayout_Vertical()
        width = _text_width(text)
    return RenderedQuery(text=text, layout=layout, width=width)
