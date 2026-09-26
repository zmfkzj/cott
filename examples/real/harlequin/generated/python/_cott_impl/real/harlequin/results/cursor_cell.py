import datetime
import decimal
from typing import Any, cast

from cott_runtime import Nothing, Option, Some

from real.harlequin.results_types import CellView, ResultsGrid


def _full_text(value: object) -> str:
    if value is None:
        return "∅ null"
    if isinstance(value, bool):
        return "✓ True" if value else "X False"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, "g")
    if isinstance(value, decimal.Decimal):
        return format(value, "f")
    if isinstance(value, (datetime.datetime, datetime.time)):
        text = value.isoformat(timespec="milliseconds")
        if text.endswith("+00:00"):
            text = text[: -len("+00:00")] + "Z"
        return text
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return repr(value)
    return str(value)


def cursor_cell(grid: ResultsGrid) -> Option[CellView]:
    result = grid.result
    columns = list(result.columns)
    row = grid.cursor.row
    column = grid.cursor.column
    if result.row_count == 0 or len(columns) == 0:
        return Nothing()
    if row >= result.row_count or column >= len(columns):
        return Nothing()
    handle = result.data
    if handle.tag != "harlequin.arrow_table":
        return Nothing()
    table: Any = handle.unwrap()
    rows = cast(object, table.slice(row, 1).column(column).to_pylist())
    if not isinstance(rows, list):
        return Nothing()
    values = cast(list[object], rows)
    if len(values) == 0:
        return Nothing()
    return Some(value=CellView(column=columns[column].name, text=_full_text(values[0])))
