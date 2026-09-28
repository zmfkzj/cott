import contextlib
import json
import threading
from typing import Final, cast

import duckdb

from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest

_TAG: Final[str] = "harlequin.session"


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


def _session_lock(connection: Connection, payload: dict[str, object]) -> contextlib.AbstractContextManager[object] | None:
    if len(payload) != 9 or any(key not in payload for key in ("adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active")):
        return None
    request = payload["request"]
    lock = payload["lock"]
    modes = payload["modes"]
    transaction_mode = payload["transaction_mode"]
    if (not isinstance(payload["adapter"], str)
            or payload["adapter"] != _adapter_name(connection.adapter)
            or not isinstance(request, ConnectionRequest)
            or request.adapter != connection.adapter
            or payload["driver"] is None
            or not isinstance(payload["cleanup"], contextlib.ExitStack)
            or not isinstance(lock, type(threading.RLock()))
            or not isinstance(payload["closed"], bool)
            or not isinstance(modes, list)
            or not isinstance(payload["active"], list)
            or (transaction_mode is not None and not isinstance(transaction_mode, str))):
        return None
    if not all(isinstance(mode, str) for mode in cast(list[object], modes)):
        return None
    return cast(contextlib.AbstractContextManager[object], lock)


def _is_valid_duckdb(driver: duckdb.DuckDBPyConnection, text: str) -> bool:
    escaped = text.replace("'", "''")
    try:
        row = driver.execute(f"select json_serialize_sql('{escaped}')").fetchone()
    except duckdb.NotImplementedException:
        return True
    if row is None:
        return False
    raw_json = cast(object, row[0])
    if not isinstance(raw_json, str):
        return False
    parsed = cast(object, json.loads(raw_json))
    if not isinstance(parsed, dict):
        return False
    result = cast(dict[str, object], parsed)
    return not (result.get("error") is True and result.get("error_type") == "parser")


def validate_sql(connection: Connection, text: str) -> bool:
    try:
        handle = connection.session
        if handle.tag != _TAG:
            return False
        raw = handle.unwrap()
        if not isinstance(raw, dict):
            return False
        payload = cast(dict[str, object], raw)
        lock = _session_lock(connection, payload)
        if lock is None:
            return False
        with lock:
            if payload["closed"] is not False:
                return False
            if not isinstance(connection.adapter, AdapterKind_DuckDb):
                return True
            driver = payload["driver"]
            if not isinstance(driver, duckdb.DuckDBPyConnection):
                return False
            return _is_valid_duckdb(driver, text)
    except Exception:
        return False
