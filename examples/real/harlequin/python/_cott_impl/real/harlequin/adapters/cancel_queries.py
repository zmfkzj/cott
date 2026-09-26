from typing import Any, Final, cast

import mysql.connector
from cott_runtime import UNIT, Err, Ok, Result, Unit

from real.harlequin.adapters_types import AdapterSetting, Connection, ConnectionRequest, QueryError, QueryError_Failed, SettingValue_Flag, SettingValue_Text

_TITLE: Final[str] = "Harlequin could not cancel your queries."
_TAG: Final[str] = "harlequin.session"
_MALFORMED: Final[str] = "The connection handle is malformed."


def _fail(message: str) -> Result[Unit, QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _display_name(adapter: str) -> str:
    names: dict[str, str] = {
        "Odbc": "ODBC",
        "BigQuery": "BigQuery",
        "Trino": "Trino",
        "Adbc": "ADBC",
        "Cassandra": "Cassandra",
        "NebulaGraph": "NebulaGraph",
    }
    return names.get(adapter, adapter)


def _setting_text(setting: AdapterSetting) -> str | None:
    value = setting.value
    if isinstance(value, SettingValue_Text):
        return value.value
    return None


def _setting_flag(setting: AdapterSetting) -> bool | None:
    value = setting.value
    if isinstance(value, SettingValue_Flag):
        return value.value
    return None


def _mysql_kwargs(request: ConnectionRequest) -> dict[str, object]:
    kwargs: dict[str, object] = {"autocommit": True}
    text_keys: dict[str, str] = {
        "host": "host",
        "unix_socket": "unix_socket",
        "database": "database",
        "user": "user",
        "password": "password",
        "password1": "password",
        "password2": "password2",
        "password3": "password3",
        "ssl_ca": "ssl_ca",
        "ssl_cert": "ssl_cert",
        "ssl_key": "ssl_key",
        "openid_token_file": "openid_token_file",
    }
    int_keys: dict[str, str] = {"port": "port", "connection_timeout": "connection_timeout"}
    flag_keys: dict[str, str] = {"ssl_disabled": "ssl_disabled", "enable_cleartext_plugin": "allow_local_infile"}
    for setting in request.settings:
        text = _setting_text(setting)
        flag = _setting_flag(setting)
        if setting.name in text_keys and text is not None:
            kwargs[text_keys[setting.name]] = text
        elif setting.name in int_keys and text is not None:
            kwargs[int_keys[setting.name]] = int(text)
        elif setting.name in flag_keys and flag is not None:
            kwargs[flag_keys[setting.name]] = flag
    return kwargs


def _cancel_mysql(driver: Any, request: ConnectionRequest) -> None:
    raw_id = cast(object, driver.connection_id)
    if not isinstance(raw_id, int):
        raise ValueError("The MySQL connection id is unavailable.")
    busy_id = raw_id
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


def cancel_queries(connection: Connection) -> Result[Unit, QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail(_MALFORMED)
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    expected = {"adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active"}
    if set(payload.keys()) != expected:
        return _fail(_MALFORMED)
    adapter = payload["adapter"]
    closed = payload["closed"]
    active_raw = payload["active"]
    request = payload["request"]
    if not isinstance(adapter, str) or not isinstance(closed, bool) or not isinstance(active_raw, list) or not isinstance(request, ConnectionRequest):
        return _fail(_MALFORMED)
    if closed:
        return _fail("The connection is closed.")
    active = list(cast(list[object], active_raw))
    driver: Any = payload["driver"]
    try:
        if adapter in ("DuckDb", "Sqlite"):
            driver.interrupt()
        elif adapter == "Postgres":
            driver.cancel_safe()
        elif adapter == "MySql":
            _cancel_mysql(driver, request)
        elif adapter == "Databricks":
            for item in active:
                cursor: Any = item
                cursor.cancel()
        elif adapter == "Chdb":
            if active:
                for item in active:
                    stmt: Any = item
                    stmt.adbc_cancel()
            else:
                driver.adbc_cancel()
        else:
            return _fail(f"The {_display_name(adapter)} adapter does not support canceling queries.")
    except Exception as error:
        return _fail(str(error))
    return Ok(value=UNIT)
