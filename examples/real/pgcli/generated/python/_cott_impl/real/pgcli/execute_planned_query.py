import time
from typing import cast

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.rows import tuple_row
from cott_runtime import CottList, Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_QueryFailed, ClientError_TransactionFailed, ConnectionPlan, ExecutedQuery, QueryRequest, QueryResult, TransactionMode_AutoCommit, TransactionMode_Manual


def _error_message(error: psycopg.Error, fallback: str) -> str:
    primary = error.diag.message_primary
    sqlstate = error.sqlstate
    if primary:
        return f"{sqlstate}: {primary}" if sqlstate else primary
    if sqlstate:
        return f"{fallback} ({sqlstate})"
    return fallback


def _conninfo(plan: ConnectionPlan) -> str:
    settings = plan.settings
    tls = plan.tls
    candidates: list[tuple[str, str]] = [
        ("host", settings.host),
        ("port", settings.port),
        ("user", settings.user),
        ("password", settings.password),
        ("dbname", settings.database),
        ("sslmode", tls.mode),
        ("sslrootcert", str(tls.root_certificate)),
        ("sslcert", str(tls.certificate)),
        ("sslkey", str(tls.private_key)),
    ]
    params: dict[str, str] = {}
    for key, value in candidates:
        if value and value != ".":
            params[key] = value
    return make_conninfo(plan.dsn, **params)


def _cell(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, memoryview):
        view = cast(memoryview[int], value)
        return "\\x" + bytes(view).hex()
    if isinstance(value, bytes | bytearray):
        return "\\x" + bytes(value).hex()
    return str(value)


def _notice_text(diag: psycopg.errors.Diagnostic) -> str:
    return diag.message_primary or ""


def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]:
    plan = request.connection
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_QueryFailed(message="SSH tunnelling is not available for planned query execution"))
    mode = request.transaction
    autocommit = isinstance(mode, TransactionMode_AutoCommit)
    read_only = not autocommit and not isinstance(mode, TransactionMode_Manual)
    notices: list[str] = []
    started = time.monotonic_ns()
    try:
        conninfo = _conninfo(plan)
        conn = psycopg.connect(conninfo, autocommit=autocommit, row_factory=tuple_row)
    except psycopg.Error:
        return Err(error=ClientError_QueryFailed(message="connection failed"))
    with conn:
        conn.add_notice_handler(lambda diag: notices.append(_notice_text(diag)))
        try:
            if read_only:
                conn.read_only = True
        except psycopg.Error as error:
            return Err(error=ClientError_TransactionFailed(message=_error_message(error, "cannot set read-only transaction")))
        columns: list[str] = []
        rows: list[CottList[str]] = []
        status = ""
        affected = 0
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
            query_message = _error_message(error, "query failed")
            if not autocommit:
                try:
                    conn.rollback()
                except psycopg.Error as rollback_error:
                    return Err(error=ClientError_TransactionFailed(message=f"{query_message}; rollback failed: {_error_message(rollback_error, 'rollback failed')}"))
            return Err(error=ClientError_QueryFailed(message=query_message))
        if not autocommit:
            try:
                if read_only:
                    conn.rollback()
                else:
                    conn.commit()
            except psycopg.Error as error:
                return Err(error=ClientError_TransactionFailed(message=_error_message(error, "transaction completion failed")))
    elapsed = (time.monotonic_ns() - started) // 1_000_000 if request.timing else 0
    return Ok(value=ExecutedQuery(
        result=QueryResult(columns=CottList(values=columns), rows=CottList(values=rows)),
        status=status,
        affected_rows=affected,
        elapsed_ms=elapsed,
        notices=CottList(values=notices),
    ))
