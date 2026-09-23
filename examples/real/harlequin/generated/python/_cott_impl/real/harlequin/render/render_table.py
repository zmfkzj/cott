from real.harlequin.core_types import Cell, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, QueryResult


def _format_cell(cell: Cell) -> str:
    if isinstance(cell, Cell_Null):
        return "NULL"
    if isinstance(cell, Cell_Integer):
        return str(cell.value)
    if isinstance(cell, Cell_Real):
        return str(cell.value)
    if isinstance(cell, Cell_Text):
        return cell.value
    return bytes(cell.value).hex()


def render_table(result: QueryResult) -> str:
    lines: list[str] = []
    if len(result.columns) > 0:
        lines.append(" | ".join(column for column in result.columns))
    for row in result.rows:
        lines.append(" | ".join(_format_cell(cell) for cell in row.values))
    return "\n".join(lines)
