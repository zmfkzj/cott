import getpass
import logging
from typing import Any, Final, Literal, cast

import click
import keyring
import psycopg
import psycopg.errors
import sshtunnel
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.types.string import TextLoader

from cott_runtime import CottList, Err, Nothing, Ok, Opaque, Option, Result, Some
from real.pgcli.connection import choose_connect_timeout, find_ssh_tunnel_url, parse_ssh_tunnel_url
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam, Executor, OpenRequest

_KEYRING_HELP: Final[str] = "\nTo remove this message do one of the following:\n- prepare keyring as described at: https://keyring.readthedocs.io/en/stable/\n- uninstall keyring: pip uninstall keyring\n- disable keyring in our configuration: add keyring = False to [main]"


def _failed(message: str) -> Result[Executor, ConnectError]:
    return Err(error=ConnectError_Failed(message=message))


def _parse_dsn(dsn: str) -> dict[str, str]:
    if not dsn:
        return {}
    try:
        parsed = conninfo_to_dict(dsn)
    except psycopg.ProgrammingError:
        return {}
    return {name: str(value) for name, value in parsed.items() if value is not None}


def _set_param(params: list[tuple[str, str]], name: str, value: str) -> None:
    for index, (key, _) in enumerate(params):
        if key == name:
            params[index] = (name, value)
            return
    params.append((name, value))


def _prompt_password(user: str) -> str:
    answer = cast(object, click.prompt("Password for " + user, hide_input=True, show_default=False, type=str))
    return answer if isinstance(answer, str) else str(answer)


def _notify_text(notify: psycopg.Notify) -> str:
    return 'Notification received on channel "' + notify.channel + '" (PID ' + str(notify.pid) + "):\n" + notify.payload


