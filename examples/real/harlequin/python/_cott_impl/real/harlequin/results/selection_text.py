from typing import Any, cast

import pyarrow

from real.harlequin.results_types import ResultsGrid


def selection_text(grid: ResultsGrid) -> str:
    result = grid.result
    row_count = int(result.row_count)
    column_count = len(result.columns)
    if row_count == 0 or column_count == 0:
        return ""

    handle = result.data
    if handle.tag != "harlequin.arrow_table":
        raise TypeError("Expected a harlequin.arrow_table")
    payload = handle.unwrap()
    if not isinstance(payload, pyarrow.Table):
        raise TypeError("ArrowTable does not contain a pyarrow.Table")
    table: Any = payload

    top = min(int(grid.anchor.row), int(grid.cursor.row), row_count - 1)
    bottom = min(max(int(grid.anchor.row), int(grid.cursor.row)), row_count - 1)
    left = min(int(grid.anchor.column), int(grid.cursor.column), column_count - 1)
    right = min(max(int(grid.anchor.column), int(grid.cursor.column)), column_count - 1)

    selected: Any = table.slice(top, bottom - top + 1)
    columns: list[list[object]] = []
    for index in range(left, right + 1):
        raw: object = cast(object, selected.column(index).to_pylist())
        if not isinstance(raw, list):
            raise TypeError("Arrow column did not return a list")
        columns.append(cast(list[object], raw))

    return "\n".join(
        "\t".join(str(values[offset]) for values in columns)
        for offset in range(bottom - top + 1)
    )
