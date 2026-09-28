import cott_runtime
import psycopg
import psycopg.errors
from cott_runtime import Err, Ok, Opaque, Result
from psycopg.conninfo import make_conninfo
from psycopg.types.string import TextLoader

from real.pgcli.connection_types import ConnectError, ConnectError_Failed, Executor


def copy_executor(executor: Executor) -> Result[Executor, ConnectError]:
    conn: psycopg.Connection[tuple[object, ...]] | None = None
    try:
        params: dict[str, str] = {}
        dsn = ""
        for param in executor.params:
            if param.name == "dsn":
                dsn = param.value
            else:
                params[param.name] = param.value
        conninfo = make_conninfo(dsn, **params) if dsn else make_conninfo(**params)

        try:
            cott_runtime._cott_fixture_database("connect")
        except cott_runtime.CottContractViolation as violation:
            if violation.message != "fixture adapters are inactive":
                raise
        conn = psycopg.connect(conninfo)
        conn.autocommit = True
        info = conn.info
        reported = info.get_parameters()
        dbname = reported.get("dbname") or params.get("dbname", "")
        user = reported.get("user") or params.get("user", "")
        host = reported.get("host") or params.get("host", "")
        port = reported.get("port") or params.get("port", "")

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
                host = "" if row is None or not row or row[0] is None else str(row[0]).split(",")[0].strip()

        if not virtual:
            for type_name in ("date", "time", "timestamp", "timestamptz", "bytea", "json", "jsonb"):
                conn.adapters.register_loader(type_name, TextLoader)

        return Ok(value=Executor(
            connection=Opaque(tag="pgcli.connection", value=conn),
            tunnel=executor.tunnel,
            params=executor.params,
            dbname=dbname,
            user=user,
            host=host,
            port=port,
            pid=info.backend_pid,
            superuser=info.parameter_status("is_superuser") in ("on", "1"),
            server_version=info.parameter_status("server_version") or "",
            virtual_database=virtual,
        ))
    except Exception as error:
        failure = Err[ConnectError](error=ConnectError_Failed(message=str(error)))
        if conn is not None:
            try:
                conn.close()
            except Exception:
                return failure
        return failure
