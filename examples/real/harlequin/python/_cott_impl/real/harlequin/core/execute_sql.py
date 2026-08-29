import sqlite3
from collections.abc import Iterable
from contextlib import closing
from typing import cast

from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, QueryResult, SqlClientError, SqlClientError_EmptySql, SqlClientError_ReadOnlyViolation, SqlClientError_SqliteFailure, SqlClientError_UnterminatedSql, SqlClientError_UnsupportedValue, TypedRow


def _split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    statements: list[str] = []
    characters: list[str] = []
    delimiter = ""
    has_sql = False
    index = 0
    while index < len(sql):
        character = sql[index]
        following = sql[index + 1] if index + 1 < len(sql) else ""
        if delimiter == "--":
            characters.append(character)
            if character == "\n" or character == "\r":
                delimiter = ""
            index += 1
        elif delimiter == "/*":
            characters.append(character)
            if character == "*" and following == "/":
                characters.append(following)
                delimiter = ""
                index += 2
            else:
                index += 1
        elif delimiter == "'":
            characters.append(character)
            if character == "'":
                if following == "'":
                    characters.append(following)
                    index += 2
                else:
                    delimiter = ""
                    index += 1
            else:
                index += 1
        elif delimiter == '"':
            characters.append(character)
            if character == '"':
                if following == '"':
                    characters.append(following)
                    index += 2
                else:
                    delimiter = ""
                    index += 1
            else:
                index += 1
        elif delimiter == "`":
            characters.append(character)
            if character == "`":
                if following == "`":
                    characters.append(following)
                    index += 2
                else:
                    delimiter = ""
                    index += 1
            else:
                index += 1
        elif delimiter == "[":
            characters.append(character)
            if character == "]":
                delimiter = ""
            index += 1
        elif character == "-" and following == "-":
            characters.append(character)
            characters.append(following)
            delimiter = "--"
            index += 2
        elif character == "/" and following == "*":
            characters.append(character)
            characters.append(following)
            delimiter = "/*"
            index += 2
        elif character == "'" or character == '"' or character == "`" or character == "[":
            characters.append(character)
            delimiter = character
            has_sql = True
            index += 1
        elif character == ";":
            if has_sql:
                statements.append("".join(characters).strip())
            characters = []
            has_sql = False
            index += 1
        else:
            characters.append(character)
            if not character.isspace():
                has_sql = True
            index += 1

    if delimiter != "" and delimiter != "--":
        return Err(error=SqlClientError_UnterminatedSql(delimiter=delimiter))
    if has_sql:
        statements.append("".join(characters).strip())
    if len(statements) == 0:
        return Err(error=SqlClientError_EmptySql())
    return Ok(value=CottList(values=tuple(statements)))


def _connect(database: DatabaseTarget) -> sqlite3.Connection:
    match database:
        case DatabaseTarget_Memory():
            return sqlite3.connect(":memory:")
        case DatabaseTarget_File() as target:
            return sqlite3.connect(target.path)


def _cell(value: object) -> Result[Cell, SqlClientError]:
    match value:
        case None:
            return Ok(value=Cell_Null())
        case bool():
            return Err(error=SqlClientError_UnsupportedValue(type_name="bool"))
        case int() as integer:
            return Ok(value=Cell_Integer(value=integer))
        case float() as real:
            return Ok(value=Cell_Real(value=real))
        case str() as text:
            return Ok(value=Cell_Text(value=text))
        case bytes() as blob:
            return Ok(value=Cell_Blob(value=blob))
        case bytearray():
            return Err(error=SqlClientError_UnsupportedValue(type_name="bytearray"))
        case memoryview():
            return Err(error=SqlClientError_UnsupportedValue(type_name="memoryview"))
        case _:
            return Err(error=SqlClientError_UnsupportedValue(type_name="object"))


def _read_only_failure(error: sqlite3.Error) -> bool:
    message = str(error).casefold()
    return "readonly" in message or "read-only" in message


def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]:
    match _split_statements(sql):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=statements):
            try:
                connection = _connect(database)
            except sqlite3.Error as error:
                return Err(error=SqlClientError_SqliteFailure(message=str(error)))

            results: list[QueryResult] = []
            statement = ""
            with closing(connection):
                try:
                    for statement in statements:
                        if read_only:
                            connection.execute("PRAGMA query_only = ON").close()
                        cursor = connection.execute(statement)
                        with closing(cursor):
                            description = cursor.description
                            if description is None:
                                columns: CottList[str] = CottList(values=())
                                rows: CottList[TypedRow] = CottList(values=())
                                affected_rows = cursor.rowcount if cursor.rowcount >= 0 else 0
                            else:
                                columns = CottList(values=tuple(column[0] for column in description))
                                typed_rows: list[TypedRow] = []
                                source_rows = cast(Iterable[tuple[object, ...]], cursor)
                                for source_row in source_rows:
                                    cells: list[Cell] = []
                                    for value in source_row:
                                        match _cell(value):
                                            case Err(error=error):
                                                return Err(error=error)
                                            case Ok(value=cell):
                                                cells.append(cell)
                                    typed_rows.append(TypedRow(values=CottList(values=tuple(cells))))
                                rows = CottList(values=tuple(typed_rows))
                                affected_rows = cursor.rowcount if cursor.rowcount >= 0 else 0
                            results.append(QueryResult(columns=columns, rows=rows, affected_rows=affected_rows))
                    connection.commit()
                except sqlite3.Error as error:
                    if read_only and statement != "" and _read_only_failure(error):
                        return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))
                    return Err(error=SqlClientError_SqliteFailure(message=str(error)))

            return Ok(value=CottList(values=tuple(results)))
