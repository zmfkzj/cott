from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.json_to_csv_types import CsvRecord as CsvRecord
"""Escape one field for a comma-separated record.

Fields containing a comma, double quote, carriage return, or line feed are
enclosed in double quotes. Each double quote inside a quoted field is
doubled. All other characters, including Unicode characters, are copied
unchanged."""
def escape_csv_field(field: str) -> str: ...

"""Serialize typed records as comma-separated values.

The output begins with the literal header `name,age,birthyear`. Records
follow in input order, with fields in name, age, birthyear order. Each field
is serialized by `escape_csv_field`.

Every record ends with CRLF (`\\r\\n`), including the last record. Empty
input therefore returns exactly `name,age,birthyear\\r\\n`."""
def serialize_csv(rows: CottList[CsvRecord]) -> str: ...

__all__ = ["CsvRecord", "escape_csv_field", "serialize_csv"]
