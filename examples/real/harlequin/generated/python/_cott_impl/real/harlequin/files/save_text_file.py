import os
import pathlib
import tempfile

from cott_runtime import CottContractViolation, Err, Ok, Result, U64, _cott_fixture_replace
from real.harlequin.files_types import FileError, FileError_Failed, FileError_IsADirectory, FileError_PermissionDenied


def _map_os_error(path: pathlib.Path, error: OSError) -> Err[FileError]:
    if isinstance(error, IsADirectoryError):
        return Err(error=FileError_IsADirectory(path=path))
    if isinstance(error, PermissionError):
        return Err(error=FileError_PermissionDenied(path=path))
    return Err(error=FileError_Failed(path=path, message=error.strerror or str(error)))


def _discard_temp(name: str) -> None:
    try:
        os.unlink(name)
    except OSError:
        return


def _save_host(path: pathlib.Path, data: bytes) -> Result[U64, FileError]:
    temp_name: str | None = None
    try:
        if path.is_dir():
            return Err(error=FileError_IsADirectory(path=path))
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".harlequin-", suffix=".tmp", dir=parent, delete=False) as handle:
            temp_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    except OSError as error:
        return _map_os_error(path, error)
    except ValueError as error:
        return Err(error=FileError_Failed(path=path, message=str(error)))
    finally:
        if temp_name is not None:
            _discard_temp(temp_name)
    return Ok(value=len(data))


def save_text_file(path: pathlib.Path, text: str) -> Result[U64, FileError]:
    try:
        data = text.encode("utf-8")
    except UnicodeError as error:
        return Err(error=FileError_Failed(path=path, message=str(error)))
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
