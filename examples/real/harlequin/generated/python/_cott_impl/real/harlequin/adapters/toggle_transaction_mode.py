import contextlib
from typing import Any, Final, cast

import cassandra
from cott_runtime import Err, Ok, Result, Some

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed, TransactionMode

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not change the transaction mode."
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"
_CASS_LEVELS: Final[str] = "ANY,ONE,TWO,THREE,QUORUM,ALL,LOCAL_QUORUM,EACH_QUORUM,SERIAL,LOCAL_SERIAL,LOCAL_ONE"


def _fail(message: str) -> Result[Connection, QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _apply(adapter: str, driver: Any, label: str) -> None:
    if adapter in ("Sqlite", "Postgres"):
        if label == "Auto":
            driver.commit()
            driver.autocommit = True
        else:
            driver.autocommit = False
    elif adapter == "Cassandra":
        matches = [name for name in _CASS_LEVELS.split(",") if name[:10] == label]
        if not matches:
            raise ValueError(f"Unknown consistency level: {label}")
        levels: Any = cassandra.ConsistencyLevel
        driver.default_consistency_level = levels.name_to_value[matches[0]]


def toggle_transaction_mode(connection: Connection) -> Result[Connection, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail("The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return _fail("The connection handle is malformed.")
    adapter = payload["adapter"]
    lock = payload["lock"]
    modes_raw = payload["modes"]
    if (
        not isinstance(adapter, str)
        or not isinstance(lock, contextlib.AbstractContextManager)
        or not isinstance(modes_raw, list)
        or not isinstance(payload["request"], ConnectionRequest)
        or not isinstance(payload["cleanup"], contextlib.ExitStack)
        or not isinstance(payload["active"], list)
        or payload["driver"] is None
    ):
        return _fail("The connection handle is malformed.")
    modes: list[str] = []
    for item in cast(list[object], modes_raw):
        if not isinstance(item, str):
            return _fail("The connection handle is malformed.")
        modes.append(item)
    guard = cast(contextlib.AbstractContextManager[object], lock)
    with guard:
        closed = payload["closed"]
        current = payload["transaction_mode"]
        if not isinstance(closed, bool) or not (current is None or isinstance(current, str)):
            return _fail("The connection handle is malformed.")
        if closed:
            return _fail("The connection is closed.")
        if not modes:
            return Ok(value=connection)
        index = modes.index(current) if current in modes else -1
        label = modes[(index + 1) % len(modes)]
        driver: Any = payload["driver"]
        try:
            _apply(adapter, driver, label)
        except Exception as error:
            return _fail(str(error))
        payload["transaction_mode"] = label
        manual = adapter in ("Sqlite", "Postgres") and label == "Manual"
        return Ok(
            value=Connection(
                adapter=connection.adapter,
                connection_id=connection.connection_id,
                init_message=connection.init_message,
                driver_details=connection.driver_details,
                read_only=connection.read_only,
                transaction_mode=Some(value=TransactionMode(label=label, can_commit=manual, can_rollback=manual)),
                session=connection.session,
            )
        )
    return _fail("The connection handle is malformed.")
