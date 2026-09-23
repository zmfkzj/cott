import shlex
import subprocess

from cott_runtime import Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_EditorFailed, EditorRequest, InputBuffer


def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    path = request.temporary_path
    try:
        command = shlex.split(request.editor)
    except ValueError as error:
        return Err(error=ClientError_EditorFailed(message=f"invalid editor command: {error}"))
    if not command:
        return Err(error=ClientError_EditorFailed(message="no editor configured"))
    try:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(request.buffer.text)
    except (OSError, UnicodeEncodeError) as error:
        return Err(error=ClientError_EditorFailed(message=f"cannot write temporary file: {error}"))
    try:
        completed = subprocess.run([*command, str(path)], check=False)
    except (OSError, ValueError) as error:
        return Err(error=ClientError_EditorFailed(message=f"cannot launch editor: {error}"))
    if completed.returncode != 0:
        return Err(error=ClientError_EditorFailed(message=f"editor exited with status {completed.returncode}"))
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        return Err(error=ClientError_EditorFailed(message=f"cannot read temporary file: {error}"))
    return Ok(value=InputBuffer(text=text, cursor=len(text), multiline=request.buffer.multiline))
