import os
import secrets
import stat
from pathlib import Path
from typing import Final

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, UNIT, Unit
from real.yt_dlp_types import MediaError, MediaError_ArchiveFailure, MediaItem

_MAX_ITEMS: Final[int] = 100000
_MAX_BYTES: Final[int] = 16777216


def _archive_error(path: Path, message: str) -> MediaError:
    return MediaError_ArchiveFailure(path=path, message=message)


def _encode_archive(path: Path, items: CottList[MediaItem]) -> Result[bytes, MediaError]:
    if len(items) > _MAX_ITEMS:
        return Err(error=_archive_error(path, "archive has too many entries"))
    data = bytearray()
    for item in items:
        identifier: str = item.id
        if not identifier or identifier != identifier.strip() or "\r" in identifier or "\n" in identifier:
            return Err(error=_archive_error(path, "invalid archive identifier"))
        if len(data) + len(identifier) + 1 > _MAX_BYTES:
            return Err(error=_archive_error(path, "archive exceeds size limit"))
        try:
            encoded: bytes = identifier.encode("utf-8")
        except UnicodeEncodeError:
            return Err(error=_archive_error(path, "archive identifier is not valid UTF-8"))
        if len(data) + len(encoded) + 1 > _MAX_BYTES:
            return Err(error=_archive_error(path, "archive exceeds size limit"))
        data.extend(encoded)
        data.append(10)
    return Ok(value=bytes(data))


def _safe_archive_platform() -> bool:
    try:
        return (
            os.name == "posix"
            and bool(os.O_NOFOLLOW)
            and bool(os.O_DIRECTORY)
            and bool(os.O_CLOEXEC)
            and os.open in os.supports_dir_fd
            and os.stat in os.supports_dir_fd
            and os.stat in os.supports_follow_symlinks
            and os.rename in os.supports_dir_fd
            and os.unlink in os.supports_dir_fd
            and os.fchmod is not None
            and os.fsync is not None
        )
    except (AttributeError, TypeError):
        return False


def _close_archive_fd(fd: int) -> bool:
    try:
        os.close(fd)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return False
    return True


def _open_archive_parent(path: Path) -> Result[int, MediaError]:
    flags: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        directory: int = os.open("/" if path.is_absolute() else ".", flags)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return Err(error=_archive_error(path, "cannot open archive base directory"))
    components: tuple[str, ...] = path.parts[1:-1] if path.is_absolute() else path.parts[:-1]
    for component in components:
        try:
            child: int = os.open(component, flags, dir_fd=directory)
        except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
            if not _close_archive_fd(directory):
                return Err(error=_archive_error(path, "cannot close archive parent directory"))
            return Err(error=_archive_error(path, "unsafe or inaccessible archive parent directory"))
        if not _close_archive_fd(directory):
            _close_archive_fd(child)
            return Err(error=_archive_error(path, "cannot close archive parent directory"))
        directory = child
    return Ok(value=directory)


def _archive_leaf_identity(directory: int, name: str, path: Path) -> Result[tuple[int, int, int, int, int] | None, MediaError]:
    try:
        info: os.stat_result = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return Ok(value=None)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return Err(error=_archive_error(path, "cannot inspect archive leaf"))
    if not stat.S_ISREG(info.st_mode):
        return Err(error=_archive_error(path, "archive leaf is not a regular file"))
    return Ok(value=(info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))


def _write_archive_bytes(fd: int, data: bytes) -> bool:
    view: memoryview = memoryview(data)
    offset: int = 0
    while offset < len(view):
        try:
            written: int = os.write(fd, view[offset:])
        except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
            return False
        if written <= 0:
            return False
        offset += written
    return True


def _abort_archive(directory: int, temp_name: str, path: Path, error: MediaError) -> Result[Unit, MediaError]:
    try:
        os.unlink(temp_name, dir_fd=directory)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return Err(error=_archive_error(path, "cannot clean up temporary archive file"))
    return Err(error=error)


def _publish_archive(directory: int, name: str, data: bytes, path: Path) -> Result[Unit, MediaError]:
    initial: Result[tuple[int, int, int, int, int] | None, MediaError] = _archive_leaf_identity(directory, name, path)
    if isinstance(initial, Err):
        return Err(error=initial.error)
    try:
        temp_name: str = ".archive-" + secrets.token_hex(16)
        fd: int = os.open(
            temp_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=directory,
        )
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return Err(error=_archive_error(path, "cannot create temporary archive file"))

    failure: MediaError | None = None
    temp_identity: tuple[int, int, int, int, int] | None = None
    try:
        if not _write_archive_bytes(fd, data):
            failure = _archive_error(path, "cannot write temporary archive file")
        else:
            os.fchmod(fd, 0o600)
            os.fsync(fd)
            info: os.stat_result = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size != len(data):
                failure = _archive_error(path, "temporary archive file is incomplete or not regular")
            else:
                temp_identity = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        failure = _archive_error(path, "cannot set mode or sync temporary archive file")
    if not _close_archive_fd(fd):
        failure = _archive_error(path, "cannot close temporary archive file")
    if failure is not None:
        return _abort_archive(directory, temp_name, path, failure)

    staged: Result[tuple[int, int, int, int, int] | None, MediaError] = _archive_leaf_identity(directory, temp_name, path)
    if isinstance(staged, Err):
        return _abort_archive(directory, temp_name, path, staged.error)
    current: Result[tuple[int, int, int, int, int] | None, MediaError] = _archive_leaf_identity(directory, name, path)
    if isinstance(current, Err):
        return _abort_archive(directory, temp_name, path, current.error)
    if staged.value != temp_identity or current.value != initial.value:
        return _abort_archive(directory, temp_name, path, _archive_error(path, "archive target or temporary file changed"))
    try:
        os.replace(temp_name, name, src_dir_fd=directory, dst_dir_fd=directory)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return _abort_archive(directory, temp_name, path, _archive_error(path, "cannot atomically replace archive"))
    try:
        os.fsync(directory)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return Err(error=_archive_error(path, "cannot sync archive parent directory"))
    return Ok(value=UNIT)


def _write_host_archive(path: Path, data: bytes) -> Result[Unit, MediaError]:
    if not _safe_archive_platform():
        return Err(error=_archive_error(path, "safe archive filesystem operations are unavailable"))
    opened: Result[int, MediaError] = _open_archive_parent(path)
    if isinstance(opened, Err):
        return Err(error=opened.error)
    directory: int = opened.value
    outcome: Result[Unit, MediaError] = _publish_archive(directory, path.name, data, path)
    if not _close_archive_fd(directory):
        return Err(error=_archive_error(path, "cannot close archive parent directory"))
    return outcome


def write_download_archive(path: Path, items: CottList[MediaItem]) -> Result[Unit, MediaError]:
    shown: str = str(path)
    if shown in ("", ".", "/") or path.name in ("", ".", "..") or "\x00" in shown or path.anchor not in ("", "/"):
        return Err(error=_archive_error(path, "invalid archive path"))
    encoded: Result[bytes, MediaError] = _encode_archive(path, items)
    if isinstance(encoded, Err):
        return Err(error=encoded.error)
    try:
        cott_runtime._cott_fixture_replace(path, encoded.value, create_parents=False)
    except CottContractViolation as violation:
        if violation.message == "fixture adapters are inactive":
            return _write_host_archive(path, encoded.value)
        return Err(error=_archive_error(path, "cannot publish archive in fixture"))
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return Err(error=_archive_error(path, "cannot publish archive in fixture"))
    return Ok(value=UNIT)
