import contextlib
from typing import Final, cast

from cott_runtime import UNIT, Err, Ok, Result, Unit

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not close the connection."
_MALFORMED: Final[str] = "The connection handle is malformed."
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"


def _fail(message: str) -> Result[Unit, QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def close_connection(connection: Connection) -> Result[Unit, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return _fail(_MALFORMED)
    cleanup = payload["cleanup"]
    lock = payload["lock"]
    closed = payload["closed"]
    active = payload["active"]
    modes = payload["modes"]
    if (
        not isinstance(cleanup, contextlib.ExitStack)
        or not isinstance(lock, contextlib.AbstractContextManager)
        or not isinstance(closed, bool)
        or not isinstance(active, list)
        or not isinstance(modes, list)
        or not isinstance(payload["adapter"], str)
        or not isinstance(payload["request"], ConnectionRequest)
        or not (payload["transaction_mode"] is None or isinstance(payload["transaction_mode"], str))
    ):
        return _fail(_MALFORMED)
    if not all(isinstance(mode, str) for mode in cast(list[object], modes)):
        return _fail(_MALFORMED)
    stack = cast(contextlib.ExitStack[bool | None], cleanup)
    guard = cast(contextlib.AbstractContextManager[object], lock)
    with guard:
        if payload["closed"] is True:
            return Ok(value=UNIT)
        payload["closed"] = True
        cast(list[object], active).clear()
        try:
            stack.close()
        except Exception as error:
            return _fail(str(error))
    return Ok(value=UNIT)
