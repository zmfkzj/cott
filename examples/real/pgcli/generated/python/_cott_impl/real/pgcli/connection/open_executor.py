import getpass
import logging
from typing import Any, Literal, cast

import click
import keyring
import psycopg
import psycopg.errors
import sshtunnel
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.types.string import TextLoader

from cott_runtime import CottContractViolation, CottList, Err, Nothing, Ok, Opaque, Option, Result, Some, _cott_fixture_database
from real.pgcli.connection import choose_connect_timeout, find_ssh_tunnel_url, parse_ssh_tunnel_url
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam, Executor, OpenRequest


def _failed(message: str) -> Result[Executor, ConnectError]:
    return Err(error=ConnectError_Failed(message=message))


def _dsn_parameters(dsn: str) -> dict[str, str]:
    if not dsn:
        return {}
    try:
        parsed = conninfo_to_dict(dsn)
    except psycopg.ProgrammingError:
        return {}
    return {key: str(value) for key, value in parsed.items() if isinstance(value, (str, int))}


def _password_prompt(user: str) -> str:
    answer = cast(object, click.prompt("Password for " + user, hide_input=True, show_default=False, type=str))
    return answer if isinstance(answer, str) else str(answer)


def _keyring_warning(heading: str, error: Exception) -> None:
    click.secho(heading + str(error) + "\nTo remove this message do one of the following:\n- prepare keyring as described at: https://keyring.readthedocs.io/en/stable/\n- uninstall keyring: pip uninstall keyring\n- disable keyring in our configuration: add keyring = False to [main]", fg="red", err=True)


def _notify(notification: psycopg.Notify) -> None:
    click.secho('Notification received on channel "' + notification.channel + '" (PID ' + str(notification.pid) + "):\n" + notification.payload, fg="green")


def _stop_tunnel(tunnel: Any) -> None:
    try:
        tunnel.stop()
    except Exception:
        return


def _start_tunnel(url: str, host: str, port: str) -> Any:
    target = parse_ssh_tunnel_url(url)
    logger = logging.getLogger("pgcli.main")
    handlers = logger.handlers[:]
    forwarder: Any = None
    try:
        options: dict[str, Any] = {
            "local_bind_address": ("127.0.0.1",),
            "remote_bind_address": (host, int(port or 5432)),
            "ssh_address_or_host": (target.host, target.port),
            "logger": logger,
        }
        if isinstance(target.username, Some):
            options["ssh_username"] = target.username.value
        if isinstance(target.password, Some):
            options["ssh_password"] = target.password.value
        forwarder = sshtunnel.SSHTunnelForwarder(**options)
        forwarder.start()
        return forwarder
    except BaseException:
        if forwarder is not None:
            _stop_tunnel(forwarder)
        raise
    finally:
        logger.handlers[:] = handlers


def _forwarded_port(tunnel: Any) -> str:
    ports = cast(object, tunnel.local_bind_ports)
    if not isinstance(ports, (list, tuple)):
        raise TypeError("SSH tunnel has no local bind ports")
    first = cast(list[object] | tuple[object, ...], ports)[0]
    if not isinstance(first, (str, int)):
        raise TypeError("SSH tunnel local bind port is invalid")
    return str(first)


def _params(database: str, user: str, password: str, host: str, port: str, dsn: str, extras: dict[str, str]) -> dict[str, str]:
    params = {"dbname": database, "user": user, "password": password, "host": host, "port": port, "dsn": dsn}
    params.update(extras)
    if dsn:
        params = {key: value for key, value in params.items() if key in ("dsn", "password", "hostaddr", "connect_timeout")}
        if password:
            params["dsn"] = make_conninfo(dsn, password=password)
            params.pop("password", None)
    return {key: value for key, value in params.items() if value}


