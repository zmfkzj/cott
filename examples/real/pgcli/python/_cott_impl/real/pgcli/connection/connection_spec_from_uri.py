import psycopg.conninfo
from cott_runtime import CottList, Err, Ok, Result

from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam, ConnectionSpec


def connection_spec_from_uri(uri: str) -> Result[ConnectionSpec, ConnectError]:
    try:
        params = psycopg.conninfo.conninfo_to_dict(uri)
    except Exception as error:
        failure: ConnectError = ConnectError_Failed(message=str(error))
        return Err(error=failure)
    database = ""
    host = ""
    user = ""
    port = ""
    password = ""
    extra: list[ConnectionParam] = []
    for name, raw in params.items():
        value = "" if raw is None else str(raw)
        if name == "dbname":
            database = value
        elif name == "host":
            host = value
        elif name == "user":
            user = value
        elif name == "port":
            port = value
        elif name == "password":
            password = value
        else:
            extra.append(ConnectionParam(name=name, value=value))
    return Ok(value=ConnectionSpec(database=database, host=host, user=user, port=port, password=password, dsn="", extra=CottList(values=extra)))
