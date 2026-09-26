import contextlib
from collections.abc import Iterable
from typing import Any, Final, cast

from cott_runtime import Err, Nothing, Ok, Result, Some

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed

_TITLE: Final[str] = "Data Catalog Interaction Error"
_TAG: Final[str] = "harlequin.session"
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"
_MALFORMED: Final[str] = "The connection handle is malformed."


def _fail(message: str) -> Result[Some[str] | Nothing, QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _first(row: object) -> Some[str] | Nothing:
    if row is None:
        return Nothing()
    if isinstance(row, (str, bytes)):
        return Some(value=str(row))
    if isinstance(row, Iterable):
        for item in cast(Iterable[object], row):
            return Some(value=str(item))
        return Nothing()
    return Some(value=str(row))


def _dbapi(driver: Any, sql: str, active: list[object], own_cursor: bool, encode: bool) -> Some[str] | Nothing:
    cursor: Any = driver.cursor() if own_cursor else None
    try:
        if own_cursor:
            active.append(cast(object, cursor))
            cursor.execute(sql.encode("utf-8") if encode else sql)
        else:
            cursor = driver.execute(sql)
            active.append(cast(object, cursor))
        if cast(object, cursor.description) is None:
            return Nothing()
        return _first(cast(object, cursor.fetchone()))
    finally:
        if cursor is not None:
            current = cast(object, cursor)
            active[:] = [a for a in active if a is not current]
            cursor.close()


def _duckdb(driver: Any, sql: str, active: list[object]) -> Some[str] | Nothing:
    conn = cast(object, driver)
    active.append(conn)
    try:
        driver.execute(sql)
        if cast(object, driver.description) is None:
            return Nothing()
        return _first(cast(object, driver.fetchone()))
    finally:
        active[:] = [a for a in active if a is not conn]


def _bigquery(driver: Any, sql: str) -> Some[str] | Nothing:
    rows: Any = driver.query(sql).result()
    for row in rows:
        record: Any = row
        return _first(cast(object, tuple(record.values())))
    return Nothing()


def _cassandra(driver: Any, sql: str) -> Some[str] | Nothing:
    result: Any = driver.execute(sql)
    row = cast(object, result.one())
    return _first(row)


def _nebula(driver: Any, sql: str) -> Some[str] | Nothing:
    result: Any = driver.execute(sql)
    if not bool(cast(object, result.is_succeeded())):
        raise RuntimeError(str(cast(object, result.error_msg())))
    if bool(cast(object, result.is_empty())):
        return Nothing()
    size = cast(object, result.row_size())
    if not isinstance(size, int) or size == 0:
        return Nothing()
    values: Any = result.row_values(0)
    if len(values) == 0:
        return Nothing()
    return Some(value=str(cast(object, values[0].cast())))


def run_scalar_query(connection: Connection, sql: str) -> Result[Some[str] | Nothing, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return _fail(_MALFORMED)
    adapter = payload["adapter"]
    active_raw = payload["active"]
    lock_raw = payload["lock"]
    modes = payload["modes"]
    mode = payload["transaction_mode"]
    if (
        not isinstance(adapter, str)
        or not isinstance(active_raw, list)
        or not isinstance(payload["closed"], bool)
        or not isinstance(payload["cleanup"], contextlib.ExitStack)
        or not isinstance(lock_raw, contextlib.AbstractContextManager)
        or not isinstance(payload["request"], ConnectionRequest)
        or not isinstance(modes, list)
        or not all(isinstance(m, str) for m in cast(list[object], modes))
        or not (mode is None or isinstance(mode, str))
        or payload["driver"] is None
    ):
        return _fail(_MALFORMED)
    lock = cast(contextlib.AbstractContextManager[object], lock_raw)
    active = cast(list[object], active_raw)
    with lock:
        if payload["closed"] is True:
            return _fail("The connection is closed.")
        driver: Any = payload["driver"]
        try:
            if adapter == "DuckDb":
                value = _duckdb(driver, sql, active)
            elif adapter == "Sqlite":
                value = _dbapi(driver, sql, active, False, False)
            elif adapter == "Postgres":
                value = _dbapi(driver, sql, active, True, True)
            elif adapter == "BigQuery":
                value = _bigquery(driver, sql)
            elif adapter == "Cassandra":
                value = _cassandra(driver, sql)
            elif adapter == "NebulaGraph":
                value = _nebula(driver, sql)
            else:
                value = _dbapi(driver, sql, active, True, False)
        except Exception as error:
            return _fail(str(error))
    return Ok(value=value)
