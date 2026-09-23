import os
import shutil
import subprocess
from pathlib import Path

from cott_runtime import UNIT, CottList, Err, Ok, Result, Unit
from real.yt_dlp_types import ExternalToolRequest, MediaError, MediaError_ExternalToolMissing, MediaError_PostProcessFailed


def _resolve_executable(executable: str) -> str | None:
    if executable.strip() == "" or "\x00" in executable:
        return None
    if os.sep in executable or (os.altsep is not None and os.altsep in executable):
        candidate = Path(executable)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
        return None
    return shutil.which(executable)


def _run_one(request: ExternalToolRequest) -> Result[Unit, MediaError]:
    name = request.executable
    resolved = _resolve_executable(name)
    if resolved is None:
        return Err(error=MediaError_ExternalToolMissing(name=name))
    input_path = Path(request.input)
    output_path = Path(request.output)
    if not input_path.is_file():
        return Err(error=MediaError_PostProcessFailed(name=name, message=f"input is not a readable file: {input_path}"))
    command: list[str] = [resolved]
    for argument in request.arguments:
        command.append(argument)
    timeout: float | None = request.timeout_ms / 1000.0 if request.timeout_ms > 0 else None
    try:
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False, shell=False)
    except subprocess.TimeoutExpired:
        return Err(error=MediaError_PostProcessFailed(name=name, message=f"timed out after {request.timeout_ms} ms"))
    except FileNotFoundError:
        return Err(error=MediaError_ExternalToolMissing(name=name))
    except OSError:
        return Err(error=MediaError_PostProcessFailed(name=name, message="failed to start tool"))
    if completed.returncode != 0:
        return Err(error=MediaError_PostProcessFailed(name=name, message=f"exited with status {completed.returncode}"))
    if not output_path.exists():
        return Err(error=MediaError_PostProcessFailed(name=name, message=f"output was not produced: {output_path}"))
    return Ok(value=UNIT)


def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    for request in requests:
        outcome = _run_one(request)
        if isinstance(outcome, Err):
            return outcome
    return Ok(value=UNIT)
