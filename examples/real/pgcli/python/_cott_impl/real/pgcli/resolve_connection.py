from cott_runtime import Err, Ok, Result
from real.pgcli_types import ConnectionError, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionInputs, ConnectionSettings, EnvironmentInputs


def _pick(primary: str, fallback: str) -> str:
    if primary != "":
        return primary
    return fallback


def _port_valid(port: str) -> bool:
    if port == "":
        return True
    if not (port.isascii() and port.isdigit()):
        return False
    return 1 <= int(port) <= 65535


def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]:
    database = _pick(inputs.database, environment.database)
    if database == "":
        return Err(error=ConnectionError_MissingDatabase())
    port = _pick(inputs.port, environment.port)
    if not _port_valid(port):
        return Err(error=ConnectionError_InvalidPort(value=port))
    return Ok(value=ConnectionSettings(host=_pick(inputs.host, environment.host), port=port, user=_pick(inputs.user, environment.user), password=_pick(inputs.password, environment.password), database=database))
