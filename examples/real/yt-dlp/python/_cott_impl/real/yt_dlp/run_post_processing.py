import os
import shutil
import stat
import subprocess
from pathlib import Path

import cott_runtime
from cott_runtime import UNIT, CottList, Result, Unit
from real.yt_dlp_types import ExternalToolRequest, MediaError, MediaError_ExternalToolMissing, MediaError_PostProcessFailed


def _is_regular(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.stat().st_mode)
    except (OSError, ValueError):
        return False


def _resolve_executable(executable: str) -> str | None:
    if not executable or "\x00" in executable:
        return None
    try:
        if os.sep in executable or (os.altsep is not None and os.altsep in executable):
            candidate: str = executable
        else:
            found: str | None = shutil.which(executable)
            if found is None:
                return None
            candidate = found
        if not _is_regular(Path(candidate)) or not os.access(candidate, os.X_OK):
            return None
        return candidate
    except (OSError, ValueError):
        return None


def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    for request in requests:
        name: str = request.executable
        executable: str | None = _resolve_executable(name)
        if executable is None:
            return cott_runtime.Err(error=MediaError_ExternalToolMissing(name=name))
        if not _is_regular(request.input):
            return cott_runtime.Err(error=MediaError_PostProcessFailed(name=name, message="input file is missing or not a regular file"))
        command: list[str] = [executable]
        for argument in request.arguments:
            command.append(argument)
        timeout: float | None = request.timeout_ms / 1000.0 if request.timeout_ms else None
        try:
            completed: subprocess.CompletedProcess[bytes] = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return cott_runtime.Err(error=MediaError_PostProcessFailed(name=name, message="tool timed out"))
        except (FileNotFoundError, PermissionError):
            return cott_runtime.Err(error=MediaError_ExternalToolMissing(name=name))
        except (OSError, ValueError, subprocess.SubprocessError):
            return cott_runtime.Err(error=MediaError_PostProcessFailed(name=name, message="tool could not be started"))
        if completed.returncode != 0:
            return cott_runtime.Err(error=MediaError_PostProcessFailed(name=name, message="tool exited with nonzero status"))
        try:
            produced: bool = os.path.lexists(request.output)
        except (OSError, ValueError):
            produced = False
        if not produced:
            return cott_runtime.Err(error=MediaError_PostProcessFailed(name=name, message="tool did not produce output"))
    return cott_runtime.Ok(value=UNIT)