def _build_params(database: str, user: str, passwd: str, host: str, port: str, dsn: str, kwargs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    merged = [("dbname", database), ("user", user), ("password", passwd), ("host", host), ("port", port), ("dsn", dsn)]
    for name, value in kwargs:
        _set_param(merged, name, value)
    if dsn:
        kept = [(name, value) for name, value in merged if name in ("dsn", "password", "hostaddr", "connect_timeout")]
        password = next((value for name, value in kept if name == "password"), "")
        if password:
            kept = [(name, value) for name, value in kept if name != "password"]
            _set_param(kept, "dsn", make_conninfo(dsn, password=password))
        merged = kept
    return [(name, value) for name, value in merged if value]


def _connect(params: list[tuple[str, str]], tunnel: Any) -> Executor:
    lookup = dict(params)
    if "dsn" in lookup:
        conninfo = make_conninfo(lookup["dsn"], **{name: value for name, value in params if name != "dsn"})
    else:
        conninfo = make_conninfo(**lookup)
    conn: psycopg.Connection[tuple[object, ...]] = psycopg.connect(conninfo)
    try:
        conn.autocommit = True
        conn.add_notify_handler(lambda notify: click.secho(_notify_text(notify), fg="green"))
        info = conn.info
        reported = info.get_parameters()
        dbname = reported.get("dbname", lookup.get("dbname", ""))
        user = reported.get("user", lookup.get("user", ""))
        host = reported.get("host", lookup.get("host", ""))
        port = reported.get("port", lookup.get("port", ""))
        virtual = False
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT 1")
            except psycopg.errors.ProtocolViolation:
                virtual = True
        if not host:
            if virtual:
                host = "pgbouncer"
            else:
                with conn.cursor() as cur:
                    cur.execute("SELECT setting FROM pg_settings WHERE name = 'unix_socket_directories'")
                    row = cur.fetchone()
                host = str(row[0]).split(",")[0].strip() if row is not None and row[0] is not None else ""
        superuser = info.parameter_status("is_superuser") in ("on", "1")
        version = info.parameter_status("server_version") or ""
        if not virtual:
            for type_name in ("date", "time", "timestamp", "timestamptz", "bytea", "json", "jsonb"):
                conn.adapters.register_loader(type_name, TextLoader)
        if not dbname and not virtual:
            raise ValueError("dbname is empty")
        tunnel_option: Option[Opaque[Literal["pgcli.ssh-tunnel"]]] = Nothing()
        if tunnel is not None:
            handle: Opaque[Literal["pgcli.ssh-tunnel"]] = Opaque(tag="pgcli.ssh-tunnel", value=cast(object, tunnel))
            tunnel_option = Some(value=handle)
        return Executor(
            connection=Opaque(tag="pgcli.connection", value=conn),
            tunnel=tunnel_option,
            params=CottList(values=[ConnectionParam(name=name, value=value) for name, value in params]),
            dbname=dbname,
            user=user,
            host=host,
            port=port,
            pid=info.backend_pid,
            superuser=superuser,
            server_version=version,
            virtual_database=virtual,
        )
    except BaseException:
        conn.close()
        raise


def _is_password_error(error: Exception) -> bool:
    if not isinstance(error, (psycopg.OperationalError, psycopg.InterfaceError)) or not error.args:
        return False
    first = str(cast(object, error.args[0]))
    return "no password supplied" in first or "password authentication failed" in first


def _stop_tunnel(tunnel: Any) -> None:
    if tunnel is not None:
        try:
            tunnel.stop()
        except Exception:
            return


def _start_tunnel(url: str, host: str, port: str) -> Any:
    target = parse_ssh_tunnel_url(url)
    logger = logging.getLogger("pgcli.main")
    handlers = logger.handlers[:]
    ssh_username: str | None = target.username.value if isinstance(target.username, Some) else None
    ssh_password: str | None = target.password.value if isinstance(target.password, Some) else None
    tunnel: Any = None
    try:
        tunnel = sshtunnel.SSHTunnelForwarder(
            ssh_address_or_host=(target.host, target.port),
            local_bind_address=("127.0.0.1",),
            remote_bind_address=(host, int(port or 5432)),
            logger=logger,
            ssh_username=ssh_username,
            ssh_password=ssh_password,
        )
        tunnel.start()
    except BaseException:
        _stop_tunnel(tunnel)
        raise
    finally:
        logger.handlers = handlers
    return tunnel


def _first_local_port(tunnel: Any) -> str:
    ports = cast(object, tunnel.local_bind_ports)
    if isinstance(ports, list):
        first = cast(list[object], ports)[0]
    elif isinstance(ports, tuple):
        first = cast(tuple[object, ...], ports)[0]
    else:
        first = ports
    return str(first) if isinstance(first, int) else str(int(str(first)))


def open_executor(request: OpenRequest) -> Result[Executor, ConnectError]:
    tunnel: Any = None
    try:
        spec = request.spec
        user = spec.user or getpass.getuser()
        database = spec.database or user
        kwargs = [(param.name, param.value) for param in spec.extra]
        if not any(name == "application_name" for name, _ in kwargs):
            kwargs.append(("application_name", request.application_name))
        dsn = spec.dsn
        timeout = choose_connect_timeout(request.explicit_timeout, dsn, CottList(values=[ConnectionParam(name=name, value=value) for name, value in kwargs]), request.pgconnect_timeout, request.default_timeout)
        if isinstance(timeout, Some):
            _set_param(kwargs, "connect_timeout", str(timeout.value))
        dsn_params = _parse_dsn(dsn)
        passwd = spec.password
        if request.force_password_prompt:
            if not passwd:
                passwd = _prompt_password(user)
        elif not passwd and not (dsn and "password" in dsn_params):
            passwd = request.pgpassword
        host = spec.host
        port = spec.port
        key = user + "@" + host + "@" + port
        if not passwd and request.keyring_enabled:
            try:
                passwd = keyring.get_password("pgcli", key) or ""
            except Exception as error:
                click.secho("Load your password from keyring returned:\n" + str(error) + _KEYRING_HELP, err=True, fg="red")
                passwd = ""
        if dsn:
            host = dsn_params.get("host", host)
            port = dsn_params.get("port", port)
        url = find_ssh_tunnel_url(request.explicit_tunnel, request.dsn_alias, host, request.dsn_tunnels, request.host_tunnels)
        if isinstance(url, Some):
            tunnel = _start_tunnel(url.value, host, port)
            port = _first_local_port(tunnel)
            if dsn:
                dsn = make_conninfo(dsn, host=host, hostaddr="127.0.0.1", port=port)
            else:
                _set_param(kwargs, "hostaddr", "127.0.0.1")
        try:
            executor = _connect(_build_params(database, user, passwd, host, port, dsn, kwargs), tunnel)
        except Exception as error:
            if request.never_password_prompt or not _is_password_error(error):
                raise
            passwd = _prompt_password(user)
            executor = _connect(_build_params(database, user, passwd, host, port, dsn, kwargs), tunnel)
        if passwd and request.keyring_enabled:
            try:
                keyring.set_password("pgcli", key, passwd)
            except Exception as error:
                click.secho("Set password in keyring returned:\n" + str(error) + _KEYRING_HELP, err=True, fg="red")
        return Ok(value=executor)
    except Exception as error:
        _stop_tunnel(tunnel)
        return _failed(str(error))
