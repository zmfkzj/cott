import contextlib
from typing import Any, Final, cast

from cott_runtime import UNIT, Err, Ok, Result, Unit

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not roll back the transaction."
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"


def _fail(message: str) -> Result[Unit, QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def rollback_transaction(connection: Connection) -> Result[Unit, QueryError]:
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
    mode = payload["transaction_mode"]
    if (
        not isinstance(adapter, str)
        or not isinstance(payload["request"], ConnectionRequest)
        or not isinstance(payload["cleanup"], contextlib.ExitStack)
        or not isinstance(lock, contextlib.AbstractContextManager)
        or not isinstance(payload["closed"], bool)
        or not (mode is None or isinstance(mode, str))
        or not isinstance(payload["modes"], list)
        or not isinstance(payload["active"], list)
    ):
        return _fail("The connection handle is malformed.")
    guard = cast(contextlib.AbstractContextManager[object], lock)
    with guard:
        if payload["closed"] is True:
            return _fail("The connection is closed.")
        if adapter not in ("Sqlite", "Postgres") or payload["transaction_mode"] != "Manual":
            return Ok(value=UNIT)
        driver: Any = payload["driver"]
        try:
            driver.rollback()
        except Exception as error:
            return _fail(str(error))
    return Ok(value=UNIT)
