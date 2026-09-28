import contextlib
import sqlite3
from typing import Final, cast

import psycopg
from cott_runtime import CottContractViolation, UNIT, Err, Ok, Result, Unit, _cott_fixture_database

from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, QueryError, QueryError_Failed

_TITLE: Final[str] = "Harlequin could not commit the transaction."
_TAG: Final[str] = "harlequin.session"
_MALFORMED: Final[str] = "The session handle is malformed."


def _fail(message: str) -> Err[QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _adapter_name(adapter: AdapterKind) -> str:
    if isinstance(adapter, AdapterKind_DuckDb):
        return "DuckDb"
    if isinstance(adapter, AdapterKind_Sqlite):
        return "Sqlite"
    if isinstance(adapter, AdapterKind_Postgres):
        return "Postgres"
    if isinstance(adapter, AdapterKind_MySql):
        return "MySql"
    if isinstance(adapter, AdapterKind_Odbc):
        return "Odbc"
    if isinstance(adapter, AdapterKind_BigQuery):
        return "BigQuery"
    if isinstance(adapter, AdapterKind_Trino):
        return "Trino"
    if isinstance(adapter, AdapterKind_Databricks):
        return "Databricks"
    if isinstance(adapter, AdapterKind_Adbc):
        return "Adbc"
    if isinstance(adapter, AdapterKind_Cassandra):
        return "Cassandra"
    if isinstance(adapter, AdapterKind_NebulaGraph):
        return "NebulaGraph"
    return "Chdb"


def commit_transaction(connection: Connection) -> Result[Unit, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail(_MALFORMED)
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    if payload.keys() != {"adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active"}:
        return _fail(_MALFORMED)

    adapter = payload["adapter"]
    request = payload["request"]
    cleanup = payload["cleanup"]
    lock = payload["lock"]
    modes = payload["modes"]
    active = payload["active"]
    if (not isinstance(adapter, str) or adapter != _adapter_name(connection.adapter)
            or not isinstance(request, ConnectionRequest)
            or request.adapter != connection.adapter or request.read_only != connection.read_only
            or not isinstance(cleanup, contextlib.ExitStack)
            or not isinstance(lock, contextlib.AbstractContextManager)
            or not isinstance(modes, list) or not isinstance(active, list)):
        return _fail(_MALFORMED)
    labels = cast(list[object], modes)
    if any(not isinstance(label, str) for label in labels):
        return _fail(_MALFORMED)
    guard = cast(contextlib.AbstractContextManager[object], lock)

    try:
        with guard:
            closed = payload["closed"]
            mode = payload["transaction_mode"]
            driver = payload["driver"]
            if not isinstance(closed, bool) or (mode is not None and not isinstance(mode, str)):
                return _fail(_MALFORMED)
            if closed:
                return _fail("The connection is closed.")
            if (mode is None) != (len(labels) == 0) or (mode is not None and mode not in labels):
                return _fail(_MALFORMED)
            if adapter == "Sqlite":
                if not isinstance(driver, sqlite3.Connection) or labels != ["Auto", "Manual"]:
                    return _fail(_MALFORMED)
            elif adapter == "Postgres":
                if not isinstance(driver, psycopg.Connection) or labels != ["Auto", "Manual"]:
                    return _fail(_MALFORMED)
            elif driver is None:
                return _fail(_MALFORMED)

            try:
                _cott_fixture_database("commit")
            except CottContractViolation as violation:
                if violation.message != "fixture adapters are inactive":
                    cause = violation.__cause__
                    return _fail(str(cause) if isinstance(cause, OSError) else violation.message)

            if mode == "Manual" and adapter == "Sqlite":
                sqlite_connection = cast(sqlite3.Connection, driver)
                sqlite_connection.commit()
            elif mode == "Manual" and adapter == "Postgres":
                postgres_connection = cast(psycopg.Connection[tuple[object, ...]], driver)
                postgres_connection.commit()
            return Ok(value=UNIT)
    except Exception as error:
        return _fail(str(error))
