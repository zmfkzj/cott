import html
import json

from cott_runtime import CottList, U16, U64
from real.pgcli_types import (
    FormatRequest,
    FormattedQuery,
    RenderLayout,
    RenderLayout_Horizontal,
    RenderLayout_Vertical,
    RenderedQuery,
    TableFormat_Aligned,
    TableFormat_Csv,
    TableFormat_Html,
    TableFormat_Json,
    TableFormat_JsonLines,
    TableFormat_Latex,
    TableFormat_Markdown,
    TableFormat_Tsv,
    TableFormat_Vertical,
)


def _truncate_cell(value: str, maximum: U16) -> str:
    if len(value) <= maximum:
        return value
    if maximum == 0:
        return ""
    if maximum == 1:
        return "…"
    return value[: maximum - 1] + "…"


def _prepare_data(columns: CottList[str], source_rows: CottList[CottList[str]], maximum_rows: U64, maximum_width: U16) -> tuple[list[str], list[list[str]], U64]:
    prepared_columns: list[str] = []
    for column in columns:
        prepared_columns.append(_truncate_cell(column, maximum_width))
    prepared_rows: list[list[str]] = []
    total_rows = 0
    for source_row in source_rows:
        if total_rows < maximum_rows:
            prepared_row: list[str] = []
            column_index = 0
            for value in source_row:
                if column_index >= len(prepared_columns):
                    break
                prepared_row.append(_truncate_cell(value, maximum_width))
                column_index += 1
            while len(prepared_row) < len(prepared_columns):
                prepared_row.append("")
            prepared_rows.append(prepared_row)
        total_rows += 1
    truncated_rows = total_rows - len(prepared_rows)
    if truncated_rows > maximum_rows:
        truncated_rows = maximum_rows
    return (prepared_columns, prepared_rows, truncated_rows)


def _single_line(value: str) -> str:
    return value.replace("\r\n", "↵").replace("\r", "↵").replace("\n", "↵")


def _text_width(text: str) -> U16:
    widest = 0
    for line in text.split("\n"):
        if len(line) > widest:
            widest = len(line)
    if widest > 65535:
        return 65535
    return widest


def _aligned_text(columns: list[str], rows: list[list[str]]) -> str:
    if len(columns) == 0:
        return ""
    widths: list[int] = []
    for column in columns:
        widths.append(len(_single_line(column)))
    for row in rows:
        index = 0
        while index < len(columns):
            cell_width = len(_single_line(row[index]))
            if cell_width > widths[index]:
                widths[index] = cell_width
            index += 1
    lines: list[str] = []
    header: list[str] = []
    index = 0
    while index < len(columns):
        header.append(_single_line(columns[index]).ljust(widths[index]))
        index += 1
    lines.append(" | ".join(header))
    separators: list[str] = []
    for width in widths:
        separators.append("-" * width)
    lines.append("-+-".join(separators))
    for row in rows:
        cells: list[str] = []
        index = 0
        while index < len(columns):
            cells.append(_single_line(row[index]).ljust(widths[index]))
            index += 1
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
            lines.append(_single_line(columns[column_index]).ljust(name_width) + " | " + _single_line(rows[row_index][column_index]))
            column_index += 1
        row_index += 1
    return "\n".join(lines)


def _delimited_cell(value: str, delimiter: str) -> str:
    if delimiter in value or '"' in value or "\n" in value or "\r" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


def _delimited_text(columns: list[str], rows: list[list[str]], delimiter: str) -> str:
    lines: list[str] = []
    header: list[str] = []
    for column in columns:
        header.append(_delimited_cell(column, delimiter))
    if len(header) > 0:
        lines.append(delimiter.join(header))
    for row in rows:
        cells: list[str] = []
        for value in row:
            cells.append(_delimited_cell(value, delimiter))
        lines.append(delimiter.join(cells))
    return "\n".join(lines)


def _json_object(columns: list[str], row: list[str]) -> str:
    fields: list[str] = []
    index = 0
    while index < len(columns):
        fields.append(json.dumps(columns[index], ensure_ascii=False) + ":" + json.dumps(row[index], ensure_ascii=False))
        index += 1
    return "{" + ",".join(fields) + "}"


