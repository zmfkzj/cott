from cott_runtime import Err, Ok, Result
from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Real, Cell_Text, QueryResult
from real.harlequin.render_types import RenderError, RenderError_InvalidWidth, RenderError_UnsupportedCell, RenderLayout_Vertical, RenderOptions


def _format_cell(cell: Cell) -> str:
    if isinstance(cell, Cell_Integer):
        return str(cell.value)
    if isinstance(cell, Cell_Real):
        return str(cell.value)
    if isinstance(cell, Cell_Text):
        return cell.value
    if isinstance(cell, Cell_Blob):
        return bytes(cell.value).hex()
    return "NULL"


def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]:
    terminal_width = options.terminal_width
    cell_width = options.maximum_cell_width
    if terminal_width == 0:
        return Err(error=RenderError_InvalidWidth(width=terminal_width))
    if cell_width == 0:
        return Err(error=RenderError_InvalidWidth(width=cell_width))
    columns: list[str] = []
    for column in result.columns:
        if "\x00" in column:
            return Err(error=RenderError_UnsupportedCell(message="column name contains NUL"))
        columns.append(column[:cell_width])
    rows: list[list[str]] = []
    for index, row in enumerate(result.rows):
        if index >= options.maximum_rows:
            break
        cells: list[str] = []
        for cell in row.values:
            if isinstance(cell, Cell_Text) and "\x00" in cell.value:
                return Err(error=RenderError_UnsupportedCell(message="text cell contains NUL"))
            cells.append(_format_cell(cell)[:cell_width])
        rows.append(cells)
    lines: list[str] = []
    if isinstance(options.layout, RenderLayout_Vertical):
        for number, cells in enumerate(rows, start=1):
            lines.append(f"Row {number}")
            for name, value in zip(columns, cells):
                lines.append(f"{name}: {value}")
    else:
        if columns:
            lines.append(" | ".join(columns))
        for cells in rows:
            lines.append(" | ".join(cells))
    output = "\n".join(line[:terminal_width] for line in lines)
    if not output.strip():
        output = "(no rows)"[:terminal_width]
    return Ok(value=output)
