from typing import Final

from cott_runtime import U64, Option

from real.harlequin.ide_types import Notification, Severity, Severity_Error

_DEFAULT_TIMEOUT_MS: Final[int] = 5000
_ERROR_TIMEOUT_MS: Final[int] = 10000
_U64_MAX: Final[int] = 18446744073709551615


def notify(title: Option[str], message: str, severity: Severity, now_ms: U64) -> Notification:
    timeout = _ERROR_TIMEOUT_MS if isinstance(severity, Severity_Error) else _DEFAULT_TIMEOUT_MS
    expires_at_ms = min(now_ms + timeout, _U64_MAX)
    return Notification(title=title, message=message, severity=severity, expires_at_ms=expires_at_ms)
