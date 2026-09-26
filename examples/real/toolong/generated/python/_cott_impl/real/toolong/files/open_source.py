import bz2
import gzip
import os
import pathlib
import tempfile
from typing import Final

from cott_runtime import CottContractViolation, Err, Nothing, Ok, Result, Some
from cott_runtime import _cott_fixture_read
from real.toolong.files import decompress, detect_compression
from real.toolong.files_types import SourceError, SourceError_NotFound, SourceError_OpenFailed
from real.toolong.model_types import Compression, Compression_Gzip, Compression_Uncompressed, LogSource

_CHUNK: Final[int] = 262144
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _fail(name: str, error: BaseException) -> Result[LogSource, SourceError]:
    if isinstance(error, FileNotFoundError):
        return Err(error=SourceError_NotFound(name=name, message=str(error)))
    return Err(error=SourceError_OpenFailed(name=name, message=str(error)))


def _copy_to_temp(stream: gzip.GzipFile | bz2.BZ2File) -> tuple[int, int]:
    size = 0
    temp = tempfile.TemporaryFile()
    try:
        while True:
            chunk = stream.read(_CHUNK)
            if not chunk:
                break
            temp.write(chunk)
            size += len(chunk)
        temp.flush()
        fd = os.dup(temp.fileno())
    finally:
        temp.close()
    return fd, size


def _open_plain(path: pathlib.Path) -> tuple[int, int]:
    fd = os.open(path, os.O_RDONLY)
    try:
        size = os.lseek(fd, 0, os.SEEK_END)
    except BaseException:
        os.close(fd)
        raise
    return fd, size


def _open_host(path: pathlib.Path, name: str, compression: Compression) -> Result[LogSource, SourceError]:
    try:
        if isinstance(compression, Compression_Uncompressed):
            fd, size = _open_plain(path)
            return Ok(value=LogSource(path=path, name=name, compression=compression, descriptor=Some(value=fd), size=size, can_tail=True))
        if isinstance(compression, Compression_Gzip):
            with gzip.open(path, "rb") as gz_stream:
                fd, size = _copy_to_temp(gz_stream)
        else:
            with bz2.open(path, "rb") as bz_stream:
                fd, size = _copy_to_temp(bz_stream)
        return Ok(value=LogSource(path=path, name=name, compression=compression, descriptor=Some(value=fd), size=size, can_tail=False))
    except Exception as error:
        return _fail(name, error)


def open_source(path: pathlib.Path) -> Result[LogSource, SourceError]:
    name = pathlib.Path(path).name
    compression = detect_compression(name)
    try:
        data = _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message == _INACTIVE:
            return _open_host(path, name, compression)
        cause = violation.__cause__
        if isinstance(cause, OSError):
            return _fail(name, cause)
        return _fail(name, violation)
    except OSError as error:
        return _fail(name, error)
    if isinstance(compression, Compression_Uncompressed):
        content = data
    else:
        result = decompress(data, compression)
        if isinstance(result, Err):
            return Err(error=SourceError_OpenFailed(name=name, message=result.error.message))
        else:
            content = result.value
    can_tail = isinstance(compression, Compression_Uncompressed)
    return Ok(value=LogSource(path=path, name=name, compression=compression, descriptor=Nothing(), size=len(content), can_tail=can_tail))
