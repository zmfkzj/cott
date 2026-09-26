import contextlib
import os
import pathlib
import tempfile

from cott_runtime import U64, CottContractViolation, Err, Ok, Result, _cott_fixture_replace
from real.harlequin.files_types import FileError, FileError_Failed, FileError_IsADirectory, FileError_PermissionDenied


def _map_os_error(path: pathlib.Path, error: OSError) -> Err[FileError]:
    if isinstance(error, IsADirectoryError):
        return Err(error=FileError_IsADirectory(path=path))
    if isinstance(error, PermissionError):
        return Err(error=FileError_PermissionDenied(path=path))
    message = error.strerror if error.strerror else str(error)
    return Err(error=FileError_Failed(path=path, message=message))


def _remove_temp(temp_name: str | None) -> None:
    if temp_name is not None:
        with contextlib.suppress(OSError):
            os.unlink(temp_name)


def _save_host(path: pathlib.Path, data: bytes) -> Result[U64, FileError]:
    temp_name: str | None = None
    try:
        if path.is_dir():
            return Err(error=FileError_IsADirectory(path=path))
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(".tmp", "." + path.name + ".", str(parent))
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    except OSError as error:
        return _map_os_error(path, error)
    finally:
        _remove_temp(temp_name)
    return Ok(value=len(data))


def save_text_file(path: pathlib.Path, text: str) -> Result[U64, FileError]:
    data = text.encode("utf-8")
    try:
        _cott_fixture_replace(path, data)
    except CottContractViolation as violation:
        if violation.message == "fixture adapters are inactive":
            return _save_host(path, data)
        cause = violation.__cause__
        if isinstance(cause, OSError):
            return _map_os_error(path, cause)
        return Err(error=FileError_Failed(path=path, message=violation.message))
    except OSError as error:
        return _map_os_error(path, error)
    return Ok(value=len(data))
