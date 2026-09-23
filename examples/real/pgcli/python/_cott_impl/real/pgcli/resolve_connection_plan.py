from collections.abc import Mapping
from pathlib import Path
from typing import Final

import psycopg
from psycopg.conninfo import conninfo_to_dict

from cott_runtime import Err, Nothing, Ok, Option, Result, Some
from real.pgcli_types import ConnectionError, ConnectionError_InvalidDsn, ConnectionError_InvalidPort, ConnectionError_MissingDatabase, ConnectionError_SshInvalid, ConnectionError_TlsInvalid, ConnectionPlan, ConnectionProfile, ConnectionRequest, ConnectionSettings, SshSettings, TlsSettings

_TLS_MODES: Final[str] = "disable allow prefer require verify-ca verify-full"
_MAX_PORT: Final[int] = 65535


def _first(a: str, b: str, c: str, d: str) -> str:
    for value in (a, b, c, d):
        if value != "":
            return value
    return ""


def _path_set(p: Path) -> bool:
    return str(p) not in ("", ".")


def _dsn_value(params: Mapping[str, str | int | None], key: str) -> str:
    value = params.get(key)
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return value


def _validate_tls(tls: TlsSettings) -> str:
    if tls.mode != "" and tls.mode not in _TLS_MODES.split(" "):
        return "unsupported sslmode"
    if _path_set(tls.certificate) != _path_set(tls.private_key):
        return "client certificate and private key must be provided together"
    if tls.mode == "verify-ca" or tls.mode == "verify-full":
        if not _path_set(tls.root_certificate):
            return "verified sslmode requires a root certificate"
    return ""


def _validate_ssh(ssh: SshSettings) -> str:
    if ssh.host.strip() == "":
        return "ssh host is required"
    if ssh.user.strip() == "":
        return "ssh user is required"
    if ssh.port < 1 or ssh.port > _MAX_PORT:
        return "ssh port out of range"
    return ""


def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]:
    prof: ConnectionProfile | None = None
    if isinstance(profile, Some):
        prof = profile.value

    dsn = request.dsn if request.dsn != "" else (prof.dsn if prof is not None else "")
    params: Mapping[str, str | int | None] = {}
    if dsn != "":
        try:
            params = conninfo_to_dict(dsn)
        except psycopg.Error:
            return Err(error=ConnectionError_InvalidDsn(value="unparseable connection string"))

    req = request.inputs
    env = request.environment
    p_host = prof.inputs.host if prof is not None else ""
    p_port = prof.inputs.port if prof is not None else ""
    p_user = prof.inputs.user if prof is not None else ""
    p_password = prof.inputs.password if prof is not None else ""
    p_database = prof.inputs.database if prof is not None else ""

    host = _first(req.host, _dsn_value(params, "host"), p_host, env.host)
    port = _first(req.port, _dsn_value(params, "port"), p_port, env.port)
    user = _first(req.user, _dsn_value(params, "user"), p_user, env.user)
    password = _first(req.password, _dsn_value(params, "password"), p_password, env.password)
    database = _first(req.database, _dsn_value(params, "dbname"), p_database, env.database)

    if port != "":
        if not (port.isascii() and port.isdigit()) or int(port) < 1 or int(port) > _MAX_PORT:
            return Err(error=ConnectionError_InvalidPort(value=port))

    if database == "":
        return Err(error=ConnectionError_MissingDatabase())

    tls = request.tls
    if tls.mode == "" and prof is not None:
        tls = prof.tls
    tls_error = _validate_tls(tls)
    if tls_error != "":
        return Err(error=ConnectionError_TlsInvalid(message=tls_error))

    ssh: Option[SshSettings] = Nothing()
    if isinstance(request.ssh, Some):
        ssh = request.ssh
    elif prof is not None:
        ssh = prof.ssh
    if isinstance(ssh, Some):
        ssh_error = _validate_ssh(ssh.value)
        if ssh_error != "":
            return Err(error=ConnectionError_SshInvalid(message=ssh_error))

    settings = ConnectionSettings(host=host, port=port, user=user, password=password, database=database)
    return Ok(value=ConnectionPlan(settings=settings, dsn=dsn, tls=tls, ssh=ssh))
