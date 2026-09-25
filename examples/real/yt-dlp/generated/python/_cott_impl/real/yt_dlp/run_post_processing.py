import os
import shutil
import stat
import subprocess
from pathlib import Path

from cott_runtime import UNIT, CottList, Err, Ok, Result, Unit
from real.yt_dlp_types import ExternalToolRequest, MediaError, MediaError_ExternalToolMissing, MediaError_PostProcessFailed


def _is_regular(path: Path) -> bool:
    try:
        return stat.S_ISREG(os.stat(path).st_mode)
    except (OSError, ValueError):
        return False


def _has_separator(executable: str) -> bool:
    return os.sep in executable or (os.altsep is not None and os.altsep in executable)


def _resolve_executable(executable: str) -> str | None:
    if executable == "" or "\x00" in executable:
        return None
    if _has_separator(executable):
        if _is_regular(Path(executable)) and os.access(executable, os.X_OK):
            return executable
        return None
    found: str | None = shutil.which(executable)
    if found is None or not _is_regular(Path(found)) or not os.access(found, os.X_OK):
        return None
    return found


def _run_one(request: ExternalToolRequest) -> Result[Unit, MediaError]:
    name: str = request.executable
    resolved: str | None = _resolve_executable(name)
    if resolved is None:
        return Err(error=MediaError_ExternalToolMissing(name=name))
    if not _is_regular(Path(request.input)):
        return Err(error=MediaError_PostProcessFailed(name=name, message="input file is missing or not a regular file"))
    command: list[str] = [resolved]
    for argument in request.arguments:
        command.append(argument)
    timeout: float | None = request.timeout_ms / 1000.0 if request.timeout_ms > 0 else None
    try:
        completed: subprocess.CompletedProcess[bytes] = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False, shell=False)
    except subprocess.TimeoutExpired:
        return Err(error=MediaError_PostProcessFailed(name=name, message="tool timed out"))
    except (FileNotFoundError, PermissionError):
        return Err(error=MediaError_ExternalToolMissing(name=name))
    except (OSError, ValueError, subprocess.SubprocessError):
        return Err(error=MediaError_PostProcessFailed(name=name, message="tool could not be started"))
    if completed.returncode != 0:
        return Err(error=MediaError_PostProcessFailed(name=name, message="tool exited with nonzero status"))
    try:
        produced: bool = os.path.lexists(Path(request.output))
    except (OSError, ValueError):
        produced = False
    if not produced:
        return Err(error=MediaError_PostProcessFailed(name=name, message="tool did not produce output"))
    return Ok(value=UNIT)


def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    for request in requests:
        outcome: Result[Unit, MediaError] = _run_one(request)
        match outcome:
            case Err(error=failure):
                return Err(error=failure)
            case Ok():
                continue
    return Ok(value=UNIT)
