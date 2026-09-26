import psycopg
import psycopg.errors
from psycopg.conninfo import make_conninfo
from psycopg.types.string import TextLoader

from cott_runtime import CottList, Err, Ok, Opaque, Result
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam, Executor


def _conninfo(params: CottList[ConnectionParam]) -> str:
    dsn = ""
    others: dict[str, str] = {}
    for param in params:
        if param.name == "dsn":
            dsn = param.value
        else:
            others[param.name] = param.value
    if dsn:
        return make_conninfo(dsn, **others)
    return make_conninfo(**others)


def _param(params: CottList[ConnectionParam], name: str) -> str:
    for param in params:
        if param.name == name:
            return param.value
    return ""


def _is_virtual(conn: psycopg.Connection[tuple[object, ...]]) -> bool:
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT 1")
        except psycopg.errors.ProtocolViolation:
            return True
    return False


def _socket_directory(conn: psycopg.Connection[tuple[object, ...]]) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT setting FROM pg_settings WHERE name = 'unix_socket_directories'")
        row = cur.fetchone()
    if row is None or not row or row[0] is None:
        return ""
    return str(row[0]).split(",")[0].strip()


def _build(executor: Executor, conn: psycopg.Connection[tuple[object, ...]]) -> Executor:
    conn.autocommit = True
    info = conn.info
    reported = info.get_parameters()
    params = executor.params
    dbname = reported.get("dbname") or _param(params, "dbname")
    user = reported.get("user") or _param(params, "user")
    host = reported.get("host") or _param(params, "host")
    port = reported.get("port") or _param(params, "port")
    virtual = _is_virtual(conn)
    if not host:
        host = "pgbouncer" if virtual else _socket_directory(conn)
    superuser = info.parameter_status("is_superuser") in ("on", "1")
    server_version = info.parameter_status("server_version") or ""
    if not virtual:
        for type_name in ("date", "time", "timestamp", "timestamptz", "bytea", "json", "jsonb"):
            conn.adapters.register_loader(type_name, TextLoader)
    return Executor(
        connection=Opaque(tag="pgcli.connection", value=conn),
        tunnel=executor.tunnel,
        params=params,
        dbname=dbname,
        user=user,
        host=host,
        port=port,
        pid=info.backend_pid,
        superuser=superuser,
        server_version=server_version,
        virtual_database=virtual,
    )


def copy_executor(executor: Executor) -> Result[Executor, ConnectError]:
    try:
        conn: psycopg.Connection[tuple[object, ...]] = psycopg.connect(_conninfo(executor.params))
    except Exception as error:
        return Err(error=ConnectError_Failed(message=str(error)))
    try:
        copied = _build(executor, conn)
    except Exception as error:
        conn.close()
        return Err(error=ConnectError_Failed(message=str(error)))
    return Ok(value=copied)
