import subprocess
import sys
from typing import IO

from cott_runtime import UNIT, Err, Ok, Result, Unit
from real.pgcli_types import ClientError, ClientError_PagerFailed, PagerRequest


def _fail(message: str) -> Result[Unit, ClientError]:
    return Err(error=ClientError_PagerFailed(message=message))


def _write_stdout(data: str) -> Result[Unit, ClientError]:
    offset = 0
    total = len(data)
    try:
        while offset < total:
            written = sys.stdout.write(data[offset:])
            if written <= 0:
                return _fail("cannot write output")
            offset += written
        sys.stdout.flush()
    except (OSError, ValueError):
        return _fail("cannot write output")
    return Ok(value=UNIT)


def _reap(process: subprocess.Popen[str]) -> Result[Unit, ClientError]:
    try:
        process.wait()
    except (OSError, subprocess.SubprocessError):
        return _fail("pager failed")
    return _fail("pager failed")


def _abort(process: subprocess.Popen[str]) -> Result[Unit, ClientError]:
    try:
        process.kill()
    except OSError:
        return _reap(process)
    return _reap(process)


def _ignore_close_error(stdin: IO[str]) -> None:
    try:
        stdin.close()
    except (OSError, ValueError):
        return

def _feed_and_close(stdin: IO[str], data: str) -> bool:
    offset = 0
    total = len(data)
    try:
        while offset < total:
            written = stdin.write(data[offset:])
            if written <= 0:
                return False
            offset += written
        stdin.flush()
        stdin.close()
    except BrokenPipeError:
        _ignore_close_error(stdin)
        return True
    except (OSError, ValueError):
        return False
    return True


def page_output(request: PagerRequest) -> Result[Unit, ClientError]:
    data = request.text + "\n"
    if not request.enabled or len(request.text.splitlines()) <= request.terminal_height:
        return _write_stdout(data)
    argv = request.pager.split()
    if not argv:
        return _fail("cannot start pager")
    try:
        process: subprocess.Popen[str] = subprocess.Popen(argv, stdin=subprocess.PIPE, text=True)
    except (OSError, ValueError):
        return _fail("cannot start pager")
    stdin = process.stdin
    if stdin is None:
        return _abort(process)
    if not _feed_and_close(stdin, data):
        return _abort(process)
    try:
        status = process.wait()
    except (OSError, subprocess.SubprocessError):
        return _fail("pager failed")
    if status != 0:
        return _fail("pager failed")
    return Ok(value=UNIT)