def _connect(params: dict[str, str], tunnel: Any) -> Executor:
    dsn = params.get("dsn", "")
    conninfo = make_conninfo(dsn, **{key: value for key, value in params.items() if key != "dsn"}) if dsn else make_conninfo(**params)
    conn = cast(psycopg.Connection[tuple[object, ...]], psycopg.connect(conninfo))
    try:
        conn.autocommit = True
        conn.add_notify_handler(lambda notification: _notify(notification))
        info = conn.info
        reported = info.get_parameters()
        dbname = str(reported.get("dbname") or params.get("dbname", ""))
        user = str(reported.get("user") or params.get("user", ""))
        host = str(reported.get("host") or params.get("host", ""))
        port = str(reported.get("port") or params.get("port", ""))
        virtual = False
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT 1")
            except psycopg.errors.ProtocolViolation:
                virtual = True
        if not host:
            if virtual:
                host = "pgbouncer"
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT setting FROM pg_settings WHERE name = 'unix_socket_directories'")
                    row = cursor.fetchone()
                host = str(row[0]).split(",")[0].strip() if row is not None and row[0] is not None else ""
        if not virtual:
            for typename in ("date", "time", "timestamp", "timestamptz", "bytea", "json", "jsonb"):
                conn.adapters.register_loader(typename, TextLoader)
        tunnel_option: Option[Opaque[Literal["pgcli.ssh-tunnel"]]] = Nothing()
        if tunnel is not None:
            tunnel_option = Some(value=Opaque(tag="pgcli.ssh-tunnel", value=cast(object, tunnel)))
        return Executor(
            connection=Opaque(tag="pgcli.connection", value=conn),
            tunnel=tunnel_option,
            params=CottList(values=[ConnectionParam(name=key, value=value) for key, value in params.items()]),
            dbname=dbname,
            user=user,
            host=host,
            port=port,
            pid=info.backend_pid,
            superuser=info.parameter_status("is_superuser") in ("on", "1"),
            server_version=info.parameter_status("server_version") or "",
            virtual_database=virtual,
        )
    except BaseException:
        conn.close()
        raise


def _password_failure(error: Exception) -> bool:
    return isinstance(error, (psycopg.OperationalError, psycopg.InterfaceError)) and bool(error.args) and ("no password supplied" in str(error.args[0]) or "password authentication failed" in str(error.args[0]))


def _fixture_connect() -> None:
    try:
        _cott_fixture_database("connect")
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            raise


def open_executor(request: OpenRequest) -> Result[Executor, ConnectError]:
    tunnel: Any = None
    try:
        spec = request.spec
        user = spec.user or getpass.getuser()
        database = spec.database or user
        extras = {param.name: param.value for param in spec.extra}
        if "application_name" not in extras:
            extras["application_name"] = request.application_name
        kwargs = CottList(values=[ConnectionParam(name=key, value=value) for key, value in extras.items()])
        timeout = choose_connect_timeout(request.explicit_timeout, spec.dsn, kwargs, request.pgconnect_timeout, request.default_timeout)
        if isinstance(timeout, Some):
            extras["connect_timeout"] = str(timeout.value)
        dsn_values = _dsn_parameters(spec.dsn)
        password = spec.password
        if request.force_password_prompt and not password:
            password = _password_prompt(user)
        elif not request.force_password_prompt and not password and not (spec.dsn and "password" in dsn_values):
            password = request.pgpassword
        key = user + "@" + spec.host + "@" + spec.port
        if not password and request.keyring_enabled:
            try:
                saved = cast(object, keyring.get_password("pgcli", key))
                password = saved if isinstance(saved, str) else ""
            except Exception as error:
                _keyring_warning("Load your password from keyring returned:\n", error)
        host = dsn_values.get("host", spec.host)
        port = dsn_values.get("port", spec.port)
        dsn = spec.dsn
        url = find_ssh_tunnel_url(request.explicit_tunnel, request.dsn_alias, host, request.dsn_tunnels, request.host_tunnels)
        if isinstance(url, Some):
            tunnel = _start_tunnel(url.value, host, port)
            forwarded_port = _forwarded_port(tunnel)
            extras["hostaddr"] = "127.0.0.1"
            if dsn:
                dsn = make_conninfo(dsn, host=host, hostaddr="127.0.0.1", port=forwarded_port)
            else:
                port = forwarded_port
        params = _params(database, user, password, host, port, dsn, extras)
        _fixture_connect()
        try:
            executor = _connect(params, tunnel)
        except (psycopg.OperationalError, psycopg.InterfaceError) as error:
            if request.never_password_prompt or not _password_failure(error):
                raise
            password = _password_prompt(user)
            params = _params(database, user, password, host, port, dsn, extras)
            executor = _connect(params, tunnel)
        if password and request.keyring_enabled:
            try:
                keyring.set_password("pgcli", key, password)
            except Exception as error:
                _keyring_warning("Set password in keyring returned:\n", error)
        return Ok(value=executor)
    except CottContractViolation:
        if tunnel is not None:
            _stop_tunnel(tunnel)
        raise
    except KeyboardInterrupt:
        if tunnel is not None:
            _stop_tunnel(tunnel)
        raise
    except Exception as error:
        if tunnel is not None:
            _stop_tunnel(tunnel)
        return _failed(str(error))
