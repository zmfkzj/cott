from typing import cast

import click
import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.errors import ProtocolViolation
from psycopg.types.string import TextLoader

from cott_runtime import CottContractViolation, CottList, Err, Ok, Opaque, Result, _cott_fixture_database
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam, Executor, ReconnectRequest


def _notification_text(notify: psycopg.Notify) -> str:
    return f'Notification received on channel "{notify.channel}" (PID {notify.pid}):\n{notify.payload}'


def _discard_connection(connection: psycopg.Connection[tuple[object, ...]]) -> None:
    try:
        connection.close()
    except Exception:
        return


def reconnect_executor(executor: Executor, request: ReconnectRequest) -> Result[Executor, ConnectError]:
    new_connection: psycopg.Connection[tuple[object, ...]] | None = None
    try:
        old_value = executor.connection.unwrap()
        if not isinstance(old_value, psycopg.Connection):
            raise TypeError("executor connection must be a psycopg connection")
        old_connection = cast(psycopg.Connection[tuple[object, ...]], old_value)

        params = {param.name: param.value for param in executor.params}
        for name, value in (("dbname", request.database), ("user", request.user), ("host", request.host), ("port", request.port)):
            if value:
                params[name] = value
        dsn = params.get("dsn")
        if dsn is not None:
            conninfo = make_conninfo(dsn, **{name: value for name, value in params.items() if name != "dsn"})
        else:
            conninfo = make_conninfo(**params)

        try:
            _cott_fixture_database("connect")
        except CottContractViolation as violation:
            if violation.message != "fixture adapters are inactive":
                raise
        new_connection = cast(psycopg.Connection[tuple[object, ...]], psycopg.connect(conninfo))
        new_connection.autocommit = True
        new_connection.add_notify_handler(lambda notify: click.secho(_notification_text(notify), fg="green"))

        info = new_connection.info
        reported = info.get_parameters()
        dbname = reported.get("dbname") or params.get("dbname", "")
        user = reported.get("user") or params.get("user", "")
        host = reported.get("host") or params.get("host", "")
        port = reported.get("port") or params.get("port", "")

        virtual = False
        with new_connection.cursor() as cursor:
            try:
                cursor.execute("SELECT 1")
            except ProtocolViolation:
                virtual = True
        if not host:
            if virtual:
                host = "pgbouncer"
            else:
                with new_connection.cursor() as cursor:
                    cursor.execute("SELECT setting FROM pg_settings WHERE name = 'unix_socket_directories'")
                    row = cursor.fetchone()
                host = str(row[0]).split(",")[0].strip() if row is not None and row[0] is not None else ""

        if not virtual:
            for type_name in ("date", "time", "timestamp", "timestamptz", "bytea", "json", "jsonb"):
                new_connection.adapters.register_loader(type_name, TextLoader)

        reconnected = Executor(
            connection=Opaque(tag="pgcli.connection", value=new_connection),
            tunnel=executor.tunnel,
            params=CottList(values=[ConnectionParam(name=name, value=value) for name, value in params.items()]),
            dbname=dbname,
            user=user,
            host=host,
            port=port,
            pid=info.backend_pid,
            superuser=info.parameter_status("is_superuser") in ("on", "1"),
            server_version=info.parameter_status("server_version") or "",
            virtual_database=virtual,
        )
    except Exception as error:
        if new_connection is not None:
            _discard_connection(new_connection)
        return Err[ConnectError](error=ConnectError_Failed(message=str(error)))

    _discard_connection(old_connection)
    return Ok(value=reconnected)
