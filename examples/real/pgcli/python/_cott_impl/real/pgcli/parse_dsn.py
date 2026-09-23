from collections.abc import Mapping

from cott_runtime import Err, Ok, Result
from psycopg import Error as _PsycopgError
from psycopg.conninfo import conninfo_to_dict

from real.pgcli_types import ConnectionError, ConnectionError_InvalidDsn, ConnectionInputs


def _field(params: Mapping[str, object], key: str) -> str:
    raw = params.get(key)
    if raw is None:
        return ""
    return str(raw)


def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]:
    try:
        params = conninfo_to_dict(value)
    except _PsycopgError:
        return Err(error=ConnectionError_InvalidDsn(value="invalid connection string"))
    database = _field(params, "dbname")
    if database == "":
        return Err(error=ConnectionError_InvalidDsn(value="connection string has no database"))
    return Ok(value=ConnectionInputs(host=_field(params, "host"), port=_field(params, "port"), user=_field(params, "user"), password=_field(params, "password"), database=database))
