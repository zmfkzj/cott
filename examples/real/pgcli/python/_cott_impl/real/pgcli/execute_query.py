from typing import cast

import psycopg
import psycopg.conninfo
from cott_runtime import CottList, Err, Ok, Result
from real.pgcli_types import ConnectionSettings, DatabaseError, DatabaseError_ConnectionFailed, DatabaseError_QueryFailed, QueryResult


def _cell(value: object) -> str:
    if value is None:
        return "<null>"
    if isinstance(value, memoryview):
        return "\\x" + bytes(cast(memoryview[int], value)).hex()
    if isinstance(value, (bytes, bytearray)):
        return "\\x" + bytes(value).hex()
    return str(value)


def _query_failed(error: psycopg.Error) -> Result[QueryResult, DatabaseError]:
    sqlstate = error.sqlstate or ""
    primary = error.diag.message_primary or ""
    return Err(error=DatabaseError_QueryFailed(message=f"{sqlstate}: {primary}"))


def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    fields: dict[str, str] = {}
    if connection.host:
        fields["host"] = connection.host
    if connection.port:
        fields["port"] = connection.port
    if connection.user:
        fields["user"] = connection.user
    if connection.password:
        fields["password"] = connection.password
    if connection.database:
        fields["dbname"] = connection.database
    try:
        conninfo = psycopg.conninfo.make_conninfo("", **fields)
        conn = psycopg.connect(conninfo, autocommit=True)
    except psycopg.Error:
        return Err(error=DatabaseError_ConnectionFailed(message="could not connect to database"))
    try:
        columns: list[str] = []
        rows: list[CottList[str]] = []
        with conn.cursor() as cur:
            cur.execute(sql.encode("utf-8"))
            while True:
                description = cur.description
                if description is not None:
                    columns = [column.name for column in description]
                    rows = [CottList(values=[_cell(value) for value in row]) for row in cur.fetchall()]
                if not cur.nextset():
                    break
    except psycopg.Error as error:
        return _query_failed(error)
    finally:
        conn.close()
    return Ok(value=QueryResult(columns=CottList(values=columns), rows=CottList(values=rows)))
