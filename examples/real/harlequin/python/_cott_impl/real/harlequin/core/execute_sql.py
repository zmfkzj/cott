import sqlite3
from pathlib import Path
from typing import Final, cast

from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, DatabaseTarget, DatabaseTarget_File, QueryResult, SqlClientError, SqlClientError_EmptySql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql, TypedRow

_READ_KEYWORDS: Final[str] = "SELECT WITH VALUES EXPLAIN"
_SAFE_PRAGMAS: Final[str] = "table_info table_xinfo table_list index_list index_info index_xinfo foreign_key_list foreign_key_check database_list collation_list compile_options function_list module_list pragma_list user_version application_id schema_version data_version page_count page_size freelist_count encoding integrity_check quick_check"


def _split_sql(sql: str) -> tuple[list[str], str | None]:
    statements: list[str] = []
    start = 0
    meaningful = False
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        if ch == "-" and sql.startswith("--", i):
            end = sql.find("\n", i)
            i = n if end < 0 else end + 1
            continue
        if ch == "/" and sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            if end < 0:
                return statements, "*/"
            i = end + 2
            continue
        if ch in "'\"`[":
            close = "]" if ch == "[" else ch
            j = i + 1
            while True:
                k = sql.find(close, j)
                if k < 0:
                    return statements, close
                if close != "]" and sql.startswith(close * 2, k):
                    j = k + 2
                    continue
                i = k + 1
                break
            meaningful = True
            continue
        if ch == ";":
            candidate = sql[start : i + 1]
            if sqlite3.complete_statement(candidate):
                if meaningful:
                    statements.append(candidate.strip())
                start = i + 1
                meaningful = False
            i += 1
            continue
        if not ch.isspace():
            meaningful = True
        i += 1
    if meaningful:
        statements.append(sql[start:].strip())
    return statements, None


def _leading_keyword(statement: str) -> str:
    i = 0
    n = len(statement)
    while i < n:
        if statement[i].isspace():
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
    while j < n and (statement[j].isalpha() or statement[j] == "_"):
        j += 1
    return statement[i:j].upper()


def _is_read_statement(statement: str) -> bool:
    keyword = _leading_keyword(statement)
    if keyword in _READ_KEYWORDS.split():
        return True
    return keyword == "PRAGMA" and "=" not in statement


def _to_cell(value: object) -> Cell | None:
    if value is None:
        return Cell_Null()
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Cell_Integer(value=value)
    if isinstance(value, float):
        return Cell_Real(value=value)
    if isinstance(value, str):
        return Cell_Text(value=value)
    if isinstance(value, memoryview):
        view = cast(memoryview[int], value)
        return Cell_Blob(value=view.tobytes())
    if isinstance(value, (bytes, bytearray)):
        return Cell_Blob(value=bytes(value))
    return None


def _unsupported_type_name(value: object) -> str:
    if isinstance(value, bool):
        return "bool"
    return "object"


def _authorize_read(denied: list[bool], action: int, arg1: str | None, arg2: str | None) -> int:
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_PRAGMA and arg2 is None and arg1 is not None and arg1.lower() in _SAFE_PRAGMAS.split():
        return sqlite3.SQLITE_OK
    denied[0] = True
    return sqlite3.SQLITE_DENY


def _connect(database: DatabaseTarget, read_only: bool) -> sqlite3.Connection:
    if isinstance(database, DatabaseTarget_File):
        path = Path(database.path)
        if read_only:
            return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, autocommit=True)
        return sqlite3.connect(path, autocommit=True)
    return sqlite3.connect(":memory:", autocommit=True)


def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]:
    statements, unterminated = _split_sql(sql)
    if unterminated is not None:
        return Err(error=SqlClientError_UnterminatedSql(delimiter=unterminated))
    if not statements:
        return Err(error=SqlClientError_EmptySql())
    if read_only:
        for statement in statements:
            if not _is_read_statement(statement):
                return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))
    try:
        connection = _connect(database, read_only)
    except sqlite3.Error as exc:
        return Err(error=SqlClientError_SqliteFailure(message=str(exc)))
    results: list[QueryResult] = []
    denied: list[bool] = [False]
    try:
        if read_only:
            connection.set_authorizer(lambda action, arg1, arg2, _db, _trigger: _authorize_read(denied, action, arg1, arg2))
        for statement in statements:
            denied[0] = False
            try:
                cursor = connection.execute(statement)
            except sqlite3.DatabaseError as exc:
                if denied[0]:
                    return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))
                raise exc
            columns = [str(column[0]) for column in cursor.description] if cursor.description is not None else []
            rows: list[TypedRow] = []
            for raw in cursor.fetchall():
                cells: list[Cell] = []
                for value in raw:
                    cell = _to_cell(value)
                    if cell is None:
                        return Err(error=SqlClientError_UnsupportedValue(type_name=_unsupported_type_name(value)))
                    cells.append(cell)
                rows.append(TypedRow(values=CottList(values=cells)))
            affected = cursor.rowcount if cursor.rowcount > 0 else 0
            cursor.close()
            results.append(QueryResult(columns=CottList(values=columns), rows=CottList(values=rows), affected_rows=affected))
    except sqlite3.Error as exc:
        return Err(error=SqlClientError_SqliteFailure(message=str(exc)))
    finally:
        connection.close()
    return Ok(value=CottList(values=results))
