import time

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from cott_runtime import CottList, Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_NotificationFailed, ClientError_TunnelUnsupported, Notification, NotificationRequest, TlsMode, TlsMode_Allow, TlsMode_Default, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa


def _text_or_none(value: str) -> str | None:
    return value if value != "" else None


def _sslmode(mode: TlsMode) -> str | None:
    if isinstance(mode, TlsMode_Default):
        return None
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


def _tls_level(mode: str | None) -> int:
    if mode == "disable":
        return 0
    if mode == "allow":
        return 1
    if mode == "prefer":
        return 2
    if mode == "require":
        return 3
    if mode == "verify-ca":
        return 4
    if mode == "verify-full":
        return 5
    return 0


def _effective_sslmode(dsn: str, mode: TlsMode) -> str | None:
    requested = _sslmode(mode)
    if dsn == "":
        return requested
    try:
        parsed = conninfo_to_dict(dsn)
    except Exception:
        return requested
    dsn_mode_val = parsed.get("sslmode")
    dsn_mode = dsn_mode_val if isinstance(dsn_mode_val, str) else None
    if requested is None:
        return dsn_mode
    if dsn_mode is None:
        return requested
    if _tls_level(dsn_mode) > _tls_level(requested):
        return dsn_mode
    return requested


def _conninfo(request: NotificationRequest) -> str:
    settings = request.connection.settings
    tls = request.connection.tls
    root: str | None = None
    cert: str | None = None
    key: str | None = None
    if isinstance(tls.root_certificate, Some):
        root = str(tls.root_certificate.value)
    if isinstance(tls.client, Some):
        cert = str(tls.client.value.certificate)
        key = str(tls.client.value.private_key)
    eff_sslmode = _effective_sslmode(request.connection.dsn, tls.mode)
    return make_conninfo(
        request.connection.dsn,
        host=_text_or_none(settings.host),
        port=_text_or_none(settings.port),
        user=_text_or_none(settings.user),
        password=_text_or_none(settings.password),
        dbname=_text_or_none(settings.database),
        sslmode=eff_sslmode,
        sslrootcert=root,
        sslcert=cert,
        sslkey=key,
        connect_timeout="10",
    )


def _failure(message: str) -> Result[CottList[Notification], ClientError]:
    return Err(error=ClientError_NotificationFailed(message=message))


def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]:
    channels = [channel for channel in request.channels]
    if len(channels) == 0:
        return _failure("no notification channels given")
    if isinstance(request.connection.ssh, Some):
        return Err(error=ClientError_TunnelUnsupported())
    limit = request.max_notifications
    received: list[Notification] = []
    try:
        conninfo = _conninfo(request)
    except psycopg.Error:
        return _failure("invalid connection settings")
    try:
        with psycopg.connect(conninfo, autocommit=True, connect_timeout=10) as conn:
            try:
                for channel in channels:
                    conn.execute(sql.SQL("LISTEN {}").format(sql.Identifier(channel)))
                deadline = time.monotonic() + request.timeout_ms / 1000.0
                while len(received) < limit:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    for notify in conn.notifies(timeout=remaining, stop_after=limit - len(received)):
                        received.append(Notification(channel=notify.channel, payload=notify.payload, pid=notify.pid))
                        if len(received) >= limit:
                            break
            finally:
                if not conn.closed:
                    try:
                        conn.execute(sql.SQL("UNLISTEN *"))
                    finally:
                        conn.close()
    except psycopg.OperationalError:
        return _failure("notification listening failed: connection error")
    except psycopg.Error:
        return _failure("notification listening failed: database error")
    return Ok(value=CottList(values=received))
