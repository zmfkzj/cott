import decimal

from cott_runtime import CottList, Opaque
from real.pgcli.output_types import (
    Cell,
    Cell_Array,
    Cell_Boolean,
    Cell_Decimal,
    Cell_Float,
    Cell_Integer,
    Cell_Null,
    Cell_Text,
    ResultRows,
)


def _convert_cell(cell: Cell) -> object:
    if isinstance(cell, Cell_Null):
        return None
    if isinstance(cell, Cell_Text):
        return str(cell.value)
    if isinstance(cell, Cell_Integer):
        return int(cell.value)
    if isinstance(cell, Cell_Float):
        return float(cell.value)
    if isinstance(cell, Cell_Decimal):
        return decimal.Decimal(cell.value)
    if isinstance(cell, Cell_Boolean):
        return bool(cell.value)
    if isinstance(cell, Cell_Array):
        return [_convert_cell(item) for item in cell.items]
    return str(cell.value)


def result_rows_from_cells(rows: CottList[CottList[Cell]]) -> ResultRows:
    value: list[tuple[object, ...]] = [tuple(_convert_cell(cell) for cell in row) for row in rows]
    return Opaque(tag="pgcli.result-rows", value=value)
