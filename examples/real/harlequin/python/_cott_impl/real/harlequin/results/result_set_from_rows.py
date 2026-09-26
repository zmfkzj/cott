from typing import Any, cast

import pyarrow

from cott_runtime import CottList, Opaque, Option, Some, U64

from real.harlequin.results_types import CellValue, CellValue_Blob, CellValue_Boolean, CellValue_Integer, CellValue_Null, CellValue_Real, CellValue_Text, ColumnInfo, ResultSet


def _kind(value: CellValue) -> str:
    if isinstance(value, CellValue_Null):
        return "null"
    if isinstance(value, CellValue_Boolean):
        return "bool"
    if isinstance(value, CellValue_Integer):
        return "int64"
    if isinstance(value, CellValue_Real):
        return "float64"
    if isinstance(value, CellValue_Text):
        return "string"
    return "binary"


def _payload(value: CellValue) -> object:
    if isinstance(value, CellValue_Null):
        return None
    if isinstance(value, CellValue_Boolean):
        return value.value
    if isinstance(value, CellValue_Integer):
        return value.value
    if isinstance(value, CellValue_Real):
        return value.value
    if isinstance(value, CellValue_Text):
        return value.value
    blob: CellValue_Blob = value
    return blob.value


def _dedupe(names: list[str]) -> list[str]:
    used: set[str] = set()
    counters: dict[str, int] = {}
    result: list[str] = []
    for name in names:
        unique = name
        if unique in used:
            counter = counters.get(name, 0)
            unique = f"{name}{counter}"
            while unique in used:
                counter += 1
                unique = f"{name}{counter}"
            counters[name] = counter + 1
        used.add(unique)
        result.append(unique)
    return result


def result_set_from_rows(statement: str, columns: CottList[ColumnInfo], rows: CottList[CottList[CellValue]], viewer_max_rows: Option[U64], elapsed_ms: U64) -> ResultSet:
    pa: Any = pyarrow
    infos = list(columns)
    width = len(infos)
    grid: list[list[CellValue]] = []
    for row in rows:
        cells = list(row)[:width]
        while len(cells) < width:
            cells.append(CellValue_Null())
        grid.append(cells)
    arrays: list[object] = []
    for index in range(width):
        kind = "null"
        for cells in grid:
            candidate = _kind(cells[index])
            if candidate != "null":
                kind = candidate
                break
        mixed = any(_kind(cells[index]) not in ("null", kind) for cells in grid)
        values: list[object] = []
        for cells in grid:
            raw = _payload(cells[index])
            values.append(str(raw) if mixed and raw is not None else raw)
        if mixed:
            kind = "string"
        arrow_types = {"null": pa.null(), "bool": pa.bool_(), "int64": pa.int64(), "float64": pa.float64(), "string": pa.string(), "binary": pa.binary()}
        arrays.append(cast(object, pa.array(values, type=arrow_types[kind])))
    names = _dedupe([info.name for info in infos])
    table = cast(object, pa.Table.from_arrays(arrays, names=names))
    fetched = len(grid)
    row_count = fetched
    if isinstance(viewer_max_rows, Some):
        row_count = min(fetched, viewer_max_rows.value)
    out_columns = [ColumnInfo(name=name, type_label=info.type_label) for name, info in zip(names, infos)]
    return ResultSet(statement=statement, columns=CottList(values=out_columns), data=Opaque(tag="harlequin.arrow_table", value=table), row_count=row_count, fetched_row_count=fetched, truncated=False, elapsed_ms=elapsed_ms)
