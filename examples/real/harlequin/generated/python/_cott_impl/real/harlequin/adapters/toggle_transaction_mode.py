import contextlib
import threading
from typing import Any, Final, cast

import cassandra
from cott_runtime import CottContractViolation, Err, Ok, Result, Some, _cott_fixture_database

from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, QueryError, QueryError_Failed, TransactionMode

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not change the transaction mode."


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


def _apply(adapter: str, driver: Any, label: str) -> None:
    if adapter == "Sqlite" or adapter == "Postgres":
        if label == "Auto":
            driver.commit()
            driver.autocommit = True
        else:
            driver.autocommit = False
        return
    if label == "LOCAL_QUOR":
        name = "LOCAL_QUORUM"
    elif label == "EACH_QUORU":
        name = "EACH_QUORUM"
    elif label == "LOCAL_SERI":
        name = "LOCAL_SERIAL"
    else:
        name = label
    sdk: Any = cassandra
    levels_raw: object = cast(object, sdk.ConsistencyLevel.name_to_value)
    if not isinstance(levels_raw, dict):
        raise TypeError("Cassandra consistency levels are malformed.")
    levels = cast(dict[str, object], levels_raw)
    level = levels[name]
    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError(f"Invalid consistency level: {name}")
    driver.default_consistency_level = level


def toggle_transaction_mode(connection: Connection) -> Result[Connection, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail("The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if (
        len(payload) != 9
        or "adapter" not in payload
        or "driver" not in payload
        or "request" not in payload
        or "cleanup" not in payload
        or "lock" not in payload
        or "closed" not in payload
        or "transaction_mode" not in payload
        or "modes" not in payload
        or "active" not in payload
    ):
        return _fail("The connection handle is malformed.")
    lock: Any = payload["lock"]
    if not isinstance(lock, type(threading.RLock())):
        return _fail("The connection handle is malformed.")
    try:
        with lock:
            adapter = payload["adapter"]
            request = payload["request"]
            modes_raw = payload["modes"]
            current = payload["transaction_mode"]
            closed = payload["closed"]
            if (
                not isinstance(adapter, str)
                or not isinstance(request, ConnectionRequest)
                or not isinstance(payload["cleanup"], contextlib.ExitStack)
                or not isinstance(modes_raw, list)
                or not isinstance(payload["active"], list)
                or payload["driver"] is None
                or not isinstance(closed, bool)
                or not (current is None or isinstance(current, str))
            ):
                return _fail("The connection handle is malformed.")
            if adapter != _adapter_name(connection.adapter) or request.adapter != connection.adapter or request.read_only != connection.read_only:
                return _fail("The connection handle is malformed.")
            for item in cast(list[object], modes_raw):
                if not isinstance(item, str):
                    return _fail("The connection handle is malformed.")
            modes = cast(list[str], modes_raw)
            if adapter == "Sqlite" or adapter == "Postgres":
                if modes != ["Auto", "Manual"]:
                    return _fail("The connection handle is malformed.")
            elif adapter == "Cassandra":
                if modes != ["ANY", "ONE", "TWO", "THREE", "QUORUM", "ALL", "LOCAL_QUOR", "EACH_QUORU", "SERIAL", "LOCAL_SERI", "LOCAL_ONE"]:
                    return _fail("The connection handle is malformed.")
            elif modes:
                return _fail("The connection handle is malformed.")
            index = 0
            if modes:
                if current is None:
                    return _fail("The connection handle is malformed.")
                try:
                    index = modes.index(current)
                except ValueError:
                    return _fail("The connection handle is malformed.")
            elif current is not None:
                return _fail("The connection handle is malformed.")
            if closed:
                return _fail("The connection is closed.")
            try:
                _cott_fixture_database("write")
            except CottContractViolation as violation:
                if violation.message != "fixture adapters are inactive":
                    cause = violation.__cause__
                    return _fail(str(cause) if isinstance(cause, OSError) else violation.message)
            if not modes:
                return Ok(value=connection)
            label = modes[(index + 1) % len(modes)]
            driver: Any = payload["driver"]
            _apply(adapter, driver, label)
            payload["transaction_mode"] = label
            manual = (adapter == "Sqlite" or adapter == "Postgres") and label == "Manual"
            return Ok(value=Connection(
                adapter=connection.adapter,
                connection_id=connection.connection_id,
                init_message=connection.init_message,
                driver_details=connection.driver_details,
                read_only=connection.read_only,
                transaction_mode=Some(value=TransactionMode(label=label, can_commit=manual, can_rollback=manual)),
                session=handle,
            ))
    except KeyboardInterrupt as error:
        return _fail(str(error) or "interrupted")
    except Exception as error:
        return _fail(str(error))
