from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from cott_runtime import CottList, Err, Ok, Result, Some, U32
from real.pgcli_types import ClientError, ClientError_NotificationFailed, Notification, NotificationRequest


def _text_or_none(value: str) -> str | None:
    return value if value != "" else None


def _path_or_none(value: Path) -> str | None:
    text = str(value)
    return text if text not in ("", ".") else None


def _conninfo(request: NotificationRequest) -> str:
    settings = request.connection.settings
    tls = request.connection.tls
    return make_conninfo(
        request.connection.dsn,
        host=_text_or_none(settings.host),
        port=_text_or_none(settings.port),
        user=_text_or_none(settings.user),
        password=_text_or_none(settings.password),
        dbname=_text_or_none(settings.database),
        sslmode=_text_or_none(tls.mode),
        sslrootcert=_path_or_none(tls.root_certificate),
        sslcert=_path_or_none(tls.certificate),
        sslkey=_path_or_none(tls.private_key),
    )


def _failure(message: str) -> Result[CottList[Notification], ClientError]:
    return Err(error=ClientError_NotificationFailed(message=message))


def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]:
    if isinstance(request.connection.ssh, Some):
        return _failure("SSH tunnelling is not supported for notification listening")
    limit = request.max_notifications
    received: list[Notification] = []
    try:
        conninfo = _conninfo(request)
    except psycopg.ProgrammingError:
        return _failure("notification listening failed: invalid connection settings")
    try:
        with psycopg.connect(conninfo, autocommit=True) as conn:
            for channel in request.channels:
                conn.execute(sql.SQL("LISTEN {}").format(sql.Identifier(channel)))
            if limit > 0:
                for notify in conn.notifies(timeout=request.timeout_ms / 1000.0, stop_after=limit):
                    pid: U32 = notify.pid
                    received.append(Notification(channel=notify.channel, payload=notify.payload, pid=pid))
                    if len(received) >= limit:
                        break
    except psycopg.OperationalError:
        return _failure("notification listening failed: connection or operational error")
    except psycopg.Error:
        return _failure("notification listening failed: database error")
    return Ok(value=CottList(values=received))
