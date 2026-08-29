from real.pgcli_types import RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery


def _column_widths(columns: list[str], rows: list[list[str]]) -> list[int]:
    widths = [len(column) for column in columns]
    for row in rows:
        limit = min(len(widths), len(row))
        for index in range(limit):
            value_width = len(row[index])
            if value_width > widths[index]:
                widths[index] = value_width
    return widths


def _horizontal_text(columns: list[str], rows: list[list[str]], widths: list[int]) -> str:
    if not columns:
        return ""
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    header = "| " + " | ".join(columns[index].ljust(widths[index]) for index in range(len(columns))) + " |"
    lines: list[str] = [border, header, border]
    for row in rows:
        cells: list[str] = []
        for index in range(len(columns)):
            value = row[index] if index < len(row) else ""
            cells.append(value.ljust(widths[index]))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append(border)
    return "\n".join(lines)


def _vertical_text(columns: list[str], rows: list[list[str]]) -> tuple[str, int]:
    if not columns or not rows:
        return "", 0
    label_width = max(len(column) for column in columns)
    rendered_width = 0
    for row_number, row in enumerate(rows, start=1):
        header_width = len("-[ RECORD " + str(row_number) + " ]")
        if header_width > rendered_width:
            rendered_width = header_width
        for index, column in enumerate(columns):
            value = row[index] if index < len(row) else ""
            line_width = label_width + 3 + len(value)
            if line_width > rendered_width:
                rendered_width = line_width

    lines: list[str] = []
    for row_number, row in enumerate(rows, start=1):
        record_header = "-[ RECORD " + str(row_number) + " ]"
        lines.append(record_header + "-" * (rendered_width - len(record_header)))
        for index, column in enumerate(columns):
            value = row[index] if index < len(row) else ""
            lines.append(column.ljust(label_width) + " | " + value)
    return "\n".join(lines), rendered_width


def render_query(request: RenderRequest) -> RenderedQuery:
    columns: list[str] = list(request.columns)
    rows: list[list[str]] = []
    for source_row in request.rows:
        row: list[str] = list(source_row)
        rows.append(row)

    widths = _column_widths(columns, rows)
    horizontal_width = sum(widths) + 3 * len(widths) + 1 if widths else 0
    if request.vertical or horizontal_width > request.terminal_width:
        text, width = _vertical_text(columns, rows)
        return RenderedQuery(text=text, layout=RenderLayout_Vertical(), width=width)

    text = _horizontal_text(columns, rows, widths)
    return RenderedQuery(text=text, layout=RenderLayout_Horizontal(), width=horizontal_width)
