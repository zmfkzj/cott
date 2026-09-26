from typing import cast

import psycopg
from cott_runtime import CottList, Err, Ok, Result

from real.pgcli.connection_types import ConnectError, ConnectError_Failed, Executor


def _fail(message: str) -> Result[CottList[str], ConnectError]:
    return Err(error=ConnectError_Failed(message=message))


def read_search_path(executor: Executor) -> Result[CottList[str], ConnectError]:
    conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    try:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM unnest(current_schemas(true))")
                rows = cur.fetchall()
            return Ok(value=CottList(values=[str(row[0]) for row in rows]))
        except psycopg.ProgrammingError:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM current_schemas(true)")
                first = cur.fetchone()
            if first is None:
                return _fail("'NoneType' object is not subscriptable")
            value = first[0]
            if isinstance(value, list):
                items = cast(list[object], value)
                return Ok(value=CottList(values=[str(item) for item in items]))
            return _fail("current_schemas(true) did not return an array")
    except Exception as error:
        return _fail(str(error))