def _json_text(columns: list[str], rows: list[list[str]], lines: bool) -> str:
    objects: list[str] = []
    for row in rows:
        objects.append(_json_object(columns, row))
    if lines:
        return "\n".join(objects)
    if len(objects) == 0:
        return "[]"
    indented: list[str] = []
    for value in objects:
        indented.append("  " + value)
    return "[\n" + ",\n".join(indented) + "\n]"


def _html_text(columns: list[str], rows: list[list[str]]) -> str:
    lines: list[str] = ["<table>"]
    if len(columns) > 0:
        headers: list[str] = []
        for column in columns:
            headers.append("<th>" + html.escape(column, quote=True) + "</th>")
        lines.append("  <thead><tr>" + "".join(headers) + "</tr></thead>")
    lines.append("  <tbody>")
    for row in rows:
        cells: list[str] = []
        for value in row:
            cells.append("<td>" + html.escape(value, quote=True) + "</td>")
        lines.append("    <tr>" + "".join(cells) + "</tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)


def _latex_cell(value: str) -> str:
    pieces: list[str] = []
    for character in value.replace("\r\n", "\n").replace("\r", "\n"):
        if character == "\\":
            pieces.append("\\textbackslash{}")
        elif character == "&":
            pieces.append("\\&")
        elif character == "%":
            pieces.append("\\%")
        elif character == "$":
            pieces.append("\\$")
        elif character == "#":
            pieces.append("\\#")
        elif character == "_":
            pieces.append("\\_")
        elif character == "{":
            pieces.append("\\{")
        elif character == "}":
            pieces.append("\\}")
        elif character == "~":
            pieces.append("\\textasciitilde{}")
        elif character == "^":
            pieces.append("\\textasciicircum{}")
        elif character == "\r" or character == "\n":
            pieces.append(" ")
        else:
            pieces.append(character)
    return "".join(pieces)


def _latex_text(columns: list[str], rows: list[list[str]]) -> str:
    alignment = "l" * len(columns)
    lines: list[str] = ["\\begin{tabular}{" + alignment + "}", "\\hline"]
    header: list[str] = []
    for column in columns:
        header.append(_latex_cell(column))
    if len(header) > 0:
        lines.append(" & ".join(header) + " \\\\")
        lines.append("\\hline")
    for row in rows:
        cells: list[str] = []
        for value in row:
            cells.append(_latex_cell(value))
        lines.append(" & ".join(cells) + " \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    return "\n".join(lines)


def _markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\r", "<br>").replace("\n", "<br>")


def _markdown_text(columns: list[str], rows: list[list[str]]) -> str:
    if len(columns) == 0:
        return ""
    header: list[str] = []
    separators: list[str] = []
    for column in columns:
        header.append(_markdown_cell(column))
        separators.append("---")
    lines: list[str] = ["| " + " | ".join(header) + " |", "| " + " | ".join(separators) + " |"]
    for row in rows:
        cells: list[str] = []
        for value in row:
            cells.append(_markdown_cell(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def format_query(request: FormatRequest) -> FormattedQuery:
    columns, rows, truncated_rows = _prepare_data(request.query.columns, request.query.rows, request.max_rows, request.max_column_width)
    layout: RenderLayout = RenderLayout_Horizontal()
    match request.format:
        case TableFormat_Aligned():
            text = _aligned_text(columns, rows)
            if _text_width(text) > request.terminal_width:
                text = _vertical_text(columns, rows)
                layout = RenderLayout_Vertical()
        case TableFormat_Csv():
            text = _delimited_text(columns, rows, ",")
        case TableFormat_Tsv():
            text = _delimited_text(columns, rows, "\t")
        case TableFormat_Json():
            text = _json_text(columns, rows, False)
        case TableFormat_JsonLines():
            text = _json_text(columns, rows, True)
        case TableFormat_Html():
            text = _html_text(columns, rows)
        case TableFormat_Latex():
            text = _latex_text(columns, rows)
        case TableFormat_Markdown():
            text = _markdown_text(columns, rows)
        case TableFormat_Vertical():
            text = _vertical_text(columns, rows)
            layout = RenderLayout_Vertical()
    rendered = RenderedQuery(text=text, layout=layout, width=_text_width(text))
    return FormattedQuery(rendered=rendered, truncated_rows=truncated_rows)
