import contextlib
import threading
from collections.abc import Iterable
from typing import Any, Final, cast

import cassandra.query
import psycopg.pq
from cott_runtime import CottContractViolation, Err, Nothing, Ok, Option, Result, Some, _cott_fixture_database
from real.harlequin.adapters_types import (
    AdapterKind,
    AdapterKind_Adbc,
    AdapterKind_BigQuery,
    AdapterKind_Cassandra,
    AdapterKind_Databricks,
    AdapterKind_DuckDb,
    AdapterKind_MySql,
    AdapterKind_NebulaGraph,
    AdapterKind_Odbc,
    AdapterKind_Postgres,
    AdapterKind_Sqlite,
    AdapterKind_Trino,
    Connection,
    ConnectionRequest,
    QueryError,
    QueryError_Failed,
)

_TITLE: Final[str] = "Data Catalog Interaction Error"
_MALFORMED: Final[str] = "The connection handle is malformed."


def _fail(message: str) -> Err[QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _adapter_name(kind: AdapterKind) -> str:
    if isinstance(kind, AdapterKind_DuckDb):
        return "DuckDb"
    if isinstance(kind, AdapterKind_Sqlite):
        return "Sqlite"
    if isinstance(kind, AdapterKind_Postgres):
        return "Postgres"
    if isinstance(kind, AdapterKind_MySql):
        return "MySql"
    if isinstance(kind, AdapterKind_Odbc):
        return "Odbc"
    if isinstance(kind, AdapterKind_BigQuery):
        return "BigQuery"
    if isinstance(kind, AdapterKind_Trino):
        return "Trino"
    if isinstance(kind, AdapterKind_Databricks):
        return "Databricks"
    if isinstance(kind, AdapterKind_Adbc):
        return "Adbc"
    if isinstance(kind, AdapterKind_Cassandra):
        return "Cassandra"
    if isinstance(kind, AdapterKind_NebulaGraph):
        return "NebulaGraph"
    return "Chdb"


def _first(row: object) -> Option[str]:
    if row is None:
        return Nothing()
    if isinstance(row, (str, bytes)):
        return Some(value=str(row))
    if isinstance(row, Iterable):
        for value in cast(Iterable[object], row):
            return Some(value=str(value))
        return Nothing()
    return Some(value=str(row))


def _deactivate(active: list[object], current: object) -> None:
    for index in range(len(active) - 1, -1, -1):
        if active[index] is current:
            del active[index]
            break


def _dbapi(driver: Any, sql: str, active: list[object], encode: bool, buffered: bool) -> Option[str]:
    cursor: Any = driver.cursor(buffered=True) if buffered else driver.cursor()
    current: object = cast(object, cursor)
    active.append(current)
    try:
        cursor.execute(sql.encode("utf-8") if encode else sql)
        if cast(object, cursor.description) is None:
            return Nothing()
        return _first(cast(object, cursor.fetchone()))
    finally:
        _deactivate(active, current)
        cursor.close()


def _duckdb(driver: Any, sql: str, active: list[object]) -> Option[str]:
    current: object = cast(object, driver)
    active.append(current)
    try:
        relation: Any = driver.sql(sql)
        if relation is None:
            return Nothing()
        return _first(cast(object, relation.fetchone()))
    finally:
        _deactivate(active, current)


def _bigquery(driver: Any, sql: str, active: list[object]) -> Option[str]:
    job: Any = driver.query(sql)
    current: object = cast(object, job)
    active.append(current)
    try:
        rows: object = cast(object, job.result())
        if rows is None:
            return Nothing()
        if not isinstance(rows, Iterable):
            raise TypeError("BigQuery returned a non-iterable result.")
        for row in cast(Iterable[object], rows):
            record: Any = row
            return _first(cast(object, record.values()))
        return Nothing()
    finally:
        _deactivate(active, current)


def _cassandra(driver: Any, sql: str, active: list[object], mode: str | None, modes: list[str]) -> Option[str]:
    current: object = cast(object, driver)
    active.append(current)
    try:
        if mode is None:
            result: Any = driver.execute(sql)
        else:
            sdk: Any = cassandra.query
            statement: object = cast(object, sdk.SimpleStatement(sql, consistency_level=modes.index(mode)))
            result = driver.execute(statement)
        return _first(cast(object, result.one()))
    finally:
        _deactivate(active, current)


def _nebula(driver: Any, sql: str, active: list[object]) -> Option[str]:
    current: object = cast(object, driver)
    active.append(current)
    try:
        result: Any = driver.execute(sql)
        if not bool(cast(object, result.is_succeeded())):
            raise RuntimeError(str(cast(object, result.error_msg())))
        if bool(cast(object, result.is_empty())):
            return Nothing()
        count: object = cast(object, result.row_size())
        if not isinstance(count, int):
            raise TypeError("NebulaGraph returned a non-integer row count.")
        if count == 0:
            return Nothing()
        raw_values: object = cast(object, result.row_values(0))
        if not isinstance(raw_values, list):
            raise TypeError("NebulaGraph returned an invalid row.")
        values = cast(list[object], raw_values)
        if not values:
            return Nothing()
        cell: Any = values[0]
        return Some(value=str(cast(object, cell.cast())))
    finally:
        _deactivate(active, current)


def run_scalar_query(connection: Connection, sql: str) -> Result[Option[str], QueryError]:
    handle = connection.session
    if handle.tag != "harlequin.session":
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    if len(payload) != 9 or any(key not in payload for key in (
        "adapter", "driver", "request", "cleanup", "lock", "closed",
        "transaction_mode", "modes", "active",
    )):
        return _fail(_MALFORMED)
    lock_raw = payload["lock"]
    if not isinstance(lock_raw, type(threading.RLock())):
        return _fail(_MALFORMED)
    with cast(contextlib.AbstractContextManager[object], lock_raw):
        request = payload["request"]
        modes_raw = payload["modes"]
        active_raw = payload["active"]
        mode_raw = payload["transaction_mode"]
        if (
            payload["adapter"] != _adapter_name(connection.adapter)
            or not isinstance(request, ConnectionRequest)
            or request.adapter != connection.adapter
            or request.read_only != connection.read_only
            or payload["driver"] is None
            or not isinstance(payload["cleanup"], contextlib.ExitStack)
            or not isinstance(payload["closed"], bool)
            or not isinstance(modes_raw, list)
            or not isinstance(active_raw, list)
        ):
            return _fail(_MALFORMED)
        modes_objects = cast(list[object], modes_raw)
        if not all(isinstance(label, str) for label in modes_objects):
            return _fail(_MALFORMED)
        modes = cast(list[str], modes_raw)
        if mode_raw is not None and not isinstance(mode_raw, str):
            return _fail(_MALFORMED)
        mode: str | None = mode_raw
        if mode is not None and mode not in modes:
            return _fail(_MALFORMED)
        if payload["closed"] is True:
            return _fail("The connection is closed.")
        active = cast(list[object], active_raw)
        driver: Any = payload["driver"]
        adapter = payload["adapter"]
        try:
            try:
                _cott_fixture_database("read")
            except CottContractViolation as violation:
                if violation.message != "fixture adapters are inactive":
                    cause = violation.__cause__
                    return _fail(str(cause) if isinstance(cause, OSError) else violation.message)
            if adapter == "DuckDb":
                value = _duckdb(driver, sql, active)
            elif adapter == "Sqlite":
                if mode == "Manual":
                    if not bool(cast(object, driver.in_transaction)):
                        driver.execute("begin;")
                    if sql.strip().rstrip(";").strip().casefold() == "begin":
                        return Ok(value=Nothing())
                value = _dbapi(driver, sql, active, False, False)
            elif adapter == "Postgres":
                if mode == "Manual" and cast(object, driver.info.transaction_status) == psycopg.pq.TransactionStatus.IDLE:
                    driver.execute("BEGIN")
                value = _dbapi(driver, sql, active, True, False)
            elif adapter == "MySql":
                value = _dbapi(driver, sql, active, False, True)
            elif adapter == "BigQuery":
                value = _bigquery(driver, sql, active)
            elif adapter == "Cassandra":
                value = _cassandra(driver, sql, active, mode, modes)
            elif adapter == "NebulaGraph":
                value = _nebula(driver, sql, active)
            else:
                value = _dbapi(driver, sql, active, False, False)
        except Exception as error:
            return _fail(str(error))
    return Ok(value=value)
