from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseTarget_Memory:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseTarget_File:
    __hash__ = None
    path: Path

DatabaseTarget: TypeAlias = Union[DatabaseTarget_Memory, DatabaseTarget_File]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Null:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Integer:
    __hash__ = None
    value: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Real:
    __hash__ = None
    value: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Text:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Blob:
    __hash__ = None
    value: bytes

Cell: TypeAlias = Union[Cell_Null, Cell_Integer, Cell_Real, Cell_Text, Cell_Blob]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypedRow:
    __hash__ = None
    values: CottList[Cell]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "values", _cott_validate_abi(self.values, CottList[Cell], path="$.values"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryResult:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[TypedRow]
    affected_rows: I64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[TypedRow], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "affected_rows", _cott_validate_abi(self.affected_rows, I64, path="$.affected_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_EmptySql:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_UnterminatedSql:
    __hash__ = None
    delimiter: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_ReadOnlyViolation:
    __hash__ = None
    statement: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_SqliteFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlClientError_UnsupportedValue:
    __hash__ = None
    type_name: str

SqlClientError: TypeAlias = Union[SqlClientError_EmptySql, SqlClientError_UnterminatedSql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue]

__all__ = ["Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "QueryResult", "SqlClientError", "SqlClientError_EmptySql", "SqlClientError_ReadOnlyViolation", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "TypedRow"]
