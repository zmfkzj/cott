from typing import Final

from cott_runtime import CottList, Err, Nothing, Ok, Result
from real.pgcli_types import (
    CliCommand,
    CliCommand_Help,
    CliCommand_Session,
    ClientError,
    ClientError_InvalidArguments,
    ConnectionInputs,
    ConnectionRequest,
    EnvironmentInputs,
    SessionMode_ExecuteOnce,
    SessionMode_Interactive,
    TlsMode_Default,
    TlsSettings,
)

_HOST: Final[str] = "host"
_PORT: Final[str] = "port"
_USER: Final[str] = "user"
_DATABASE: Final[str] = "database"
_COMMAND: Final[str] = "command"


def _invalid(message: str) -> Result[CliCommand, ClientError]:
    return Err(error=ClientError_InvalidArguments(message=message))


def _field_for(option: str) -> str:
    if option in ("-h", "--host"):
        return _HOST
    if option in ("-p", "--port"):
        return _PORT
    if option in ("-U", "--username"):
        return _USER
    if option in ("-d", "--dbname"):
        return _DATABASE
    if option in ("-c", "--command"):
        return _COMMAND
    return ""


def parse_arguments(arguments: CottList[str], environment: EnvironmentInputs) -> Result[CliCommand, ClientError]:
    for item in arguments:
        if item == "--help":
            return Ok(value=CliCommand_Help())

    host: str = ""
    port: str = ""
    user: str = ""
    database: str = ""
    command: str = ""
    has_command: bool = False
    dsn: str = ""
    has_dsn: bool = False

    index = 0
    total = len(arguments)
    while index < total:
        argument = arguments[index]
        index += 1

        if not argument.startswith("-"):
            if has_dsn:
                return _invalid("extra positional argument")
            dsn = argument
            has_dsn = True
            continue

        if argument.startswith("--") and "=" in argument:
            name, _, inline = argument.partition("=")
            field = _field_for(name)
            if field == "":
                return _invalid(f"unknown option: {name}")
            if field == _HOST:
                host = inline
            elif field == _PORT:
                port = inline
            elif field == _USER:
                user = inline
            elif field == _DATABASE:
                database = inline
            elif field == _COMMAND:
                command = inline
                has_command = True
            continue

        field = _field_for(argument)
        if field == "":
            offending = argument.partition("=")[0]
            if not offending.startswith("--") and len(offending) > 2:
                offending = offending[:2]
            return _invalid(f"unknown option: {offending}")
        
        if index >= total:
            return _invalid(f"option requires a value: {argument}")

        val = arguments[index]
        index += 1
        if field == _HOST:
            host = val
        elif field == _PORT:
            port = val
        elif field == _USER:
            user = val
        elif field == _DATABASE:
            database = val
        elif field == _COMMAND:
            command = val
            has_command = True

    inputs = ConnectionInputs(
        host=host,
        port=port,
        user=user,
        password="",
        database=database,
    )
    connection = ConnectionRequest(
        dsn=dsn,
        profile="",
        inputs=inputs,
        environment=environment,
        tls=TlsSettings(mode=TlsMode_Default(), root_certificate=Nothing(), client=Nothing()),
        ssh=Nothing(),
    )
    if has_command:
        return Ok(value=CliCommand_Session(connection=connection, mode=SessionMode_ExecuteOnce(), initial_sql=command))
    return Ok(value=CliCommand_Session(connection=connection, mode=SessionMode_Interactive(), initial_sql=""))
