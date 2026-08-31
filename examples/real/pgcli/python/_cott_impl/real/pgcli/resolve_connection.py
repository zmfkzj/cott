from cott_runtime import Err, Ok, Result
from real.pgcli_types import (
    ConnectionError,
    ConnectionError_InvalidPort,
    ConnectionError_MissingDatabase,
    ConnectionInputs,
    ConnectionSettings,
    EnvironmentInputs,
)


def _prefer(value: str, fallback: str) -> str:
    if value != "":
        return value
    return fallback


def _valid_port(value: str) -> bool:
    if value == "":
        return True
    port = 0
    for character in value:
        if character < "0" or character > "9":
            return False
        port = port * 10 + ord(character) - ord("0")
        if port > 65535:
            return False
    return port > 0


def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    host = _prefer(inputs.host, environment.host)
    port = _prefer(inputs.port, environment.port)
    user = _prefer(inputs.user, environment.user)
    password = _prefer(inputs.password, environment.password)
    database = _prefer(inputs.database, environment.database)
    if database == "":
        return Err(error=ConnectionError_MissingDatabase())
    if not _valid_port(port):
        return Err(error=ConnectionError_InvalidPort(value=port))
    return Ok(value=ConnectionSettings(host=host, port=port, user=user, password=password, database=database))
