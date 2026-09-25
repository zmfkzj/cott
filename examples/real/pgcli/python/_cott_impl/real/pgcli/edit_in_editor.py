import os
import pathlib
import subprocess

import cott_runtime
from cott_runtime import Result
from real.pgcli_types import ClientError, ClientError_EditorFailed, EditorRequest, InputBuffer


def _fail(message: str) -> Result[InputBuffer, ClientError]:
    return cott_runtime.Err(error=ClientError_EditorFailed(message=message))


def _remove_quietly(path: pathlib.Path) -> bool:
    try:
        os.remove(path)
    except OSError:
        return False
    return True


def _run(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    path = request.temporary_path
    command = request.editor.split()
    if not command:
        return _fail("no editor configured")
    try:
        data = request.buffer.text.encode("utf-8")
        with open(path, "wb") as handle:
            handle.write(data)
    except (OSError, UnicodeEncodeError):
        return _fail("cannot write temporary file")
    try:
        completed: subprocess.CompletedProcess[bytes] = subprocess.run([*command, os.fspath(path)], check=False)
    except (OSError, ValueError):
        return _fail("cannot launch editor")
    if completed.returncode != 0:
        return _fail("editor failed")
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError:
        return _fail("cannot read temporary file")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _fail("cannot decode temporary file")
    if text.endswith("\n"):
        text = text[:-1]
    if not _remove_quietly(path):
        return _fail("cannot remove temporary file")
    return cott_runtime.Ok(value=InputBuffer(text=text, cursor=len(text), multiline=request.buffer.multiline))


def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    try:
        return _run(request)
    finally:
        _remove_quietly(request.temporary_path)
