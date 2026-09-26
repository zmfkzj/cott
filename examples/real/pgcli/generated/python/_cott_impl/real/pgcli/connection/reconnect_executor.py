from typing import cast

import click
import psycopg
import psycopg.errors
from psycopg.conninfo import make_conninfo
from psycopg.types.string import TextLoader

from cott_runtime import CottList, Err, Ok, Opaque, Result
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam, Executor, ReconnectRequest


def _set_param(params: list[tuple[str, str]], name: str, value: str) -> None:
    for index, (key, _old) in enumerate(params):
        if key == name:
            params[index] = (name, value)
            return
    params.append((name, value))


def _notify_text(notify: psycopg.Notify) -> str:
    return 'Notification received on channel "' + notify.channel + '" (PID ' + str(notify.pid) + "):\n" + notify.payload


def _open(params: list[tuple[str, str]], previous: Executor) -> Executor:
    lookup = dict(params)
    if "dsn" in lookup:
        others = {name: value for name, value in params if name != "dsn"}
        conninfo = make_conninfo(lookup["dsn"], **others)
    else:
        conninfo = make_conninfo(**lookup)
    connection: psycopg.Connection[tuple[object, ...]] = psycopg.connect(conninfo)
    try:
        connection.autocommit = True
        connection.add_notify_handler(lambda notify: click.secho(_notify_text(notify), fg="green"))
        info = connection.info
        reported = info.get_parameters()
        dbname = reported.get("dbname", lookup.get("dbname", ""))
        user = reported.get("user", lookup.get("user", ""))
        host = reported.get("host", lookup.get("host", ""))
        port = reported.get("port", lookup.get("port", ""))
        virtual = False
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT 1")
            except psycopg.errors.ProtocolViolation:
                virtual = True
        if not host:
            if virtual:
                host = "pgbouncer"
            else:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT setting FROM pg_settings WHERE name = 'unix_socket_directories'")
                    row = cursor.fetchone()
                host = str(row[0]).split(",")[0].strip() if row is not None and row[0] is not None else ""
        superuser = info.parameter_status("is_superuser") in ("on", "1")
        version = info.parameter_status("server_version") or ""
        if not virtual:
            for type_name in ("date", "time", "timestamp", "timestamptz", "bytea", "json", "jsonb"):
                connection.adapters.register_loader(type_name, TextLoader)
        pid = info.backend_pid
    except BaseException:
        connection.close()
        raise
    return Executor(
        connection=Opaque(tag="pgcli.connection", value=connection),
        tunnel=previous.tunnel,
        params=CottList(values=[ConnectionParam(name=name, value=value) for name, value in params]),
        dbname=dbname,
        user=user,
        host=host,
        port=port,
        pid=pid,
        superuser=superuser,
        server_version=version,
        virtual_database=virtual,
    )


def reconnect_executor(executor: Executor, request: ReconnectRequest) -> Result[Executor, ConnectError]:
    params = [(param.name, param.value) for param in executor.params]
    for name, value in (("dbname", request.database), ("user", request.user), ("host", request.host), ("port", request.port)):
        if value:
            _set_param(params, name, value)
    try:
        reconnected = _open(params, executor)
    except Exception as error:
        return Err[ConnectError](error=ConnectError_Failed(message=str(error)))
    try:
        previous = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        previous.close()
    except Exception as error:
        cast(psycopg.Connection[tuple[object, ...]], reconnected.connection.unwrap()).close()
        return Err[ConnectError](error=ConnectError_Failed(message=str(error)))
    return Ok(value=reconnected)
