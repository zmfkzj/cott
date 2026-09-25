from collections.abc import Mapping
from typing import Final

import psycopg
from psycopg.conninfo import conninfo_to_dict

from cott_runtime import Err, Nothing, Ok, Option, Result, Some
from real.pgcli_types import ConnectionError, ConnectionError_InvalidDsn, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionError_SshInvalid, ConnectionInputs, ConnectionPlan, ConnectionProfile, ConnectionRequest, ConnectionSettings, SshSettings, TlsMode_Default, TlsSettings

_MAX_PORT: Final[int] = 65535


def _first(a: str, b: str, c: str, d: str) -> str:
    for value in (a, b, c, d):
        if value != "":
            return value
    return ""


def _dsn_value(params: Mapping[str, str | int | None], key: str) -> str:
    value = params.get(key)
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return value


def _ssh_error(hop: SshSettings) -> str:
    if hop.host == "" or hop.host.startswith("-"):
        return "invalid ssh host"
    if hop.user == "":
        return "ssh user is required"
    if hop.port == 0:
        return "invalid ssh port"
    return ""


def _port_valid(port: str) -> bool:
    if not (port.isascii() and port.isdigit()):
        return False
    return 1 <= int(port) <= _MAX_PORT


def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]:
    prof_inputs = ConnectionInputs(host="", port="", user="", password="", database="")
    prof_dsn = ""
    prof_tls: TlsSettings | None = None
    prof_ssh: Option[SshSettings] = Nothing()
    if isinstance(profile, Some):
        prof = profile.value
        prof_inputs = prof.inputs
        prof_dsn = prof.dsn
        prof_tls = prof.tls
        prof_ssh = prof.ssh

    dsn = request.dsn if request.dsn != "" else prof_dsn

    tls = request.tls
    if isinstance(tls.mode, TlsMode_Default) and prof_tls is not None:
        tls = prof_tls

    ssh: Option[SshSettings] = request.ssh if isinstance(request.ssh, Some) else prof_ssh

    if isinstance(ssh, Some):
        message = _ssh_error(ssh.value)
        if message != "":
            return Err(error=ConnectionError_SshInvalid(message=message))

    params: Mapping[str, str | int | None] = {}
    if dsn != "":
        try:
            params = conninfo_to_dict(dsn)
        except psycopg.Error:
            return Err(error=ConnectionError_InvalidDsn(value="unparseable connection string"))

    req = request.inputs
    env = request.environment
    host = _first(req.host, _dsn_value(params, "host"), prof_inputs.host, env.host)
    port = _first(req.port, _dsn_value(params, "port"), prof_inputs.port, env.port)
    user = _first(req.user, _dsn_value(params, "user"), prof_inputs.user, env.user)
    password = _first(req.password, _dsn_value(params, "password"), prof_inputs.password, env.password)
    database = _first(req.database, _dsn_value(params, "dbname"), prof_inputs.database, env.database)

    if port != "" and not _port_valid(port):
        return Err(error=ConnectionError_InvalidPort(value=port))
    if database == "":
        return Err(error=ConnectionError_MissingDatabase())

    settings = ConnectionSettings(host=host, port=port, user=user, password=password, database=database)
    return Ok(value=ConnectionPlan(settings=settings, dsn=dsn, tls=tls, ssh=ssh))
