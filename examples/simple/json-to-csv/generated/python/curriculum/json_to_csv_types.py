from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CsvRecord:
    __hash__ = None
    name: str
    age: str
    birthyear: str

"""Escape one field for a comma-separated record.

Fields containing a comma, double quote, carriage return, or line feed are
enclosed in double quotes. Each double quote inside a quoted field is
doubled. All other characters, including Unicode characters, are copied
unchanged."""
"""Serialize typed records as comma-separated values.

The output begins with the literal header `name,age,birthyear`. Records
follow in input order, with fields in name, age, birthyear order. Each field
is serialized by `escape_csv_field`.

Every record ends with CRLF (`\\r\\n`), including the last record. Empty
input therefore returns exactly `name,age,birthyear\\r\\n`."""
__all__ = ["CsvRecord"]
