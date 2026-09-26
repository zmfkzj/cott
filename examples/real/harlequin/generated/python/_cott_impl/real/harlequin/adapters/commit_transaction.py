import contextlib
import sqlite3
from typing import Final, cast

import psycopg
from cott_runtime import UNIT, Err, Ok, Result, Unit

from real.harlequin.adapters_types import Connection, QueryError, QueryError_Failed

_TITLE: Final[str] = "Harlequin could not commit the transaction."
_TAG: Final[str] = "harlequin.session"
_MALFORMED: Final[str] = "The session handle is malformed."


def _fail(message: str) -> Result[Unit, QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _commit_driver(adapter: str, driver: object) -> Result[Unit, QueryError]:
    if adapter == "Sqlite":
        if not isinstance(driver, sqlite3.Connection):
            return _fail(_MALFORMED)
        try:
            driver.commit()
        except sqlite3.Error as error:
            return _fail(str(error))
        return Ok(value=UNIT)
    if adapter == "Postgres":
        if not isinstance(driver, psycopg.Connection):
            return _fail(_MALFORMED)
        pg = cast(psycopg.Connection[tuple[object, ...]], driver)
        try:
            pg.commit()
        except psycopg.Error as error:
            return _fail(str(error))
        return Ok(value=UNIT)
    return Ok(value=UNIT)


def commit_transaction(connection: Connection) -> Result[Unit, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail(_MALFORMED)
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    adapter = payload.get("adapter")
    lock = payload.get("lock")
    if not isinstance(adapter, str) or not isinstance(lock, contextlib.AbstractContextManager):
        return _fail(_MALFORMED)
    guard = cast(contextlib.AbstractContextManager[object], lock)
    try:
        with guard:
            closed = payload.get("closed")
            if not isinstance(closed, bool):
                return _fail(_MALFORMED)
            if closed:
                return _fail("The connection is closed.")
            mode = payload.get("transaction_mode")
            if adapter not in ("Sqlite", "Postgres") or mode != "Manual":
                return Ok(value=UNIT)
            return _commit_driver(adapter, payload.get("driver"))
    except Exception as error:
        return _fail(str(error))
