import errno
import pathlib
from typing import Final

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_read
from real.harlequin.files_types import FileError, FileError_Failed, FileError_InvalidEncoding, FileError_IsADirectory, FileError_NotFound, FileError_PermissionDenied

_INACTIVE: Final[str] = "fixture adapters are inactive"


def _map_os_error(path: pathlib.Path, error: OSError) -> Err[FileError]:
    if isinstance(error, FileNotFoundError) or error.errno == errno.ENOENT:
        return Err(error=FileError_NotFound(path=path))
    if isinstance(error, IsADirectoryError) or error.errno == errno.EISDIR:
        return Err(error=FileError_IsADirectory(path=path))
    if isinstance(error, PermissionError) or error.errno in (errno.EACCES, errno.EPERM):
        return Err(error=FileError_PermissionDenied(path=path))
    message = error.strerror if error.strerror else str(error)
    return Err(error=FileError_Failed(path=path, message=message))


def _decode(path: pathlib.Path, data: bytes) -> Result[str, FileError]:
    try:
        return Ok(value=data.decode("utf-8"))
    except UnicodeDecodeError:
        return Err(error=FileError_InvalidEncoding(path=path))


def load_text_file(path: pathlib.Path) -> Result[str, FileError]:
    try:
        data = _cott_fixture_read(path)
    except CottContractViolation as violation:
        cause = violation.__cause__
        if isinstance(cause, OSError):
            return _map_os_error(path, cause)
        if violation.message != _INACTIVE:
            return Err(error=FileError_Failed(path=path, message=violation.message))
        try:
            data = path.read_bytes()
        except OSError as error:
            return _map_os_error(path, error)
    except OSError as error:
        return _map_os_error(path, error)
    return _decode(path, data)
