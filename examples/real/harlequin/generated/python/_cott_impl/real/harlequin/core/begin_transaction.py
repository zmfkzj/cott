import contextlib
import sqlite3
import threading
from typing import Final, cast

import adbc_driver_manager.dbapi
import duckdb
import psycopg
import pymysql.connections
import pyodbc
from psycopg.pq import ExecStatus, TransactionStatus

from cott_runtime import Err, Ok, Opaque, Result
from real.harlequin.core_types import AdapterKind_Adbc, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, Connection, ConnectionError, ConnectionError_Failed, Transaction

_SESSION_TAG: Final[str] = "harlequin.session"
_TRANSACTION_TAG: Final[str] = "harlequin.transaction"
_PAYLOAD_KEYS: Final[str] = "id,adapter,endpoint,read_only,driver,cleanup,lock,closed,transaction"
_INVALID: Final[str] = "invalid or closed connection"


def _fail(message: str) -> Result[Transaction, ConnectionError]:
    return Err(error=ConnectionError_Failed(message=message))


def _payload(connection: Connection) -> dict[str, object] | None:
    session = connection.session
    if session.tag != _SESSION_TAG:
        return None
    raw = session.unwrap()
    if not isinstance(raw, dict):
        return None
    payload = cast(dict[str, object], raw)
    keys: set[str] = set(_PAYLOAD_KEYS.split(","))
    if set(payload.keys()) != keys:
        return None
    if type(payload["lock"]) is not type(threading.Lock()):
        return None
    return payload


def _metadata_matches(connection: Connection, payload: dict[str, object]) -> bool:
    return (
        isinstance(payload["cleanup"], contextlib.ExitStack)
        and isinstance(payload["closed"], bool)
        and isinstance(payload["id"], str)
        and payload["id"] == connection.id
        and payload["adapter"] == connection.adapter
        and isinstance(payload["endpoint"], str)
        and payload["endpoint"] == connection.endpoint
        and isinstance(payload["read_only"], bool)
        and payload["read_only"] == connection.read_only
    )


def _start(connection: Connection, driver: object) -> bool:
    """Start a real transaction on the retained driver; False means driver/adapter mismatch."""
    adapter = connection.adapter
    if isinstance(adapter, AdapterKind_Sqlite):
        if not isinstance(driver, sqlite3.Connection):
            return False
        if driver.in_transaction:
            raise RuntimeError("transaction already open")
        driver.execute("BEGIN")
        if not driver.in_transaction:
            raise RuntimeError("transaction not started")
        return True
    if isinstance(adapter, AdapterKind_DuckDb):
        if not isinstance(driver, duckdb.DuckDBPyConnection):
            return False
        driver.execute("BEGIN")
        return True
    if isinstance(adapter, AdapterKind_PostgreSql):
        if not isinstance(driver, psycopg.Connection):
            return False
        pg = cast(psycopg.Connection[tuple[object, ...]], driver)
        if pg.info.transaction_status != TransactionStatus.IDLE:
            raise RuntimeError("connection not idle")
        # Low-level exec avoids psycopg's implicit BEGIN in manual-commit mode.
        result = pg.pgconn.exec_(b"BEGIN READ ONLY" if connection.read_only else b"BEGIN")
        if result.status != ExecStatus.COMMAND_OK or pg.info.transaction_status != TransactionStatus.INTRANS:
            raise RuntimeError("transaction not started")
        return True
    if isinstance(adapter, AdapterKind_MySql):
        if not isinstance(driver, pymysql.connections.Connection):
            return False
        driver.begin()
        return True
    if isinstance(adapter, AdapterKind_Odbc):
        if not isinstance(driver, pyodbc.Connection):
            return False
        if driver.autocommit:
            raise RuntimeError("not in manual-commit mode")
        return True
    if isinstance(adapter, AdapterKind_Adbc):
        # connect enforced manual-commit; the physical transaction starts lazily.
        return isinstance(driver, adbc_driver_manager.dbapi.Connection)
    return False


def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]:
    payload = _payload(connection)
    if payload is None:
        return _fail(_INVALID)
    lock = cast(threading.Lock, payload["lock"])
    with lock:
        if payload["closed"] is not False or not _metadata_matches(connection, payload):
            return _fail(_INVALID)
        if not isinstance(connection.adapter, (AdapterKind_Sqlite, AdapterKind_DuckDb, AdapterKind_PostgreSql, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_Adbc)):
            return _fail("adapter does not support transactions")
        if payload["transaction"] is not None:
            return _fail("a transaction is already active")
        try:
            started = _start(connection, payload["driver"])
        except Exception:
            return _fail("failed to begin transaction")
        if not started:
            return _fail(_INVALID)
        lease = object()
        payload["transaction"] = lease
        return Ok(value=Transaction(connection=connection, lease=Opaque(tag=_TRANSACTION_TAG, value=lease), active=True))
