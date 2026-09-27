from pathlib import Path

from cott_runtime import CottContractViolation, CottList, Err, Ok, Option, Result, Some, _cott_fixture_read
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
    try:
        try:
            text = _cott_fixture_read(path).decode()
        except CottContractViolation as error:
            if error.message != "fixture adapters are inactive":
                if isinstance(error.__cause__, FileNotFoundError):
                    return Err(error=ConnectError_ServiceMissing(service=service, file=file))
                if isinstance(error.__cause__, OSError):
                    return Err(error=ConnectError_Failed(message=str(error.__cause__)))
                raise
            if not path.exists():
                return Err(error=ConnectError_ServiceMissing(service=service, file=file))
            with path.open(newline="") as handle:
                text = handle.read()
    except FileNotFoundError:
        return Err(error=ConnectError_ServiceMissing(service=service, file=file))
    except (OSError, UnicodeDecodeError) as error:
        return Err(error=ConnectError_Failed(message=str(error)))
    parsed = parse_pg_service(text, service)
    if isinstance(parsed, Ok):
        if isinstance(parsed.value, Some):
            return parsed
        return Err(error=ConnectError_ServiceMissing(service=service, file=file))
    return parsed
