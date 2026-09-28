import os
import stat
from pathlib import Path
from typing import Final

import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp import parse_batch_urls
from real.yt_dlp_types import MediaError, MediaError_BatchReadFailed

_MAX_BYTES: Final[int] = 16777216


def _failure(path: Path, message: str) -> Result[CottList[str], MediaError]:
    return cott_runtime.Err(error=MediaError_BatchReadFailed(path=path, message=message))


def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    try:
        raw: bytes = cott_runtime._cott_fixture_read(path)
    except cott_runtime.CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            cause: BaseException | None = violation.__cause__
            if isinstance(cause, (FileNotFoundError, NotADirectoryError)):
                return _failure(path, "batch file not found")
            if isinstance(cause, IsADirectoryError):
                return _failure(path, "batch path is not a regular file")
            return _failure(path, "cannot read batch file")
        try:
            fd: int = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
        except (FileNotFoundError, NotADirectoryError):
            return _failure(path, "batch file not found")
        except (OSError, ValueError):
            return _failure(path, "cannot open batch file")
        try:
            with os.fdopen(fd, "rb") as handle:
                status: os.stat_result = os.fstat(handle.fileno())
                if not stat.S_ISREG(status.st_mode):
                    return _failure(path, "batch path is not a regular file")
                if status.st_size > _MAX_BYTES:
                    return _failure(path, "batch file exceeds 16 MiB")
                raw = handle.read(_MAX_BYTES + 1)
        except (OSError, ValueError):
            return _failure(path, "cannot read batch file")
    except (FileNotFoundError, NotADirectoryError):
        return _failure(path, "batch file not found")
    except IsADirectoryError:
        return _failure(path, "batch path is not a regular file")
    except OSError:
        return _failure(path, "cannot read batch file")
    if len(raw) > _MAX_BYTES:
        return _failure(path, "batch file exceeds 16 MiB")
    try:
        text: str = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _failure(path, "batch file is not valid UTF-8")
    return parse_batch_urls(text, comment_prefixes)
