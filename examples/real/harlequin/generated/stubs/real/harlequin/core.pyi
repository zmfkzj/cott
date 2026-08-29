from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.core_types import Cell as Cell, Cell_Blob as Cell_Blob, Cell_Integer as Cell_Integer, Cell_Null as Cell_Null, Cell_Real as Cell_Real, Cell_Text as Cell_Text, DatabaseTarget as DatabaseTarget, DatabaseTarget_File as DatabaseTarget_File, DatabaseTarget_Memory as DatabaseTarget_Memory, QueryResult as QueryResult, SqlClientError as SqlClientError, SqlClientError_EmptySql as SqlClientError_EmptySql, SqlClientError_ReadOnlyViolation as SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure as SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue as SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql as SqlClientError_UnterminatedSql, TypedRow as TypedRow
def split_statements(sql: str) -> Result[CottList[str], SqlClientError]: ...

def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]: ...

__all__ = ["Cell", "Cell_Blob", "Cell_Integer", "Cell_Null", "Cell_Real", "Cell_Text", "DatabaseTarget", "DatabaseTarget_File", "DatabaseTarget_Memory", "QueryResult", "SqlClientError", "SqlClientError_EmptySql", "SqlClientError_ReadOnlyViolation", "SqlClientError_SqliteFailure", "SqlClientError_UnsupportedValue", "SqlClientError_UnterminatedSql", "TypedRow", "execute_sql", "split_statements"]
