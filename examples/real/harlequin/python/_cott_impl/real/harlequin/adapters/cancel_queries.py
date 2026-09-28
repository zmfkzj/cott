import contextlib
import threading
from typing import Any, Final, cast

import mysql.connector
from cott_runtime import CottContractViolation, UNIT, Err, Ok, Result, Unit, _cott_fixture_database
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
    SettingValue,
    SettingValue_Flag,
    SettingValue_Text,
)

_TITLE: Final[str] = "Harlequin could not cancel your queries."
_TAG: Final[str] = "harlequin.session"
_MALFORMED: Final[str] = "The connection handle is malformed."


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


def _display_name(adapter: str) -> str:
    if adapter == "Odbc":
        return "ODBC"
    if adapter == "Adbc":
        return "ADBC"
    return adapter


def _session(connection: Connection) -> dict[str, object] | None:
    handle = connection.session
    if handle.tag != _TAG:
        return None
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return None
    payload = cast(dict[str, object], raw)
    if payload.keys() != {"adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active"}:
        return None
    adapter = payload["adapter"]
    request = payload["request"]
    mode = payload["transaction_mode"]
    modes = payload["modes"]
    active = payload["active"]
    if (not isinstance(adapter, str) or adapter != _adapter_name(connection.adapter)
            or not isinstance(request, ConnectionRequest)
            or request.adapter != connection.adapter or request.read_only != connection.read_only
            or payload["driver"] is None or not isinstance(payload["cleanup"], contextlib.ExitStack)
            or not isinstance(payload["lock"], type(threading.RLock()))
            or not isinstance(payload["closed"], bool)
            or not isinstance(modes, list) or not isinstance(active, list)
            or (mode is not None and not isinstance(mode, str))):
        return None
    labels = cast(list[object], modes)
    if any(not isinstance(label, str) for label in labels):
        return None
    if mode is not None and mode not in labels:
        return None
    return payload


def _text(settings: dict[str, SettingValue], name: str) -> str | None:
    value = settings.get(name)
    if isinstance(value, SettingValue_Text) and value.value != "":
        return value.value
    return None


def _mysql_kwargs(request: ConnectionRequest) -> dict[str, object]:
    settings: dict[str, SettingValue] = {}
    for setting in request.settings:
        settings[setting.name] = setting.value
    kwargs: dict[str, object] = {"autocommit": True}
    for name in ("host", "unix_socket", "database", "user", "password2", "password3", "ssl_ca", "ssl_cert", "ssl_key", "openid_token_file"):
        value = _text(settings, name)
        if value is not None:
            kwargs[name] = value
    password = _text(settings, "password1")
    if password is not None:
        kwargs["password"] = password
    for name in ("port", "connection_timeout"):
        value = _text(settings, name)
        if value is not None:
            kwargs[name] = int(value)
    ssl_disabled = settings.get("ssl_disabled")
    if isinstance(ssl_disabled, SettingValue_Flag):
        kwargs["ssl_disabled"] = ssl_disabled.value
    cleartext = settings.get("enable_cleartext_plugin")
    if isinstance(cleartext, SettingValue_Flag):
        kwargs["allow_local_infile"] = cleartext.value
    return kwargs


def _cancel_mysql(driver: Any, request: ConnectionRequest) -> None:
    busy_id: object = cast(object, driver.connection_id)
    if isinstance(busy_id, bool) or not isinstance(busy_id, int):
        raise ValueError("The MySQL connection id is unavailable.")
    sdk: Any = mysql.connector
    killer: Any = sdk.connect(**_mysql_kwargs(request))
    try:
        cursor: Any = killer.cursor()
        try:
            cursor.execute(f"KILL QUERY {busy_id}")
        finally:
            cursor.close()
    finally:
        killer.close()


def _cancel_chdb(driver: Any, active: list[object]) -> None:
    cursors = list(active)
    if not cursors:
        driver.adbc_cancel()
        return
    for item in cursors:
        cursor: Any = item
        try:
            cursor.adbc_cancel()
        except Exception:
            driver.adbc_cancel()
            return


def cancel_queries(connection: Connection) -> Result[Unit, QueryError]:
    payload = _session(connection)
    if payload is None:
        return _fail(_MALFORMED)
    if payload["closed"] is True:
        return _fail("The connection is closed.")
    adapter = cast(str, payload["adapter"])
    driver: Any = payload["driver"]
    try:
        try:
            _cott_fixture_database("cancel")
        except CottContractViolation as violation:
            if violation.message != "fixture adapters are inactive":
                cause = violation.__cause__
                return _fail(str(cause) if isinstance(cause, OSError) else violation.message)
        if adapter == "DuckDb" or adapter == "Sqlite":
            driver.interrupt()
        elif adapter == "Postgres":
            driver.cancel_safe()
        elif adapter == "MySql":
            _cancel_mysql(driver, cast(ConnectionRequest, payload["request"]))
        elif adapter == "Databricks":
            for item in list(cast(list[object], payload["active"])):
                cursor: Any = item
                cursor.cancel()
        elif adapter == "Chdb":
            _cancel_chdb(driver, cast(list[object], payload["active"]))
        else:
            return _fail(f"The {_display_name(adapter)} adapter does not support canceling queries.")
    except KeyboardInterrupt:
        return _fail("interrupted")
    except Exception as error:
        return _fail(str(error))
    return Ok(value=UNIT)
