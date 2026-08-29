from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, QueryResult


def _escape_text(text: str) -> str:
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _render_cell(cell: Cell) -> str:
    match cell:
        case Cell_Null():
            return "NULL"
        case Cell_Integer(value=value):
            return str(value)
        case Cell_Real(value=value):
            return repr(value)
        case Cell_Text(value=value):
            return _escape_text(value)
        case Cell_Blob(value=value):
            return "0x" + value.hex()


def _render_grid(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            if len(value) > widths[index]:
                widths[index] = len(value)

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    lines = [
        border,
        "|" + "|".join(f" {header:<{widths[index]}} " for index, header in enumerate(headers)) + "|",
        border,
    ]
    for row in rows:
        lines.append("|" + "|".join(f" {value:<{widths[index]}} " for index, value in enumerate(row)) + "|")
    lines.append(border)
    return "\n".join(lines)


def render_table(result: QueryResult) -> str:
    """Render a query result deterministically in horizontal or vertical table form."""
    headers = tuple(_escape_text(column) for column in result.columns)
    if len(headers) == 0:
        return _render_grid(("affected_rows",), [(str(result.affected_rows),)])

    rows: list[tuple[str, ...]] = []
    for row in result.rows:
        rows.append(tuple(_render_cell(cell) for cell in row.values))
    return _render_grid(headers, rows)
