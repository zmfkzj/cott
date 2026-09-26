import contextlib
import json
from typing import Final, cast

import duckdb

from real.harlequin.adapters_types import Connection

_TAG: Final[str] = "harlequin.session"
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"


def _is_valid_duckdb(driver: duckdb.DuckDBPyConnection, text: str) -> bool:
    escaped = text.replace("'", "''")
    row = driver.execute(f"select json_serialize_sql('{escaped}')").fetchone()
    if row is None:
        return False
    raw_json = cast(object, row[0])
    if not isinstance(raw_json, str):
        return False
    parsed = cast(object, json.loads(raw_json))
    if not isinstance(parsed, dict):
        return False
    result = cast(dict[str, object], parsed)
    if result.get("error") is True and result.get("error_type") == "parser":
        return False
    return True


def validate_sql(connection: Connection, text: str) -> bool:
    handle = connection.session
    if handle.tag != _TAG:
        return False
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return False
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return False
    adapter = payload["adapter"]
    lock = payload["lock"]
    if not isinstance(adapter, str) or not isinstance(lock, contextlib.AbstractContextManager):
        return False
    guard = cast(contextlib.AbstractContextManager[object], lock)
    try:
        with guard:
            if payload["closed"] is not False:
                return False
            if adapter != "DuckDb":
                return True
            driver = payload["driver"]
            if not isinstance(driver, duckdb.DuckDBPyConnection):
                return False
            return _is_valid_duckdb(driver, text)
    except Exception:
        return False
