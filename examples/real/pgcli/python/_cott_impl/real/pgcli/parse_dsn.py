from collections.abc import Mapping
from typing import Final

from cott_runtime import Err, Ok, Result
from psycopg import Error as _PsycopgError
from psycopg.conninfo import conninfo_to_dict

from real.pgcli_types import ConnectionError, ConnectionError_InvalidDsn, ConnectionInputs

_INVALID_DSN_MSG: Final[str] = "invalid DSN"


def _field(params: Mapping[str, str | int | None], key: str) -> str:
    raw = params.get(key)
    if raw is None:
        return ""
    if isinstance(raw, int):
        return str(raw)
    return raw


def _invalid() -> Result[ConnectionInputs, ConnectionError]:
    return Err(error=ConnectionError_InvalidDsn(value=_INVALID_DSN_MSG))


def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]:
    try:
        params = conninfo_to_dict(value)
    except (_PsycopgError, ValueError):
        return _invalid()
    database = _field(params, "dbname")
    if database == "":
        return _invalid()
    return Ok(
        value=ConnectionInputs(
            host=_field(params, "host"),
            port=_field(params, "port"),
            user=_field(params, "user"),
            password=_field(params, "password"),
            database=database,
        )
    )
