import contextlib
import threading
from typing import Any, Final, cast

from cott_runtime import CottContractViolation, UNIT, Err, Ok, Result, Unit, _cott_fixture_database
from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, QueryError, QueryError_Failed

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not roll back the transaction."


def _fail(message: str) -> Err[QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _adapter_matches(name: str, kind: AdapterKind) -> bool:
    if isinstance(kind, AdapterKind_DuckDb):
        return name == "DuckDb"
    if isinstance(kind, AdapterKind_Sqlite):
        return name == "Sqlite"
    if isinstance(kind, AdapterKind_Postgres):
        return name == "Postgres"
    if isinstance(kind, AdapterKind_MySql):
        return name == "MySql"
    if isinstance(kind, AdapterKind_Odbc):
        return name == "Odbc"
    if isinstance(kind, AdapterKind_BigQuery):
        return name == "BigQuery"
    if isinstance(kind, AdapterKind_Trino):
        return name == "Trino"
    if isinstance(kind, AdapterKind_Databricks):
        return name == "Databricks"
    if isinstance(kind, AdapterKind_Adbc):
        return name == "Adbc"
    if isinstance(kind, AdapterKind_Cassandra):
        return name == "Cassandra"
    if isinstance(kind, AdapterKind_NebulaGraph):
        return name == "NebulaGraph"
    return name == "Chdb"


def rollback_transaction(connection: Connection) -> Result[Unit, QueryError]:
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
    adapter = payload["adapter"]
    request = payload["request"]
    lock = payload["lock"]
    modes = payload["modes"]
    active = payload["active"]
    if (
        not isinstance(adapter, str)
        or not isinstance(request, ConnectionRequest)
        or not isinstance(payload["cleanup"], contextlib.ExitStack)
        or not isinstance(lock, type(threading.RLock()))
        or not isinstance(payload["closed"], bool)
        or not isinstance(modes, list)
        or not isinstance(active, list)
        or payload["driver"] is None
    ):
        return _fail("The connection handle is malformed.")
    labels = cast(list[object], modes)
    if not _adapter_matches(adapter, connection.adapter) or request.adapter != connection.adapter or any(not isinstance(label, str) for label in labels):
        return _fail("The connection handle is malformed.")
    with lock:
        mode = payload["transaction_mode"]
        if not (mode is None or isinstance(mode, str)) or (mode is not None and mode not in labels):
            return _fail("The connection handle is malformed.")
        if payload["closed"] is True:
            return _fail("The connection is closed.")
        try:
            try:
                _cott_fixture_database("rollback")
            except CottContractViolation as violation:
                if violation.message != "fixture adapters are inactive":
                    cause = violation.__cause__
                    return _fail(str(cause) if isinstance(cause, OSError) else violation.message)
            if adapter in ("Sqlite", "Postgres") and mode == "Manual":
                driver: Any = payload["driver"]
                driver.rollback()
        except (Exception, KeyboardInterrupt) as error:
            return _fail(str(error))
    return Ok(value=UNIT)
