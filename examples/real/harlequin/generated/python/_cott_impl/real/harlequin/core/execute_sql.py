import math
import sqlite3
from pathlib import Path
from typing import Final, cast

from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.core import split_statements
from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, DatabaseTarget, DatabaseTarget_File, QueryResult, SqlClientError, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, TypedRow

_TRANSACTION_KEYWORDS: Final[str] = "BEGIN START COMMIT ROLLBACK SAVEPOINT RELEASE END"
_ASCII_WHITESPACE: Final[str] = " \t\n\v\f\r"
_WORD_CHARS: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
_CONTROL_MESSAGE: Final[str] = "transaction control statements are not permitted"


def _leading_keyword(statement: str) -> str:
    i = 0
    n = len(statement)
    while i < n:
        if statement[i] in _ASCII_WHITESPACE:
            i += 1
        elif statement.startswith("--", i):
            end = statement.find("\n", i)
            i = n if end < 0 else end + 1
        elif statement.startswith("/*", i):
            end = statement.find("*/", i + 2)
            i = n if end < 0 else end + 2
        else:
            break
    j = i
    while j < n and statement[j] in _WORD_CHARS:
        j += 1
    return statement[i:j].upper()


def _to_cell(value: object) -> Cell | str:
    if value is None:
        return Cell_Null()
    if isinstance(value, int):
        return Cell_Integer(value=value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return "REAL"
        return Cell_Real(value=value)
    if isinstance(value, str):
        return Cell_Text(value=value)
    if isinstance(value, memoryview):
        return Cell_Blob(value=bytes(cast(memoryview[int], value)))
    if isinstance(value, (bytes, bytearray)):
        return Cell_Blob(value=bytes(value))
    return "UNKNOWN"


def _is_readonly_error(exc: sqlite3.Error) -> bool:
    return (exc.sqlite_errorcode & 0xFF) == sqlite3.SQLITE_READONLY


def _open(database: DatabaseTarget, read_only: bool) -> sqlite3.Connection:
    if isinstance(database, DatabaseTarget_File):
        uri = Path(database.path).resolve().as_uri() + ("?mode=ro" if read_only else "?mode=rw")
        return sqlite3.connect(uri, uri=True, isolation_level=None)
    return sqlite3.connect(":memory:", isolation_level=None)


def _rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("ROLLBACK").close()
    except sqlite3.Error:
        return


def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]:
    split = split_statements(sql)
    if isinstance(split, Err):
        return Err(error=split.error)
    statements: list[str] = [statement for statement in split.value]
    keywords = _TRANSACTION_KEYWORDS.split()
    for statement in statements:
        if _leading_keyword(statement) in keywords:
            return Err(error=SqlClientError_SqliteFailure(message=_CONTROL_MESSAGE))
    try:
        connection = _open(database, read_only)
    except sqlite3.Error as exc:
        return Err(error=SqlClientError_SqliteFailure(message=str(exc)))
    results: list[QueryResult] = []
    in_transaction = False
    try:
        if read_only:
            connection.execute("PRAGMA query_only = ON").close()
        connection.execute("BEGIN").close()
        in_transaction = True
        for statement in statements:
            try:
                cursor = connection.execute(statement)
            except sqlite3.Error as exc:
                if read_only and _is_readonly_error(exc):
                    _rollback(connection)
                    in_transaction = False
                    return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))
                raise
            try:
                try:
                    raw_rows = cursor.fetchall()
                except sqlite3.Error as exc:
                    if read_only and _is_readonly_error(exc):
                        _rollback(connection)
                        in_transaction = False
                        return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))
                    raise
                description = cursor.description
                columns = [str(column[0]) for column in description] if description is not None else []
                rows: list[TypedRow] = []
                for raw in raw_rows:
                    cells: list[Cell] = []
                    for value in cast(tuple[object, ...], raw):
                        cell = _to_cell(value)
                        if isinstance(cell, str):
                            _rollback(connection)
                            in_transaction = False
                            return Err(error=SqlClientError_UnsupportedValue(type_name=cell))
                        cells.append(cell)
                    rows.append(TypedRow(values=CottList(values=cells)))
                affected = cursor.rowcount if cursor.rowcount >= 0 else -1
            finally:
                cursor.close()
            results.append(QueryResult(columns=CottList(values=columns), rows=CottList(values=rows), affected_rows=affected))
        connection.execute("COMMIT").close()
        in_transaction = False
    except sqlite3.Error as exc:
        if in_transaction:
            _rollback(connection)
        return Err(error=SqlClientError_SqliteFailure(message=str(exc)))
    finally:
        connection.close()
    return Ok(value=CottList(values=results))
