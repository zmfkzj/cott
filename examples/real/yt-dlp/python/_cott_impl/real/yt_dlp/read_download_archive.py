import errno
import os
import stat
from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import ArchiveRequest, MediaError, MediaError_ArchiveFailure

_MAX_ENTRIES: Final[int] = 100000
_MAX_BYTES: Final[int] = 16777216
_CHUNK: Final[int] = 65536


def _failure(request: ArchiveRequest, message: str) -> Result[CottList[str], MediaError]:
    return Err(error=MediaError_ArchiveFailure(path=request.path, message=message))


def _open_error(request: ArchiveRequest, error: OSError, dir_closed: bool) -> MediaError:
    if not dir_closed:
        return MediaError_ArchiveFailure(path=request.path, message="cannot close archive directory")
    if error.errno == errno.ENOENT:
        return MediaError_ArchiveFailure(path=request.path, message="download archive does not exist")
    if error.errno in (errno.ELOOP, errno.ENOTDIR):
        return MediaError_ArchiveFailure(path=request.path, message="download archive path contains a symlink or non-directory")
    return MediaError_ArchiveFailure(path=request.path, message="cannot open download archive")


def _close(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _open_archive(request: ArchiveRequest) -> Result[int, MediaError]:
    if os.name != "posix" or os.open not in os.supports_dir_fd:
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="platform lacks no-follow directory-fd operations"))
    path: Path = Path(request.path)
    name: str = path.name
    if name in ("", ".", "..") or "\x00" in str(path):
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="invalid download archive path"))
    components: tuple[str, ...] = path.parts[1:-1] if path.is_absolute() else path.parts[:-1]
    dir_flags: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        dfd: int = os.open("/" if path.is_absolute() else ".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="cannot open base directory"))
    for component in components:
        try:
            next_fd: int = os.open(component, dir_flags, dir_fd=dfd)
        except OSError as dir_error:
            return Err(error=_open_error(request, dir_error, _close(dfd)))
        if not _close(dfd):
            _close(next_fd)
            return Err(error=MediaError_ArchiveFailure(path=request.path, message="cannot close archive directory"))
        dfd = next_fd
    try:
        fd: int = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dfd)
    except OSError as file_error:
        return Err(error=_open_error(request, file_error, _close(dfd)))
    if not _close(dfd):
        _close(fd)
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="cannot close archive directory"))
    return Ok(value=fd)


def _read_bounded(request: ArchiveRequest, fd: int) -> Result[bytes, MediaError]:
    try:
        info: os.stat_result = os.fstat(fd)
    except OSError:
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="cannot inspect download archive"))
    if not stat.S_ISREG(info.st_mode):
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="download archive is not a regular file"))
    if info.st_size > _MAX_BYTES:
        return Err(error=MediaError_ArchiveFailure(path=request.path, message="download archive exceeds size limit"))
    buffer: bytearray = bytearray()
    while True:
        try:
            chunk: bytes = os.read(fd, _CHUNK)
        except OSError:
            return Err(error=MediaError_ArchiveFailure(path=request.path, message="cannot read download archive"))
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > _MAX_BYTES:
            return Err(error=MediaError_ArchiveFailure(path=request.path, message="download archive exceeds size limit"))
    return Ok(value=bytes(buffer))


def read_download_archive(request: ArchiveRequest) -> Result[CottList[str], MediaError]:
    match _open_archive(request):
        case Err(error=open_failure):
            return Err(error=open_failure)
        case Ok(value=fd):
            read_result: Result[bytes, MediaError] = _read_bounded(request, fd)
    closed: bool = _close(fd)
    match read_result:
        case Err(error=read_failure):
            return Err(error=read_failure)
        case Ok(value=data):
            if not closed:
                return _failure(request, "cannot close download archive")
    try:
        text: str = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _failure(request, "download archive is not valid UTF-8")
    entries: list[str] = []
    for raw_line in text.splitlines():
        line: str = raw_line.strip()
        if line == "":
            continue
        if len(entries) >= _MAX_ENTRIES:
            return _failure(request, "download archive exceeds entry limit")
        entries.append(line)
    return Ok(value=CottList(values=entries))
