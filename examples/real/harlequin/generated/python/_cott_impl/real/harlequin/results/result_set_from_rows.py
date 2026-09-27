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


def _dedupe(columns: CottList[ColumnInfo]) -> list[str]:
    used: set[str] = set()
    counters: dict[str, int] = {}
    names: list[str] = []
    for column in columns:
        name = column.name
        unique = name
        if unique in used:
            counter = counters.get(name, 0)
            unique = f"{name}{counter}"
            while unique in used:
                counter += 1
                unique = f"{name}{counter}"
            counters[name] = counter + 1
        used.add(unique)
        names.append(unique)
    return names


def result_set_from_rows(statement: str, columns: CottList[ColumnInfo], rows: CottList[CottList[CellValue]], viewer_max_rows: Option[U64], elapsed_ms: U64) -> ResultSet:
    pa: Any = pyarrow
    names = _dedupe(columns)
    width = len(names)
    values_by_column: list[list[object]] = [[] for _ in range(width)]
    kinds = ["null"] * width
    mixed = [False] * width
    for row in rows:
        seen = 0
        for index, cell in enumerate(row):
            if index >= width:
                break
            kind = _kind(cell)
            if kind != "null" and not mixed[index]:
                if kinds[index] == "null":
                    kinds[index] = kind
                elif kinds[index] != kind:
                    mixed[index] = True
            values_by_column[index].append(_payload(cell))
            seen += 1
        for index in range(seen, width):
            values_by_column[index].append(None)

    arrays: list[object] = []
    for index, values in enumerate(values_by_column):
        if mixed[index]:
            for offset, value in enumerate(values):
                if value is not None:
                    values[offset] = str(value)
            arrow_type: object = cast(object, pa.string())
        elif kinds[index] == "null":
            arrow_type = cast(object, pa.null())
        elif kinds[index] == "bool":
            arrow_type = cast(object, pa.bool_())
        elif kinds[index] == "int64":
            arrow_type = cast(object, pa.int64())
        elif kinds[index] == "float64":
            arrow_type = cast(object, pa.float64())
        elif kinds[index] == "string":
            arrow_type = cast(object, pa.string())
        else:
            arrow_type = cast(object, pa.binary())
        array: object = cast(object, pa.array(values, type=arrow_type))
        if not isinstance(array, pa.Array):
            raise TypeError("pyarrow did not return an Array")
        arrays.append(array)

    fetched = len(rows)
    if width:
        table: object = cast(object, pa.Table.from_arrays(arrays, names=names))
    else:
        struct_array: object = cast(object, pa.StructArray.from_buffers(pa.struct([]), fetched, [None], null_count=0, children=[]))
        if not isinstance(struct_array, pa.StructArray):
            raise TypeError("pyarrow did not return a StructArray")
        table = cast(object, pa.Table.from_struct_array(struct_array))
    if not isinstance(table, pa.Table):
        raise TypeError("pyarrow did not return a Table")

    row_count = min(fetched, viewer_max_rows.value) if isinstance(viewer_max_rows, Some) else fetched
    out_columns = [ColumnInfo(name=name, type_label=column.type_label) for name, column in zip(names, columns)]
    return ResultSet(statement=statement, columns=CottList(values=out_columns), data=Opaque(tag="harlequin.arrow_table", value=table), row_count=row_count, fetched_row_count=fetched, truncated=False, elapsed_ms=elapsed_ms)
