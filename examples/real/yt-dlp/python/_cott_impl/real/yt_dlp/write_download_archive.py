import os
import secrets
import stat
from pathlib import Path
from typing import Final

from cott_runtime import UNIT, CottList, Err, Ok, Result, Unit
from real.yt_dlp_types import MediaError, MediaError_ArchiveFailure, MediaItem

_MAX_ITEMS: Final[int] = 100000
_MAX_BYTES: Final[int] = 16777216


def _fail(path: Path, message: str) -> Result[Unit, MediaError]:
    return Err(error=MediaError_ArchiveFailure(path=path, message=message))


def _platform_safe() -> bool:
    if os.name != "posix":
        return False
    return (
        os.O_NOFOLLOW != 0
        and os.O_DIRECTORY != 0
        and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.rename in os.supports_dir_fd
        and os.unlink in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
    )


def _encode(items: CottList[MediaItem]) -> bytes | None:
    if len(items) > _MAX_ITEMS:
        return None
    out = bytearray()
    for item in items:
        ident: str = item.id
        if ident == "" or ident != ident.strip() or "\r" in ident or "\n" in ident:
            return None
        try:
            encoded = ident.encode("utf-8")
        except UnicodeEncodeError:
            return None
        out.extend(encoded)
        out.extend(b"\n")
        if len(out) > _MAX_BYTES:
            return None
    return bytes(out)


def _close(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _open_parent(path: Path) -> int | None:
    parts = path.parts[:-1]
    start = "/" if path.is_absolute() else "."
    components = parts[1:] if path.is_absolute() else parts
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        dfd = os.open(start, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return None
    for component in components:
        try:
            next_fd = os.open(component, flags, dir_fd=dfd)
        except OSError:
            _close(dfd)
            return None
        if not _close(dfd):
            _close(next_fd)
            return None
        dfd = next_fd
    return dfd


def _write_all(fd: int, data: bytes) -> bool:
    view = memoryview(data)
    try:
        while view:
            written = os.write(fd, view)
            if written <= 0:
                return False
            view = view[written:]
    except OSError:
        return False
    return True


def _leaf_ok(dfd: int, name: str) -> bool | None:
    try:
        current = os.stat(name, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    except OSError:
        return None
    return stat.S_ISREG(current.st_mode)


def _publish(dfd: int, name: str, data: bytes, path: Path) -> Result[Unit, MediaError]:
    initial = _leaf_ok(dfd, name)
    if initial is None:
        return _fail(path, "cannot inspect archive target")
    if not initial:
        return _fail(path, "archive target is not a regular file")
    temp_name = f".{name}.archive-{secrets.token_hex(16)}"
    try:
        fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dfd)
    except OSError:
        return _fail(path, "cannot create temporary archive file")
    committed = False
    outcome: Result[Unit, MediaError] = Ok(value=UNIT)
    try:
        if not _write_all(fd, data):
            outcome = _fail(path, "cannot write temporary archive file")
        else:
            try:
                os.fchmod(fd, 0o600)
                os.fsync(fd)
                flushed = True
            except OSError:
                flushed = False
            if not flushed:
                outcome = _fail(path, "cannot flush temporary archive file")
            elif _leaf_ok(dfd, name) is not True:
                outcome = _fail(path, "archive target changed during write")
            else:
                try:
                    os.replace(temp_name, name, src_dir_fd=dfd, dst_dir_fd=dfd)
                    committed = True
                except OSError:
                    outcome = _fail(path, "atomic archive replacement failed")
    finally:
        try:
            os.close(fd)
        except OSError:
            if not committed:
                outcome = _fail(path, "cannot close temporary archive file")
        if not committed:
            try:
                os.unlink(temp_name, dir_fd=dfd)
            except OSError:
                outcome = _fail(path, "cannot clean up temporary archive file")
    if committed:
        try:
            os.fsync(dfd)
        except OSError:
            return _fail(path, "archive directory fsync failed")
    return outcome


def write_download_archive(path: Path, items: CottList[MediaItem]) -> Result[Unit, MediaError]:
    data = _encode(items)
    if data is None:
        return _fail(path, "invalid archive entries or size limit exceeded")
    target = Path(path)
    shown = str(target)
    name = target.name
    if shown in ("", ".", "/") or name in ("", ".", "..") or "\x00" in shown:
        return _fail(path, "invalid archive path")
    if not _platform_safe():
        return _fail(path, "platform lacks safe filesystem primitives")
    dfd = _open_parent(target)
    if dfd is None:
        return _fail(path, "unsafe or inaccessible archive directory")
    try:
        outcome = _publish(dfd, name, data, path)
    finally:
        closed = _close(dfd)
    if not closed:
        return _fail(path, "cannot close archive directory")
    return outcome
