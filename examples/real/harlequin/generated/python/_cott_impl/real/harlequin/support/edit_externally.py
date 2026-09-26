import os
import subprocess
import tempfile

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.support_types import ExternalEdit, ExternalEditorError, ExternalEditorError_Failed


def _failed(reason: str) -> Result[ExternalEdit, ExternalEditorError]:
    return Err(error=ExternalEditorError_Failed(message=f"Harlequin could not run your editor. {reason}"))


def _remove(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        return


def edit_externally(text: str, command: CottList[str]) -> Result[ExternalEdit, ExternalEditorError]:
    path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".sql", delete=False) as handle:
            path = handle.name
            handle.write(text)
        args: list[str] = [part for part in command]
        args.append(path)
        completed: subprocess.CompletedProcess[bytes] = subprocess.run(args)
        status = completed.returncode
        if status != 0:
            return Ok(value=ExternalEdit(text=Nothing(), returncode=status))
        with open(path, "r", encoding="utf-8", newline=None) as source:
            contents = source.read()
        return Ok(value=ExternalEdit(text=Some(value=contents), returncode=0))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return _failed(str(error))
    finally:
        if path is not None:
            _remove(path)
