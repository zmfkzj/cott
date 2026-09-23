import time
from pathlib import PurePath
from typing import Final, LiteralString, cast

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.errors import Diagnostic

from cott_runtime import CottList, Err, Ok, Result, Some, U64
from real.pgcli_types import ClientError, ClientError_QueryFailed, ClientError_TransactionFailed, ConnectionPlan, ExecutedQuery, QueryResult, TransactionMode_AutoCommit, TransactionMode_ReadOnly, WatchRequest, WatchResult

_FALLBACK_MESSAGE: Final[str] = "database operation failed"


def _record_notice(sink: list[str], diag: Diagnostic) -> None:
    sink.append(diag.message_primary or "")


def _error_message(error: psycopg.Error) -> str:
    primary = error.diag.message_primary
    return primary if primary else _FALLBACK_MESSAGE


def _path_text(value: PurePath | str) -> str:
    text = str(value)
    return "" if text == "." else text


def _connection_params(plan: ConnectionPlan) -> dict[str, str]:
    settings = plan.settings
    tls = plan.tls
    candidates: dict[str, str] = {
        "host": settings.host,
        "port": settings.port,
        "user": settings.user,
        "password": settings.password,
        "dbname": settings.database,
        "sslmode": tls.mode,
        "sslrootcert": _path_text(tls.root_certificate),
        "sslcert": _path_text(tls.certificate),
        "sslkey": _path_text(tls.private_key),
    }
    return {key: value for key, value in candidates.items() if value}


def _cell(value: object) -> str:
    return "NULL" if value is None else str(value)


def _execute_once(conn: psycopg.Connection[tuple[object, ...]], request: WatchRequest, notices: list[str]) -> Result[ExecutedQuery, ClientError]:
    query = request.query
    notices.clear()
    started = time.monotonic()
    try:
        with conn.cursor() as cur:
            cur.execute(cast(LiteralString, query.sql))
            columns: list[str] = []
            rows: list[CottList[str]] = []
            if cur.description is not None:
                columns = [column.name for column in cur.description]
                fetched = cur.fetchmany(query.max_rows) if query.max_rows > 0 else []
                rows = [CottList(values=[_cell(cell) for cell in row]) for row in fetched]
            status = cur.statusmessage or ""
            affected: U64 = cur.rowcount if cur.rowcount > 0 else 0
    except psycopg.Error as error:
        return Err(error=ClientError_QueryFailed(message=_error_message(error)))
    if isinstance(query.transaction, TransactionMode_ReadOnly):
        try:
            conn.rollback()
        except psycopg.Error as error:
            return Err(error=ClientError_TransactionFailed(message=_error_message(error)))
    elapsed: U64 = int((time.monotonic() - started) * 1000) if query.timing else 0
    result = QueryResult(columns=CottList(values=columns), rows=CottList(values=rows))
    return Ok(value=ExecutedQuery(result=result, status=status, affected_rows=affected, elapsed_ms=elapsed, notices=CottList(values=list(notices))))


def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]:
    plan = request.query.connection
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_QueryFailed(message="SSH tunnelling is not supported by this client"))
    if request.max_iterations == 0:
        return Err(error=ClientError_QueryFailed(message="watch requires at least one iteration"))
    mode = request.query.transaction
    autocommit = isinstance(mode, TransactionMode_AutoCommit)
    notices: list[str] = []
    try:
        conninfo = make_conninfo(plan.dsn, **_connection_params(plan))
        conn = psycopg.connect(conninfo, autocommit=autocommit)
    except psycopg.Error as error:
        return Err(error=ClientError_QueryFailed(message=_error_message(error)))
    try:
        if isinstance(mode, TransactionMode_ReadOnly):
            try:
                conn.read_only = True
            except psycopg.Error as error:
                return Err(error=ClientError_TransactionFailed(message=_error_message(error)))
        conn.add_notice_handler(lambda diag: _record_notice(notices, diag))
        executions: U64 = 0
        last: ExecutedQuery | None = None
        while executions < request.max_iterations:
            if executions > 0:
                time.sleep(request.interval_ms / 1000)
            outcome = _execute_once(conn, request, notices)
            if isinstance(outcome, Err):
                return outcome
            last = outcome.value
            executions += 1
        if last is None:
            return Err(error=ClientError_QueryFailed(message="watch produced no result"))
        return Ok(value=WatchResult(executions=executions, last_result=last))
    finally:
        conn.close()
