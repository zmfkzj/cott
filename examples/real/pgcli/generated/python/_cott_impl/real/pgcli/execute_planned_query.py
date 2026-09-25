import os
import time
from typing import Final, cast

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import tuple_row
from cott_runtime import CottList, Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_ConnectionFailed, ClientError_QueryFailed, ClientError_TransactionFailed, ClientError_TunnelUnsupported, ConnectionPlan, ExecutedQuery, QueryRequest, QueryResult, TlsMode, TlsMode_Allow, TlsMode_Default, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TransactionMode_AutoCommit, TransactionMode_Manual

_SSL_RANKS: Final[str] = "disable,allow,prefer,require,verify-ca,verify-full"


def _rank(mode: str) -> int:
    ranks = _SSL_RANKS.split(",")
    return ranks.index(mode) if mode in ranks else -1


def _mode_text(mode: TlsMode) -> str:
    if isinstance(mode, TlsMode_Default):
        return ""
    if isinstance(mode, TlsMode_Disable):
        return "disable"
    if isinstance(mode, TlsMode_Allow):
        return "allow"
    if isinstance(mode, TlsMode_Prefer):
        return "prefer"
    if isinstance(mode, TlsMode_Require):
        return "require"
    if isinstance(mode, TlsMode_VerifyCa):
        return "verify-ca"
    return "verify-full"


def _conninfo(plan: ConnectionPlan) -> str:
    settings = plan.settings
    tls = plan.tls
    params: dict[str, str] = {}
    for key, value in (("host", settings.host), ("port", settings.port), ("user", settings.user), ("password", settings.password), ("dbname", settings.database)):
        if value:
            params[key] = value
    requested = _mode_text(tls.mode)
    if requested:
        existing = conninfo_to_dict(plan.dsn).get("sslmode")
        current = existing if isinstance(existing, str) else ""
        if current == "" or (_rank(current) >= 0 and _rank(requested) >= _rank(current)):
            params["sslmode"] = requested
    root = tls.root_certificate
    if isinstance(root, Some):
        params["sslrootcert"] = os.fspath(root.value)
    client = tls.client
    if isinstance(client, Some):
        params["sslcert"] = os.fspath(client.value.certificate)
        params["sslkey"] = os.fspath(client.value.private_key)
    params["connect_timeout"] = "10"
    return make_conninfo(plan.dsn, **params)


def _error_message(error: psycopg.Error, fallback: str) -> str:
    primary = error.diag.message_primary
    sqlstate = error.sqlstate
    if primary:
        return f"{sqlstate}: {primary}" if sqlstate else primary
    return f"{fallback} ({sqlstate})" if sqlstate else fallback


def _cell(value: object) -> str:
    if value is None:
        return "<null>"
    if isinstance(value, memoryview):
        return "\\x" + bytes(cast(memoryview[int], value)).hex()
    if isinstance(value, bytes | bytearray):
        return "\\x" + bytes(value).hex()
    return str(value)


def _notice(notices: list[str], diag: psycopg.errors.Diagnostic) -> None:
    notices.append(diag.message_primary or "")


def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]:
    plan = request.connection
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_TunnelUnsupported())
    mode = request.transaction
    autocommit = isinstance(mode, TransactionMode_AutoCommit)
    read_only = not autocommit and not isinstance(mode, TransactionMode_Manual)
    notices: list[str] = []
    try:
        conninfo = _conninfo(plan)
        conn = psycopg.connect(conninfo, autocommit=autocommit, connect_timeout=10, row_factory=tuple_row)
    except psycopg.Error:
        return Err(error=ClientError_ConnectionFailed(message="connection failed"))
    columns: list[str] = []
    rows: list[CottList[str]] = []
    status = ""
    affected = 0
    elapsed_ns = 0
    try:
        conn.add_notice_handler(lambda diag: _notice(notices, diag))
        if read_only:
            conn.read_only = True
        started = time.monotonic_ns()
        try:
            with conn.cursor() as cursor:
                cursor.execute(request.sql.encode("utf-8"))
                while True:
                    if cursor.description is not None:
                        columns = [column.name for column in cursor.description]
                        rows = [CottList(values=[_cell(value) for value in row]) for row in cursor.fetchmany(request.max_rows)] if request.max_rows > 0 else []
                    status = cursor.statusmessage or ""
                    affected = cursor.rowcount if cursor.rowcount >= 0 else 0
                    if not cursor.nextset():
                        break
        except psycopg.Error as error:
            message = _error_message(error, "query failed")
            if not autocommit:
                try:
                    conn.rollback()
                except psycopg.Error:
                    return Err(error=ClientError_TransactionFailed(message="rollback failed"))
            return Err(error=ClientError_QueryFailed(message=message))
        if not autocommit:
            try:
                if read_only:
                    conn.rollback()
                else:
                    conn.commit()
            except psycopg.Error:
                return Err(error=ClientError_TransactionFailed(message="rollback failed" if read_only else "commit failed"))
        elapsed_ns = time.monotonic_ns() - started
    finally:
        conn.close()
    elapsed = elapsed_ns // 1_000_000 if request.timing else 0
    return Ok(value=ExecutedQuery(
        result=QueryResult(columns=CottList(values=columns), rows=CottList(values=rows)),
        status=status,
        affected_rows=affected,
        elapsed_ms=elapsed,
        notices=CottList(values=notices),
    ))
