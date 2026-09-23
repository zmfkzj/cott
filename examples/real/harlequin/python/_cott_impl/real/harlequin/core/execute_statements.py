import contextlib
import datetime
import decimal
import math
import sqlite3
import threading
import uuid
from collections.abc import Iterable, Sequence
from typing import Final, cast

import adbc_driver_manager.dbapi
import cassandra.cluster
import duckdb
import psycopg
import psycopg.errors
import pymysql.connections
import pymysql.cursors
import pyodbc
import trino.dbapi
from cassandra.cluster import Session as CassandraSession
from databricks.sql.client import Connection as DatabricksConnection
from google.cloud import bigquery
from google.cloud.bigquery.table import Row as BigQueryRow
from nebula3.gclient.net.Session import Session as NebulaSession

from cott_runtime import CottList, Err, Ok, Result, U32
from real.harlequin.core import split_statements
from real.harlequin.core_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Cell, Cell_Blob, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, Connection, QueryBatch, QueryResult, SqlClientError, SqlClientError_Cancelled, SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded, SqlClientError_UnsupportedValue, TypedRow

_SESSION_TAG: Final[str] = "harlequin.session"
_INVALID_SESSION: Final[str] = "session is closed or invalid"
_EXEC_FAILED: Final[str] = "statement execution failed"
_COMMIT_FAILED: Final[str] = "commit failed"
_TX_CONTROL: Final[str] = "transaction control statements must use the transaction lease API"
_NEBULA_FAILED: Final[str] = "NebulaGraph statement failed"
_I64_MAX: Final[int] = 9223372036854775807


def _in_i64(value: int) -> bool:
    return -_I64_MAX - 1 <= value <= _I64_MAX


def _driver_matches(adapter: AdapterKind, driver: object) -> bool:
    if isinstance(adapter, AdapterKind_Sqlite):
        return isinstance(driver, sqlite3.Connection)
    if isinstance(adapter, AdapterKind_DuckDb):
        return isinstance(driver, duckdb.DuckDBPyConnection)
    if isinstance(adapter, AdapterKind_PostgreSql):
        return isinstance(driver, psycopg.Connection)
    if isinstance(adapter, AdapterKind_MySql):
        return isinstance(driver, pymysql.connections.Connection)
    if isinstance(adapter, AdapterKind_Odbc):
        return isinstance(driver, pyodbc.Connection)
    if isinstance(adapter, AdapterKind_BigQuery):
        return isinstance(driver, bigquery.Client)
    if isinstance(adapter, AdapterKind_Trino):
        return isinstance(driver, trino.dbapi.Connection)
    if isinstance(adapter, AdapterKind_Databricks):
        return isinstance(driver, DatabricksConnection)
    if isinstance(adapter, AdapterKind_Adbc):
        return isinstance(driver, adbc_driver_manager.dbapi.Connection)
    if isinstance(adapter, AdapterKind_Cassandra):
        return isinstance(driver, CassandraSession)
    return isinstance(driver, NebulaSession)


def _payload(connection: Connection) -> dict[str, object] | None:
    session = connection.session
    if session.tag != _SESSION_TAG:
        return None
    raw = session.unwrap()
    if not isinstance(raw, dict):
        return None
    value = cast(dict[str, object], raw)
    if set(value.keys()) != {"id", "adapter", "endpoint", "read_only", "driver", "cleanup", "lock", "closed", "transaction"}:
        return None
    if value["id"] != connection.id or value["adapter"] != connection.adapter or value["endpoint"] != connection.endpoint or value["read_only"] is not connection.read_only:
        return None
    if not isinstance(value["cleanup"], contextlib.ExitStack) or not isinstance(value["lock"], threading.Lock) or not isinstance(value["closed"], bool):
        return None
    if not _driver_matches(connection.adapter, value["driver"]):
        return None
    return value


