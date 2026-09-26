from typing import Any, cast

from real.harlequin.results_types import ResultsGrid


def selection_text(grid: ResultsGrid) -> str:
    result = grid.result
    column_count = len(list(result.columns))
    row_count = int(result.row_count)
    if row_count == 0 or column_count == 0:
        return ""
    handle = result.data
    if handle.tag != "harlequin.arrow_table":
        return ""
    table: Any = handle.unwrap()
    top = min(int(grid.anchor.row), int(grid.cursor.row), row_count - 1)
    bottom = min(max(int(grid.anchor.row), int(grid.cursor.row)), row_count - 1)
    left = min(int(grid.anchor.column), int(grid.cursor.column), column_count - 1)
    right = min(max(int(grid.anchor.column), int(grid.cursor.column)), column_count - 1)
    count = bottom - top + 1
    sliced: Any = table.slice(top, count)
    columns: list[list[object]] = []
    for index in range(left, right + 1):
        raw = cast(object, sliced.column(index).to_pylist())
        columns.append(cast(list[object], raw) if isinstance(raw, list) else [])
    lines: list[str] = []
    for offset in range(count):
        cells: list[str] = []
        for values in columns:
            cells.append(str(values[offset]) if offset < len(values) else "None")
        lines.append("\t".join(cells))
    return "\n".join(lines)
