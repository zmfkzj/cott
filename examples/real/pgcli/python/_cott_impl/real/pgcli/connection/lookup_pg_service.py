from pathlib import Path

from cott_runtime import CottList, Err, Ok, Option, Result, Some

from real.pgcli.connection import parse_pg_service
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectError_ServiceMissing, ConnectionParam


def lookup_pg_service(service: str, service_file: str, sysconfdir: str, home: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]:
    if service_file != "":
        file = service_file
    elif sysconfdir != "":
        file = sysconfdir + "/.pg_service.conf"
    else:
        file = home + "/.pg_service.conf"
    path = Path(file)
    if not path.exists():
        return _missing(service, file)
    try:
        with path.open(newline="") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        return _failed(str(error))
    parsed = parse_pg_service(text, service)
    if isinstance(parsed, Ok):
        found = parsed.value
        if isinstance(found, Some):
            return Ok(value=found)
        return _missing(service, file)
    return parsed


def _missing(service: str, file: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]:
    return Err(error=ConnectError_ServiceMissing(service=service, file=file))


def _failed(message: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]:
    return Err(error=ConnectError_Failed(message=message))
