import errno
import os
import re
import stat
from pathlib import Path
from typing import Final

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Err, Result
from real.yt_dlp_types import ArchiveRequest, MediaError, MediaError_ArchiveFailure

_MAX_ENTRIES: Final[int] = 100000
_MAX_BYTES: Final[int] = 16777216
_CHUNK: Final[int] = 65536


def _failure(request: ArchiveRequest, message: str) -> MediaError:
    return MediaError_ArchiveFailure(path=request.path, message=message)


def _io_failure(request: ArchiveRequest, error: OSError) -> MediaError:
    if error.errno == errno.ENOENT:
        return _failure(request, "download archive does not exist")
    if error.errno in (errno.ELOOP, errno.ENOTDIR):
        return _failure(request, "download archive path contains a symlink or non-directory")
    if error.errno == errno.EISDIR:
        return _failure(request, "download archive is not a regular file")
    return _failure(request, "cannot read download archive")


def _close(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _open_host(request: ArchiveRequest) -> Result[int, MediaError]:
    if os.name != "posix" or os.open not in os.supports_dir_fd:
        return cott_runtime.Err(error=_failure(request, "platform lacks no-follow directory-fd operations"))
    path: Path = request.path
    name: str = path.name
    if name in ("", ".", "..") or "\x00" in str(path):
        return cott_runtime.Err(error=_failure(request, "invalid download archive path"))
    components: tuple[str, ...] = path.parts[1:-1] if path.is_absolute() else path.parts[:-1]
    dir_flags: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        dfd: int = os.open("/" if path.is_absolute() else ".", dir_flags)
    except OSError as base_error:
        return cott_runtime.Err(error=_io_failure(request, base_error))
    for component in components:
        try:
            next_fd: int = os.open(component, dir_flags, dir_fd=dfd)
        except OSError as parent_error:
            closed: bool = _close(dfd)
            if not closed:
                return cott_runtime.Err(error=_failure(request, "cannot close download archive directory"))
            return cott_runtime.Err(error=_io_failure(request, parent_error))
        if not _close(dfd):
            _close(next_fd)
            return cott_runtime.Err(error=_failure(request, "cannot close download archive directory"))
        dfd = next_fd
    try:
        fd: int = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dfd)
    except OSError as leaf_error:
        if not _close(dfd):
            return cott_runtime.Err(error=_failure(request, "cannot close download archive directory"))
        return cott_runtime.Err(error=_io_failure(request, leaf_error))
    if not _close(dfd):
        _close(fd)
        return cott_runtime.Err(error=_failure(request, "cannot close download archive directory"))
    return cott_runtime.Ok(value=fd)


def _read_bounded(request: ArchiveRequest, fd: int) -> Result[bytes, MediaError]:
    try:
        info: os.stat_result = os.fstat(fd)
    except OSError:
        return cott_runtime.Err(error=_failure(request, "cannot inspect download archive"))
    if not stat.S_ISREG(info.st_mode):
        return cott_runtime.Err(error=_failure(request, "download archive is not a regular file"))
    if info.st_size > _MAX_BYTES:
        return cott_runtime.Err(error=_failure(request, "download archive exceeds size limit"))
    buffer: bytearray = bytearray()
    while True:
        try:
            chunk: bytes = os.read(fd, min(_CHUNK, _MAX_BYTES + 1 - len(buffer)))
        except OSError:
            return cott_runtime.Err(error=_failure(request, "cannot read download archive"))
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > _MAX_BYTES:
            return cott_runtime.Err(error=_failure(request, "download archive exceeds size limit"))
    return cott_runtime.Ok(value=bytes(buffer))


def _parse_archive(request: ArchiveRequest, data: bytes) -> Result[CottList[str], MediaError]:
    if len(data) > _MAX_BYTES:
        return cott_runtime.Err(error=_failure(request, "download archive exceeds size limit"))
    try:
        text: str = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return cott_runtime.Err(error=_failure(request, "download archive is not valid UTF-8"))
    entries: list[str] = []
    for raw_line in re.split(r"\r\n?|\n", text):
        line: str = raw_line.strip()
        if line == "":
            continue
        if len(entries) >= _MAX_ENTRIES:
            return cott_runtime.Err(error=_failure(request, "download archive exceeds entry limit"))
        entries.append(line)
    return cott_runtime.Ok(value=CottList(values=entries))


def _read_host(request: ArchiveRequest) -> Result[CottList[str], MediaError]:
    opened: Result[int, MediaError] = _open_host(request)
    if isinstance(opened, Err):
        return cott_runtime.Err(error=opened.error)
    fd: int = opened.value
    read_result: Result[bytes, MediaError] = _read_bounded(request, fd)
    closed: bool = _close(fd)
    if not closed:
        return cott_runtime.Err(error=_failure(request, "cannot close download archive"))
    if isinstance(read_result, Err):
        return cott_runtime.Err(error=read_result.error)
    return _parse_archive(request, read_result.value)


def read_download_archive(request: ArchiveRequest) -> Result[CottList[str], MediaError]:
    try:
        data: bytes = cott_runtime._cott_fixture_read(request.path)
    except CottContractViolation as fixture_error:
        if fixture_error.message == "fixture adapters are inactive":
            return _read_host(request)
        cause: BaseException | None = fixture_error.__cause__
        if isinstance(cause, OSError):
            return cott_runtime.Err(error=_io_failure(request, cause))
        return cott_runtime.Err(error=_failure(request, "cannot read download archive"))
    except OSError as read_error:
        return cott_runtime.Err(error=_io_failure(request, read_error))
    return _parse_archive(request, data)
