import contextlib
import sqlite3
import threading
from typing import Final, cast

import adbc_driver_manager.dbapi
import duckdb
import psycopg
import pymysql.connections
import pyodbc
import trino.dbapi
from cassandra.cluster import Session as CassandraSession
from databricks.sql.client import Connection as DatabricksConnection
from google.cloud import bigquery
from nebula3.gclient.net import Session as NebulaSession

from cott_runtime import UNIT, Err, Ok, Result, Unit
from real.harlequin.core_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionError, ConnectionError_Failed

_SESSION_TAG: Final[str] = "harlequin.session"
_INVALID_MESSAGE: Final[str] = "invalid session handle"
_CLOSE_MESSAGE: Final[str] = "disconnect failed"
_KEYS: Final[str] = "id,adapter,endpoint,read_only,driver,cleanup,lock,closed,transaction"


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
    else:
        return isinstance(driver, NebulaSession)


def _payload(connection: Connection) -> dict[str, object] | None:
    try:
        if connection.session.tag != _SESSION_TAG:
            return None
        raw = connection.session.unwrap()
    except AttributeError:
        return None
    if not isinstance(raw, dict):
        return None
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return None
    if not isinstance(payload["id"], str) or not isinstance(payload["endpoint"], str) or not isinstance(payload["read_only"], bool):
        return None
    if payload["id"] != connection.id or payload["adapter"] != connection.adapter or payload["endpoint"] != connection.endpoint or payload["read_only"] != connection.read_only:
        return None
    if not isinstance(payload["lock"], type(threading.Lock())) or not isinstance(payload["cleanup"], contextlib.ExitStack) or not isinstance(payload["closed"], bool):
        return None
    if not _driver_matches(connection.adapter, payload["driver"]):
        return None
    return payload


def _rollback(driver: object) -> None:
    if isinstance(driver, sqlite3.Connection):
        if driver.in_transaction:
            driver.rollback()
    elif isinstance(driver, duckdb.DuckDBPyConnection):
        try:
            driver.rollback()
        except duckdb.TransactionException:
            return
    elif isinstance(driver, (psycopg.Connection, pymysql.connections.Connection, pyodbc.Connection, adbc_driver_manager.dbapi.Connection)):
        driver.rollback()


def disconnect(connection: Connection) -> Result[Unit, ConnectionError]:
    payload = _payload(connection)
    if payload is None:
        return Err(error=ConnectionError_Failed(message=_INVALID_MESSAGE))
    lock = payload["lock"]
    cleanup = payload["cleanup"]
    if not isinstance(lock, type(threading.Lock())) or not isinstance(cleanup, contextlib.ExitStack):
        return Err(error=ConnectionError_Failed(message=_INVALID_MESSAGE))
    failed = False
    with lock:
        if payload["closed"] is True:
            return Ok(value=UNIT)
        payload["transaction"] = None
        payload["closed"] = True
        try:
            _rollback(payload["driver"])
        except Exception:
            failed = True
        try:
            cleanup.close()
        except Exception:
            failed = True
    if failed:
        return Err(error=ConnectionError_Failed(message=_CLOSE_MESSAGE))
    return Ok(value=UNIT)
