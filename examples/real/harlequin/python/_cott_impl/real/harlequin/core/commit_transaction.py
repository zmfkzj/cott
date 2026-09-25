import contextlib
import sqlite3
import threading
from typing import Final, cast

import adbc_driver_manager.dbapi
import duckdb
import psycopg
import pymysql.connections
import pyodbc
from cott_runtime import Err, Ok, Result

from real.harlequin.core_types import AdapterKind, AdapterKind_Adbc, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, Connection, ConnectionError, ConnectionError_Failed, ConnectionError_LeaseRejected, Transaction, TransactionStatus_Active, TransactionStatus_Committed

_SESSION_TAG: Final[str] = "harlequin.session"
_LEASE_TAG: Final[str] = "harlequin.transaction"
_COMMIT_FAILED_MESSAGE: Final[str] = "transaction commit failed; session closed"


def _driver_supported(adapter: AdapterKind, driver: object) -> bool:
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
    if isinstance(adapter, AdapterKind_Adbc):
        return isinstance(driver, adbc_driver_manager.dbapi.Connection)
    return False


def _driver_finish(driver: object, commit: bool) -> None:
    if not isinstance(driver, (sqlite3.Connection, duckdb.DuckDBPyConnection, psycopg.Connection, pymysql.connections.Connection, pyodbc.Connection, adbc_driver_manager.dbapi.Connection)):
        raise TypeError("unsupported transactional driver")
    if commit:
        driver.commit()
    else:
        driver.rollback()


def _attempt_rollback(driver: object) -> bool:
    try:
        _driver_finish(driver, False)
    except Exception:
        return False
    return True


def _attempt_cleanup(cleanup: contextlib.ExitStack[bool | None]) -> bool:
    try:
        cleanup.close()
    except Exception:
        return False
    return True


def _session_state(connection: Connection) -> dict[str, object] | None:
    handle = connection.session
    if handle.tag != _SESSION_TAG:
        return None
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return None
    state = cast(dict[str, object], raw)
    expected: set[str] = {"id", "adapter", "endpoint", "read_only", "driver", "cleanup", "lock", "closed", "transaction"}
    if set(state.keys()) != expected:
        return None
    if state["id"] != connection.id or state["adapter"] != connection.adapter or state["endpoint"] != connection.endpoint or state["read_only"] != connection.read_only:
        return None
    if not isinstance(state["cleanup"], contextlib.ExitStack) or not isinstance(state["lock"], threading.Lock) or not isinstance(state["closed"], bool):
        return None
    return state


def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    if not isinstance(transaction.status, TransactionStatus_Active) or transaction.lease.tag != _LEASE_TAG:
        return Err(error=ConnectionError_LeaseRejected())
    lease = transaction.lease.unwrap()
    connection = transaction.connection
    state = _session_state(connection)
    if state is None:
        return Err(error=ConnectionError_LeaseRejected())
    lock = state["lock"]
    raw_cleanup = state["cleanup"]
    if not isinstance(lock, threading.Lock) or not isinstance(raw_cleanup, contextlib.ExitStack):
        return Err(error=ConnectionError_LeaseRejected())
    cleanup = cast(contextlib.ExitStack[bool | None], raw_cleanup)
    with lock:
        driver = state["driver"]
        current = state["transaction"]
        if state["closed"] is not False or current is None or current is not lease or not _driver_supported(connection.adapter, driver):
            return Err(error=ConnectionError_LeaseRejected())
        try:
            _driver_finish(driver, True)
        except Exception:
            state["transaction"] = None
            state["closed"] = True
            _attempt_rollback(driver)
            _attempt_cleanup(cleanup)
            return Err(error=ConnectionError_Failed(message=_COMMIT_FAILED_MESSAGE))
        state["transaction"] = None
    return Ok(value=Transaction(connection=connection, lease=transaction.lease, status=TransactionStatus_Committed()))
