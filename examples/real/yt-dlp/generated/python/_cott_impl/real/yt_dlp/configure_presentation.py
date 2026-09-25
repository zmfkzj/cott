import os
import stat
from pathlib import Path

import cott_runtime
from cott_runtime import Result, UNIT, Unit
from real.yt_dlp_types import MediaError, MediaError_LogFailure, PresentationRequest


def _log_failure(path: Path, message: str) -> Result[Unit, MediaError]:
    return cott_runtime.Err(error=MediaError_LogFailure(path=path, message=message))


def _close_fd(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _is_regular_fd(fd: int) -> bool | None:
    try:
        return stat.S_ISREG(os.fstat(fd).st_mode)
    except OSError:
        return None


def configure_presentation(request: PresentationRequest) -> Result[Unit, MediaError]:
    log_file: Path = Path(request.log_file)
    raw: str = str(request.log_file)
    leaf: str = os.path.basename(raw)
    if leaf in ("", ".", ".."):
        return _log_failure(log_file, "log file must name a file leaf")
    flags: int = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd: int = os.open(log_file, flags, 0o600)
    except OSError:
        return _log_failure(log_file, "cannot open log file for appending")
    regular: bool | None = _is_regular_fd(fd)
    closed: bool = _close_fd(fd)
    if regular is None:
        return _log_failure(log_file, "cannot inspect log file")
    if not regular:
        return _log_failure(log_file, "log file is not a regular file")
    if not closed:
        return _log_failure(log_file, "cannot close log file")
    return cott_runtime.Ok(value=UNIT)