def _words(statement: str) -> list[str]:
    words: list[str] = []
    i = 0
    n = len(statement)
    while i < n:
        ch = statement[i]
        if ch == "-" and statement.startswith("--", i):
            end = statement.find("\n", i)
            i = n if end < 0 else end + 1
        elif ch == "/" and statement.startswith("/*", i):
            end = statement.find("*/", i + 2)
            i = n if end < 0 else end + 2
        elif ch in "'\"`":
            j = i + 1
            while j < n:
                if statement[j] == ch:
                    if j + 1 < n and statement[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
        elif ch.isalpha() or ch == "_":
            j = i
            while j < n and (statement[j].isalnum() or statement[j] == "_"):
                j += 1
            words.append(statement[i:j].upper())
            i = j
        else:
            i += 1
    return words


def _is_transaction_control(words: list[str]) -> bool:
    return len(words) > 0 and words[0] in ("BEGIN", "START", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE", "END", "ABORT")


def _is_write_intent(words: list[str]) -> bool:
    if len(words) == 0:
        return True
    if words[0] not in ("SELECT", "WITH", "VALUES", "TABLE", "SHOW", "DESCRIBE", "DESC", "EXPLAIN", "MATCH", "GO", "FETCH", "LOOKUP", "FIND", "GET", "YIELD"):
        return True
    for word in words:
        if word in ("INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE", "CREATE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE", "COPY", "CALL", "INTO", "ANALYZE", "VACUUM", "SET", "LOCK", "ATTACH", "DETACH", "PRAGMA"):
            return True
    return False


def _unsupported_name(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return "list"
    if isinstance(value, dict):
        return "map"
    if isinstance(value, (set, frozenset)):
        return "set"
    return "opaque"


def _cell(value: object) -> Cell | SqlClientError:
    if value is None:
        return Cell_Null()
    if isinstance(value, bool):
        return Cell_Integer(value=1 if value else 0)
    if isinstance(value, int):
        if _in_i64(value):
            return Cell_Integer(value=value)
        return SqlClientError_UnsupportedValue(type_name="int")
    if isinstance(value, float):
        if math.isfinite(value):
            return Cell_Real(value=value)
        return SqlClientError_UnsupportedValue(type_name="float")
    if isinstance(value, str):
        return Cell_Text(value=value)
    if isinstance(value, (bytes, bytearray)):
        return Cell_Blob(value=bytes(value))
    if isinstance(value, memoryview):
        return Cell_Blob(value=bytes(cast(memoryview[int], value)))
    if isinstance(value, (decimal.Decimal, datetime.date, datetime.time, datetime.timedelta, uuid.UUID)):
        return Cell_Text(value=str(value))
    return SqlClientError_UnsupportedValue(type_name=_unsupported_name(value))


def _query_result(columns: list[str], rows: list[tuple[object, ...]], affected: int, maximum_rows: int) -> QueryResult | SqlClientError:
    if len(rows) > maximum_rows:
        return SqlClientError_ResultLimitExceeded(limit=maximum_rows)
    typed: list[TypedRow] = []
    for row in rows:
        cells: list[Cell] = []
        for value in row:
            cell = _cell(value)
            if isinstance(cell, SqlClientError):
                return cell
            cells.append(cell)
        typed.append(TypedRow(values=CottList(values=cells)))
    return QueryResult(columns=CottList(values=columns), rows=CottList(values=typed), affected_rows=affected if _in_i64(affected) else -1)


def _normalize(statement: str, description: object, fetched: object, rowcount: object, maximum_rows: int) -> QueryResult | SqlClientError:
    columns: list[str] = []
    if description is not None:
        if not isinstance(description, (list, tuple)):
            return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
        for column in cast(Sequence[object], description):
            if not isinstance(column, (list, tuple)) or len(cast(Sequence[object], column)) == 0:
                return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
            columns.append(str(cast(Sequence[object], column)[0]))
    rows: list[tuple[object, ...]] = []
    if fetched is not None:
        if not isinstance(fetched, (list, tuple)):
            return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
        for row in cast(Sequence[object], fetched):
            if isinstance(row, (list, tuple)):
                rows.append(tuple(cast(Sequence[object], row)))
            elif isinstance(row, pyodbc.Row):
                rows.append(tuple(cast(Iterable[object], row)))
            else:
                return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
    affected = rowcount if isinstance(rowcount, int) and not isinstance(rowcount, bool) else -1
    return _query_result(columns, rows, affected, maximum_rows)


def _run_sqlite(driver: sqlite3.Connection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = driver.cursor()
    try:
        cur.execute(statement)
        description = cast(object, cur.description)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1)) if description is not None else None
        return _normalize(statement, description, fetched, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_duckdb(driver: duckdb.DuckDBPyConnection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    # Execute on the retained connection itself: DuckDBPyConnection.cursor() is a
    # duplicate connection with independent transaction state.
    driver.execute(statement)
    description = cast(object, driver.description)
    fetched = cast(object, driver.fetchmany(maximum_rows + 1)) if description is not None else None
    return _normalize(statement, description, fetched, -1, maximum_rows)


def _run_postgres(driver: psycopg.Connection[tuple[object, ...]], statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = driver.cursor()
    try:
        cur.execute(statement.encode("utf-8"))
        description = cast(object, cur.description)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1)) if description is not None else None
        return _normalize(statement, description, fetched, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_mysql(driver: pymysql.connections.Connection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = cast(pymysql.cursors.Cursor, driver.cursor())
    try:
        cur.execute(statement)
        description = cast(object, cur.description)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1)) if description is not None else None
        return _normalize(statement, description, fetched, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_odbc(driver: pyodbc.Connection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = driver.cursor()
    try:
        cur.execute(statement)
        description = cast(object, cur.description)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1)) if description is not None else None
        return _normalize(statement, description, fetched, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_trino(driver: trino.dbapi.Connection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = driver.cursor()
    try:
        cur.execute(statement)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1))
        description = cast(object, cur.description)
        return _normalize(statement, description, fetched if description is not None else None, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_databricks(driver: DatabricksConnection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = driver.cursor()
    try:
        cur.execute(statement)
        description = cast(object, cur.description)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1)) if description is not None else None
        return _normalize(statement, description, fetched, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_adbc(driver: adbc_driver_manager.dbapi.Connection, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    cur = driver.cursor()
    try:
        cur.execute(statement)
        description = cast(object, cur.description)
        fetched = cast(object, cur.fetchmany(maximum_rows + 1)) if description is not None else None
        return _normalize(statement, description, fetched, cast(object, cur.rowcount), maximum_rows)
    finally:
        cur.close()


def _run_bigquery(client: bigquery.Client, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    job = client.query(statement)
    iterator = job.result(max_results=maximum_rows + 1)
    columns: list[str] = []
    for field in iterator.schema:
        columns.append(str(field.name))
    rows: list[tuple[object, ...]] = []
    for row in cast(Iterable[BigQueryRow], iterator):
        rows.append(tuple(cast(Iterable[object], row.values())))
        if len(rows) > maximum_rows:
            break
    affected = cast(object, job.num_dml_affected_rows)
    return _query_result(columns, rows, affected if isinstance(affected, int) and not isinstance(affected, bool) else -1, maximum_rows)


def _run_cassandra(session: CassandraSession, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    result_set = cast(cassandra.cluster.ResultSet, session.execute(statement))
    columns: list[str] = []
    names = cast(object, result_set.column_names)
    if names is not None:
        if not isinstance(names, (list, tuple)):
            return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
        for name in cast(Sequence[object], names):
            columns.append(str(name))
    rows: list[tuple[object, ...]] = []
    for row in cast(Iterable[tuple[object, ...]], result_set):
        rows.append(tuple(row))
        if len(rows) > maximum_rows:
            break
    return _query_result(columns, rows, -1, maximum_rows)


def _run_nebula(session: NebulaSession, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    result_set = session.execute(statement)
    if not result_set.is_succeeded():
        return SqlClientError_ExecutionFailed(statement=statement, message=_NEBULA_FAILED)
    columns: list[str] = []
    for key in cast(Iterable[object], result_set.keys()):
        columns.append(str(key))
    primitive = cast(object, result_set.as_primitive())
    if not isinstance(primitive, list):
        return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
    rows: list[tuple[object, ...]] = []
    for record in cast(list[object], primitive):
        if not isinstance(record, dict):
            return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
        mapping = cast(dict[str, object], record)
        rows.append(tuple(mapping.get(key) for key in columns))
        if len(rows) > maximum_rows:
            break
    return _query_result(columns, rows, -1, maximum_rows)


def _run(adapter: AdapterKind, driver: object, statement: str, maximum_rows: int) -> QueryResult | SqlClientError:
    if isinstance(adapter, AdapterKind_Sqlite):
        if isinstance(driver, sqlite3.Connection):
            return _run_sqlite(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_DuckDb):
        if isinstance(driver, duckdb.DuckDBPyConnection):
            return _run_duckdb(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_PostgreSql):
        if isinstance(driver, psycopg.Connection):
            return _run_postgres(cast(psycopg.Connection[tuple[object, ...]], driver), statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_MySql):
        if isinstance(driver, pymysql.connections.Connection):
            return _run_mysql(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_Odbc):
        if isinstance(driver, pyodbc.Connection):
            return _run_odbc(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_BigQuery):
        if isinstance(driver, bigquery.Client):
            return _run_bigquery(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_Trino):
        if isinstance(driver, trino.dbapi.Connection):
            return _run_trino(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_Databricks):
        if isinstance(driver, DatabricksConnection):
            return _run_databricks(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_Adbc):
        if isinstance(driver, adbc_driver_manager.dbapi.Connection):
            return _run_adbc(driver, statement, maximum_rows)
    elif isinstance(adapter, AdapterKind_Cassandra):
        if isinstance(driver, CassandraSession):
            return _run_cassandra(driver, statement, maximum_rows)
    else:
        if isinstance(driver, NebulaSession):
            return _run_nebula(driver, statement, maximum_rows)
    return SqlClientError_ExecutionFailed(statement=statement, message=_INVALID_SESSION)


def _is_cancel(error: Exception) -> bool:
    if isinstance(error, (psycopg.errors.QueryCanceled, duckdb.InterruptException)):
        return True
    return isinstance(error, sqlite3.OperationalError) and str(error) == "interrupted"


def _is_transactional(driver: object) -> bool:
    return isinstance(driver, (psycopg.Connection, pymysql.connections.Connection, pyodbc.Connection, adbc_driver_manager.dbapi.Connection))


def _rollback(driver: object) -> None:
    try:
        if isinstance(driver, psycopg.Connection):
            cast(psycopg.Connection[tuple[object, ...]], driver).rollback()
        elif isinstance(driver, pymysql.connections.Connection):
            driver.rollback()
        elif isinstance(driver, pyodbc.Connection):
            driver.rollback()
        elif isinstance(driver, adbc_driver_manager.dbapi.Connection):
            driver.rollback()
    except Exception:
        return


def _commit(driver: object) -> None:
    if isinstance(driver, psycopg.Connection):
        cast(psycopg.Connection[tuple[object, ...]], driver).commit()
    elif isinstance(driver, pymysql.connections.Connection):
        driver.commit()
    elif isinstance(driver, pyodbc.Connection):
        driver.commit()
    elif isinstance(driver, adbc_driver_manager.dbapi.Connection):
        driver.commit()


def _execute_one(adapter: AdapterKind, driver: object, statement: str, maximum_rows: int, autocommit: bool) -> QueryResult | SqlClientError:
    try:
        outcome = _run(adapter, driver, statement, maximum_rows)
    except Exception as exc:
        if autocommit:
            _rollback(driver)
        if _is_cancel(exc):
            return SqlClientError_Cancelled()
        return SqlClientError_ExecutionFailed(statement=statement, message=_EXEC_FAILED)
    if isinstance(outcome, SqlClientError):
        if autocommit:
            _rollback(driver)
        return outcome
    if autocommit:
        try:
            _commit(driver)
        except Exception:
            _rollback(driver)
            return SqlClientError_ExecutionFailed(statement=statement, message=_COMMIT_FAILED)
    return outcome


def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]:
    split = split_statements(sql)
    if isinstance(split, Err):
        return Err(error=split.error)
    statements: list[str] = []
    for statement in split.value:
        statements.append(statement)
    first = statements[0] if statements else ""
    payload = _payload(connection)
    if payload is None:
        return Err(error=SqlClientError_ExecutionFailed(statement=first, message=_INVALID_SESSION))
    lock = payload["lock"]
    if not isinstance(lock, threading.Lock):
        return Err(error=SqlClientError_ExecutionFailed(statement=first, message=_INVALID_SESSION))
    with lock:
        if payload["closed"] is not False:
            return Err(error=SqlClientError_ExecutionFailed(statement=first, message=_INVALID_SESSION))
        for statement in statements:
            words = _words(statement)
            if _is_transaction_control(words):
                return Err(error=SqlClientError_ExecutionFailed(statement=statement, message=_TX_CONTROL))
            if connection.read_only and _is_write_intent(words):
                return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))
        driver = payload["driver"]
        autocommit = _is_transactional(driver) and payload["transaction"] is None
        results: list[QueryResult] = []
        for statement in statements:
            outcome = _execute_one(connection.adapter, driver, statement, maximum_rows, autocommit)
            if isinstance(outcome, SqlClientError):
                return Err(error=outcome)
            results.append(outcome)
    return Ok(value=QueryBatch(statements=CottList(values=statements), results=CottList(values=results)))
