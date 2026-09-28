import contextlib
import threading
from typing import Final, cast

from cott_runtime import UNIT, CottContractViolation, Err, Ok, Result, Unit, _cott_fixture_database
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

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not close the connection."
_MALFORMED: Final[str] = "The connection handle is malformed."
_INACTIVE: Final[str] = "fixture adapters are inactive"


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


def _fail(message: str) -> Err[QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def close_connection(connection: Connection) -> Result[Unit, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
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
        return _fail(_MALFORMED)
    cleanup = payload["cleanup"]
    lock = payload["lock"]
    request = payload["request"]
    modes = payload["modes"]
    active = payload["active"]
    transaction_mode = payload["transaction_mode"]
    if (
        not isinstance(cleanup, contextlib.ExitStack)
        or not isinstance(lock, type(threading.RLock()))
        or not isinstance(request, ConnectionRequest)
        or not isinstance(payload["adapter"], str)
        or payload["driver"] is None
        or not isinstance(payload["closed"], bool)
        or not isinstance(modes, list)
        or not isinstance(active, list)
        or not (transaction_mode is None or isinstance(transaction_mode, str))
    ):
        return _fail(_MALFORMED)
    if (
        not all(isinstance(mode, str) for mode in cast(list[object], modes))
        or payload["adapter"] != _adapter_name(connection.adapter)
        or request.adapter != connection.adapter
        or request.read_only != connection.read_only
    ):
        return _fail(_MALFORMED)

    try:
        with cast(contextlib.AbstractContextManager[object], lock):
            if payload["closed"]:
                return Ok(value=UNIT)
            payload["closed"] = True
            try:
                try:
                    _cott_fixture_database("close")
                except CottContractViolation as violation:
                    if violation.message != _INACTIVE:
                        cause = violation.__cause__
                        return _fail(str(cause) if isinstance(cause, OSError) else violation.message)
            finally:
                try:
                    cleanup.close()
                finally:
                    cast(list[object], active).clear()
    except Exception as error:
        return _fail(str(error))
    return Ok(value=UNIT)
