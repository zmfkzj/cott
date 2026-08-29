from typing import Any

import psycopg
from cott_runtime import CottList, Err, Ok, Result
from real.pgcli_types import ConnectionSettings, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, QueryResult


def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    try:
        database: psycopg.Connection[tuple[Any, ...]] = psycopg.connect(host=connection.host, port=connection.port, user=connection.user, password=connection.password, dbname=connection.database)
    except psycopg.Error as error:
        return Err(error=DatabaseError_ConnectionFailed(message=str(error)))

    try:
        cursor: psycopg.Cursor[tuple[Any, ...]]
        with database:
            with database.cursor() as cursor:
                cursor.execute(sql.encode("utf-8"))
                description: list[psycopg.Column] | None = cursor.description
                if description is None:
                    columns: CottList[str] = CottList(values=())
                    rows: CottList[CottList[str]] = CottList(values=())
                else:
                    columns = CottList(values=tuple(column.name for column in description))
                    raw_rows: list[tuple[Any, ...]] = cursor.fetchall()
                    converted_rows: tuple[CottList[str], ...] = tuple(CottList(values=tuple(str(value) for value in raw_row)) for raw_row in raw_rows)
                    rows = CottList(values=converted_rows)
        return Ok(value=QueryResult(columns=columns, rows=rows))
    except psycopg.Error as error:
        return Err(error=DatabaseError_QueryFailed(message=str(error)))
