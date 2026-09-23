from typing import LiteralString, cast

import psycopg
from cott_runtime import CottList, Err, Ok, Result
from real.pgcli_types import ConnectionSettings, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, QueryResult


def _cell(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    try:
        conn = psycopg.connect(host=connection.host, port=connection.port, user=connection.user, password=connection.password, dbname=connection.database)
    except psycopg.Error:
        return Err(error=DatabaseError_ConnectionFailed(message="could not connect to database"))
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(cast(LiteralString, sql))
                description = cur.description
                if description is None:
                    return Ok(value=QueryResult(columns=CottList(values=[]), rows=CottList(values=[])))
                columns = [column.name for column in description]
                rows = [CottList(values=[_cell(value) for value in row]) for row in cur.fetchall()]
    except psycopg.Error:
        if conn.broken:
            return Err(error=DatabaseError_ConnectionFailed(message="database connection lost"))
        return Err(error=DatabaseError_QueryFailed(message="query execution failed"))
    return Ok(value=QueryResult(columns=CottList(values=columns), rows=CottList(values=rows)))
