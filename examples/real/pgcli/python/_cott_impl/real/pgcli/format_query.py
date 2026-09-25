import html
import json
from typing import Final

from cott_runtime import U16, U64, CottList
from real.pgcli import render_query
from real.pgcli_types import FormatRequest, FormattedQuery, RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv

_U16_MAX: Final[int] = 65535
_LATEX_SPECIAL: Final[str] = "&%$#_{}"


def _clip(value: str, limit: int) -> str:
    if limit <= 0 or len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _delimited_field(value: str, delimiter: str) -> str:
    if delimiter in value or '"' in value or "\r" in value or "\n" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


def _delimited(columns: list[str], rows: list[list[str]], delimiter: str) -> str:
    records = [columns, *rows]
    return "\n".join(delimiter.join(_delimited_field(field, delimiter) for field in record) for record in records)


def _record(columns: list[str], row: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, cell in zip(columns, row):
        result[name] = cell
    return result


def _latex_cell(value: str) -> str:
    parts: list[str] = []
    for character in value:
        if character == "\\":
            parts.append("\\textbackslash{}")
        elif character in _LATEX_SPECIAL:
            parts.append("\\" + character)
        else:
            parts.append(character)
    return "".join(parts)


def _markdown_line(cells: list[str]) -> str:
    return "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"


def _measure(text: str) -> int:
    return min(max((len(line) for line in text.split("\n")), default=0), _U16_MAX)


def _render(columns: list[str], rows: list[list[str]], terminal_width: U16, layout: RenderLayout) -> RenderedQuery:
    return render_query(RenderRequest(columns=CottList(values=columns), rows=CottList(values=[CottList(values=row) for row in rows]), terminal_width=terminal_width, layout=layout))


def format_query(request: FormatRequest) -> FormattedQuery:
    limit = int(request.max_column_width)
    columns = [column for column in request.query.columns]
    column_count = len(columns)
    total_rows = 0
    kept_rows: list[list[str]] = []
    for row in request.query.rows:
        total_rows += 1
        if len(kept_rows) >= request.max_rows:
            continue
        cells = [cell for cell in row][:column_count]
        cells.extend([""] * (column_count - len(cells)))
        kept_rows.append([_clip(cell, limit) for cell in cells])
    truncated_rows: U64 = total_rows - len(kept_rows)

    table_format: TableFormat = request.format
    if isinstance(table_format, TableFormat_Aligned):
        rendered = _render(columns, kept_rows, request.terminal_width, RenderLayout_Horizontal())
        if rendered.width > request.terminal_width:
            rendered = _render(columns, kept_rows, request.terminal_width, RenderLayout_Vertical())
        return FormattedQuery(rendered=rendered, truncated_rows=truncated_rows)

    if isinstance(table_format, TableFormat_Csv):
        text = _delimited(columns, kept_rows, ",")
    elif isinstance(table_format, TableFormat_Tsv):
        text = _delimited(columns, kept_rows, "\t")
    elif isinstance(table_format, TableFormat_Json):
        text = json.dumps([_record(columns, row) for row in kept_rows], ensure_ascii=False, indent=2)
    elif isinstance(table_format, TableFormat_JsonLines):
        text = "\n".join(json.dumps(_record(columns, row), ensure_ascii=False) for row in kept_rows)
    elif isinstance(table_format, TableFormat_Html):
        lines = ["<table>", "<thead><tr>" + "".join(f"<th>{html.escape(column)}</th>" for column in columns) + "</tr></thead>", "<tbody>"]
        lines.extend("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>" for row in kept_rows)
        lines.extend(["</tbody>", "</table>"])
        text = "\n".join(lines)
    elif isinstance(table_format, TableFormat_Latex):
        lines = ["\\begin{tabular}{" + "l" * column_count + "}", " & ".join(_latex_cell(column) for column in columns) + " \\\\", "\\hline"]
        lines.extend(" & ".join(_latex_cell(cell) for cell in row) + " \\\\" for row in kept_rows)
        lines.append("\\end{tabular}")
        text = "\n".join(lines)
    elif isinstance(table_format, TableFormat_Markdown):
        lines = [_markdown_line(columns), "|" + "---|" * column_count]
        lines.extend(_markdown_line(row) for row in kept_rows)
        text = "\n".join(lines)
    else:
        rendered = _render(columns, kept_rows, request.terminal_width, RenderLayout_Vertical())
        return FormattedQuery(rendered=rendered, truncated_rows=truncated_rows)

    width: U16 = _measure(text)
    return FormattedQuery(rendered=RenderedQuery(text=text, layout=RenderLayout_Horizontal(), width=width), truncated_rows=truncated_rows)
