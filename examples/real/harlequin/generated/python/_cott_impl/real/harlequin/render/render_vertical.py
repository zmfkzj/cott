from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Real, Cell_Text, QueryResult


def _cell_text(cell: Cell) -> str:
    if isinstance(cell, Cell_Integer) or isinstance(cell, Cell_Real):
        return str(cell.value)
    if isinstance(cell, Cell_Text):
        return cell.value
    if isinstance(cell, Cell_Blob):
        return bytes(cell.value).hex()
    return "NULL"


def render_vertical(result: QueryResult) -> str:
    lines: list[str] = []
    columns = list(result.columns)
    for index, row in enumerate(result.rows, start=1):
        lines.append(f"Row {index}")
        for column, cell in zip(columns, row.values):
            lines.append(f"{column}: {_cell_text(cell)}")
    return "\n".join(lines)
