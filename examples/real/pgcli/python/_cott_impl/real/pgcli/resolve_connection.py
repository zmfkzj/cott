from cott_runtime import Err, Ok, Result
from real.pgcli_types import ConnectionError, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionInputs, ConnectionSettings, EnvironmentInputs


def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    host = inputs.host if inputs.host != "" else environment.host
    port = inputs.port if inputs.port != "" else environment.port
    user = inputs.user if inputs.user != "" else environment.user
    password = inputs.password if inputs.password != "" else environment.password
    database = inputs.database if inputs.database != "" else environment.database

    if database == "":
        return Err(error=ConnectionError_MissingDatabase())
    if port != "":
        if not port.isascii() or not port.isdecimal():
            return Err(error=ConnectionError_InvalidPort(value=port))
        normalized_port = port.lstrip("0")
        if normalized_port == "" or len(normalized_port) > 5 or (len(normalized_port) == 5 and normalized_port > "65535"):
            return Err(error=ConnectionError_InvalidPort(value=port))

    return Ok(value=ConnectionSettings(host=host, port=port, user=user, password=password, database=database))
