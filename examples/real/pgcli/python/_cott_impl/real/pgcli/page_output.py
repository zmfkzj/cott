import shlex
import subprocess
import sys

from cott_runtime import UNIT, Err, Ok, Result, Unit
from real.pgcli_types import ClientError, ClientError_PagerFailed, PagerRequest


def _write_stdout(text: str) -> Result[Unit, ClientError]:
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except OSError as exc:
        return Err(error=ClientError_PagerFailed(message=f"cannot write output: {exc.strerror or exc}"))
    return Ok(value=UNIT)


def page_output(request: PagerRequest) -> Result[Unit, ClientError]:
    if not request.enabled:
        return _write_stdout(request.text)
    height = request.terminal_height
    if height > 0 and len(request.text.splitlines()) < height:
        return _write_stdout(request.text)
    try:
        argv = shlex.split(request.pager)
    except ValueError as exc:
        return Err(error=ClientError_PagerFailed(message=f"invalid pager command: {exc}"))
    if not argv:
        return Err(error=ClientError_PagerFailed(message="pager command is empty"))
    try:
        completed = subprocess.run(argv, input=request.text, text=True, check=False)
    except OSError as exc:
        return Err(error=ClientError_PagerFailed(message=f"cannot start pager: {exc.strerror or exc}"))
    if completed.returncode != 0:
        return Err(error=ClientError_PagerFailed(message=f"pager exited with status {completed.returncode}"))
    return Ok(value=UNIT)
