import errno
import hashlib
import http.client
import os
import secrets
import socket
import ssl
import stat
from pathlib import Path
from typing import Final
from urllib.parse import urljoin, urlsplit

from cott_runtime import UNIT, Err, Ok, Result, Unit
from real.yt_dlp import resolve_update_repository
from real.yt_dlp_types import MediaError, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_UpdateUnavailable, UpdateOutcome, UpdateOutcome_Available, UpdateOutcome_Current, UpdateOutcome_Disabled, UpdateOutcome_Installed, UpdatePolicy_Apply, UpdatePolicy_Check, UpdatePolicy_Master, UpdatePolicy_Never, UpdatePolicy_Nightly, UpdateRequest

_ASSET: Final[str] = "yt-dlp"
_MANIFEST: Final[str] = "SHA2-256SUMS"
_MANIFEST_CAP: Final[int] = 1048576
_ASSET_CAP: Final[int] = 67108864
_TIMEOUT: Final[float] = 30.0
_MAX_REDIRECTS: Final[int] = 5
_CHUNK: Final[int] = 65536
_HEAD: Final[int] = 512
_HOST_GITHUB: Final[str] = "github.com"
_HOST_ASSETS: Final[str] = "release-assets.githubusercontent.com"
_HEXDIGITS: Final[str] = "0123456789abcdefABCDEF"
_REPO_STABLE: Final[str] = "yt-dlp/yt-dlp"
_REPO_NIGHTLY: Final[str] = "yt-dlp/yt-dlp-nightly-builds"
_REPO_MASTER: Final[str] = "yt-dlp/yt-dlp-master-builds"


def _looks_html(head: bytes) -> bool:
    lowered: bytes = head.lstrip().lower()
    return lowered.startswith(b"<!doctype") or lowered.startswith(b"<html") or lowered.startswith(b"<head") or lowered.startswith(b"<body")


def _write_all(out_fd: int, chunk: bytes) -> bool:
    view: memoryview = memoryview(chunk)
    try:
        while view:
            written: int = os.write(out_fd, view)
            if written <= 0:
                return False
            view = view[written:]
    except OSError:
        return False
    return True


def _read_body(response: http.client.HTTPResponse, label: str, cap: int, out_fd: int) -> Result[tuple[bytes, str], MediaError]:
    digest = hashlib.sha256()
    buffer: bytearray = bytearray()
    head: bytearray = bytearray()
    total: int = 0
    while True:
        try:
            chunk: bytes = response.read(_CHUNK)
        except ssl.SSLError:
            return Err(error=MediaError_NetworkFailure(message=f"TLS failure reading {label}"))
        except (TimeoutError, socket.timeout):
            return Err(error=MediaError_NetworkFailure(message=f"timeout reading {label}"))
        except (OSError, http.client.HTTPException):
            return Err(error=MediaError_NetworkFailure(message=f"connection failure reading {label}"))
        if not chunk:
            break
        total += len(chunk)
        if total > cap:
            return Err(error=MediaError_UpdateUnavailable(message=f"{label} exceeds size limit"))
        if len(head) < _HEAD:
            head.extend(chunk[: _HEAD - len(head)])
            if len(head) >= _HEAD and _looks_html(bytes(head)):
                return Err(error=MediaError_UpdateUnavailable(message=f"HTML payload for {label}"))
        digest.update(chunk)
        if out_fd < 0:
            buffer.extend(chunk)
        elif not _write_all(out_fd, chunk):
            return Err(error=MediaError_OutputFailure(message=f"failed writing temporary file for {label}"))
    if total == 0 or _looks_html(bytes(head)):
        return Err(error=MediaError_UpdateUnavailable(message=f"empty or HTML payload for {label}"))
    return Ok(value=(bytes(buffer), digest.hexdigest()))


def _fetch(repository: str, channel: str, asset: str, cap: int, out_fd: int) -> Result[tuple[bytes, str], MediaError]:
    try:
        context: ssl.SSLContext = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
    except (ssl.SSLError, OSError, ValueError):
        return Err(error=MediaError_NetworkFailure(message=f"cannot establish verifying TLS context ({channel})"))
    url: str = f"https://{_HOST_GITHUB}/{repository}/releases/latest/download/{asset}"
    label: str = f"{asset} ({channel})"
    redirects: int = 0
    while True:
        parts = urlsplit(url)
        host: str = parts.hostname or ""
        try:
            port: int | None = parts.port
        except ValueError:
            return Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect while fetching {label}"))
        if parts.scheme != "https" or host not in (_HOST_GITHUB, _HOST_ASSETS) or parts.username is not None or parts.password is not None or port not in (None, 443):
            return Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect while fetching {label}"))
        request_target: str = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        connection = http.client.HTTPSConnection(host, 443, timeout=_TIMEOUT, context=context)
        try:
            try:
                connection.request("GET", request_target, headers={"User-Agent": "yt-dlp-updater", "Accept": "application/octet-stream", "Accept-Encoding": "identity"})
                response: http.client.HTTPResponse = connection.getresponse()
            except ssl.SSLError:
                return Err(error=MediaError_NetworkFailure(message=f"TLS failure fetching {label} from {host}"))
            except (socket.gaierror, TimeoutError, socket.timeout):
                return Err(error=MediaError_NetworkFailure(message=f"DNS or timeout failure fetching {label} from {host}"))
            except (OSError, http.client.HTTPException):
                return Err(error=MediaError_NetworkFailure(message=f"connection failure fetching {label} from {host}"))
            status: int = response.status
            if status in (301, 302, 303, 307, 308):
                location: str | None = response.getheader("Location")
                if location is None or redirects >= _MAX_REDIRECTS or not location.isascii() or not location.isprintable() or any(c.isspace() for c in location):
                    return Err(error=MediaError_UpdateUnavailable(message=f"invalid or excessive redirect fetching {label}"))
                redirects += 1
                url = urljoin(url, location)
                continue
            if status == 404:
                return Err(error=MediaError_UpdateUnavailable(message=f"{label} not found (HTTP 404)"))
            if status != 200:
                return Err(error=MediaError_NetworkFailure(message=f"HTTP {status} fetching {label}"))
            content_type: str = (response.getheader("Content-Type") or "").lower()
            if "text/html" in content_type or "application/xhtml" in content_type:
                return Err(error=MediaError_UpdateUnavailable(message=f"HTML payload for {label}"))
            if (response.getheader("Content-Encoding") or "identity").lower() not in ("identity", ""):
                return Err(error=MediaError_UpdateUnavailable(message=f"unexpected encoding for {label}"))
            length_header: str | None = response.getheader("Content-Length")
            if length_header is not None:
                stripped: str = length_header.strip()
                if not stripped.isascii() or not stripped.isdigit():
                    return Err(error=MediaError_UpdateUnavailable(message=f"malformed Content-Length for {label}"))
                significant: str = stripped.lstrip("0")
                if len(significant) > 19 or int(significant or "0") > cap:
                    return Err(error=MediaError_UpdateUnavailable(message=f"{label} exceeds size limit"))
            return _read_body(response, label, cap, out_fd)
        finally:
            connection.close()


def _parse_manifest(data: bytes, channel: str) -> Result[str, MediaError]:
    try:
        text: str = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=MediaError_UpdateUnavailable(message=f"malformed checksum manifest ({channel})"))
    found: list[str] = []
    for raw_line in text.split("\n"):
        line: str = raw_line.rstrip("\r")
        pieces: list[str] = line.split(" ", 1)
        if len(pieces) != 2:
            continue
        name: str = pieces[1]
        if name.startswith(" ") or name.startswith("*"):
            name = name[1:]
        if name != _ASSET:
            continue
        checksum: str = pieces[0]
        if len(checksum) != 64 or any(c not in _HEXDIGITS for c in checksum):
            return Err(error=MediaError_UpdateUnavailable(message=f"malformed checksum for {_ASSET} ({channel})"))
        found.append(checksum.lower())
    if len(found) != 1:
        return Err(error=MediaError_UpdateUnavailable(message=f"missing or duplicate checksum for {_ASSET} ({channel})"))
    return Ok(value=found[0])


def _platform_safe() -> bool:
    if os.name != "posix":
        return False
    return os.O_NOFOLLOW != 0 and os.O_DIRECTORY != 0 and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd and os.rename in os.supports_dir_fd and os.unlink in os.supports_dir_fd and os.stat in os.supports_follow_symlinks and os.chmod in os.supports_fd


def _close(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _open_parent(target: Path) -> Result[tuple[int, str], MediaError]:
    shown: str = str(target)
    if not _platform_safe():
        return Err(error=MediaError_OutputFailure(message=f"platform lacks no-follow directory-fd operations for {shown}"))
    name: str = target.name
    if shown in ("", ".", "/") or name in ("", ".", "..") or "\x00" in shown:
        return Err(error=MediaError_OutputFailure(message=f"invalid update target {shown}"))
    parts: tuple[str, ...] = target.parts[:-1]
    flags: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    start: str = "/" if target.is_absolute() else "."
    components: tuple[str, ...] = parts[1:] if target.is_absolute() else parts
    try:
        dfd: int = os.open(start, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return Err(error=MediaError_OutputFailure(message=f"cannot open base directory for {shown}"))
    for component in components:
        try:
            next_fd: int = os.open(component, flags, dir_fd=dfd)
        except OSError:
            _close(dfd)
            return Err(error=MediaError_OutputFailure(message=f"unsafe or inaccessible directory in {shown}"))
        if not _close(dfd):
            _close(next_fd)
            return Err(error=MediaError_OutputFailure(message=f"cannot close directory in {shown}"))
        dfd = next_fd
    return Ok(value=(dfd, name))


def _inspect_target(dfd: int, name: str, shown: str) -> Result[tuple[int, int, int, str], MediaError]:
    try:
        fd: int = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dfd)
    except FileNotFoundError:
        return Ok(value=(-1, -1, 0, ""))
    except OSError as error:
        if error.errno == errno.ELOOP:
            return Err(error=MediaError_OutputFailure(message=f"update target is a symlink: {shown}"))
        return Err(error=MediaError_OutputFailure(message=f"cannot open update target {shown}"))
    result: Result[tuple[int, int, int, str], MediaError]
    try:
        info: os.stat_result = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            result = Err(error=MediaError_OutputFailure(message=f"update target is not a regular file: {shown}"))
        else:
            digest = hashlib.sha256()
            while True:
                chunk: bytes = os.read(fd, _CHUNK)
                if not chunk:
                    break
                digest.update(chunk)
            result = Ok(value=(info.st_dev, info.st_ino, info.st_mode, digest.hexdigest()))
    except OSError:
        result = Err(error=MediaError_OutputFailure(message=f"cannot read update target {shown}"))
    if not _close(fd):
        return Err(error=MediaError_OutputFailure(message=f"cannot close update target {shown}"))
    return result


def _target_unchanged(dfd: int, name: str, dev: int, ino: int) -> bool:
    try:
        current: os.stat_result = os.stat(name, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        return dev < 0
    except OSError:
        return False
    return dev >= 0 and stat.S_ISREG(current.st_mode) and current.st_dev == dev and current.st_ino == ino


def _commit(fd: int, dfd: int, temp_name: str, name: str, shown: str, dev: int, ino: int, mode: int) -> Result[Unit, MediaError]:
    try:
        os.fsync(fd)
        os.fchmod(fd, (mode & 0o777) if dev >= 0 else 0o755)
        os.fsync(fd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message=f"cannot flush or chmod temporary file for {shown}"))
    if not _target_unchanged(dfd, name, dev, ino):
        return Err(error=MediaError_OutputFailure(message=f"update target changed during update: {shown}"))
    try:
        os.replace(temp_name, name, src_dir_fd=dfd, dst_dir_fd=dfd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message=f"atomic replacement failed for {shown}"))
    return Ok(value=UNIT)


def _install(dfd: int, name: str, shown: str, repository: str, channel: str, expected: str, dev: int, ino: int, mode: int) -> Result[UpdateOutcome, MediaError]:
    temp_name: str = f".{name}.update-{secrets.token_hex(16)}"
    try:
        fd: int = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dfd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message=f"cannot create temporary file beside {shown}"))
    committed: bool = False
    outcome: Result[Unit, MediaError] = Ok(value=UNIT)
    try:
        fetched: Result[tuple[bytes, str], MediaError] = _fetch(repository, channel, _ASSET, _ASSET_CAP, fd)
        match fetched:
            case Err(error=fetch_error):
                outcome = Err(error=fetch_error)
            case Ok(value=(_, digest)):
                if not secrets.compare_digest(digest, expected):
                    outcome = Err(error=MediaError_UpdateUnavailable(message=f"checksum mismatch for {_ASSET} ({channel})"))
                else:
                    outcome = _commit(fd, dfd, temp_name, name, shown, dev, ino, mode)
                    match outcome:
                        case Ok():
                            committed = True
                        case Err():
                            committed = False
    finally:
        if not _close(fd) and not committed:
            outcome = Err(error=MediaError_OutputFailure(message=f"cannot close temporary file for {shown}"))
        if not committed:
            try:
                os.unlink(temp_name, dir_fd=dfd)
            except OSError:
                outcome = Err(error=MediaError_OutputFailure(message=f"cannot clean up temporary file for {shown}"))
    match outcome:
        case Err(error=install_error):
            return Err(error=install_error)
        case Ok():
            try:
                os.fsync(dfd)
            except OSError:
                return Err(error=MediaError_OutputFailure(message=f"directory fsync failed for {shown}"))
            return Ok(value=UpdateOutcome_Installed())


def _run(dfd: int, name: str, shown: str, repository: str, channel: str, install: bool) -> Result[UpdateOutcome, MediaError]:
    manifest: Result[tuple[bytes, str], MediaError] = _fetch(repository, channel, _MANIFEST, _MANIFEST_CAP, -1)
    match manifest:
        case Err(error=manifest_error):
            return Err(error=manifest_error)
        case Ok(value=(manifest_bytes, _)):
            parsed: Result[str, MediaError] = _parse_manifest(manifest_bytes, channel)
    match parsed:
        case Err(error=parse_error):
            return Err(error=parse_error)
        case Ok(value=expected):
            inspected: Result[tuple[int, int, int, str], MediaError] = _inspect_target(dfd, name, shown)
    match inspected:
        case Err(error=inspect_error):
            return Err(error=inspect_error)
        case Ok(value=(dev, ino, mode, current_digest)):
            if dev >= 0 and secrets.compare_digest(current_digest, expected):
                return Ok(value=UpdateOutcome_Current())
            if not install:
                return Ok(value=UpdateOutcome_Available())
            return _install(dfd, name, shown, repository, channel, expected, dev, ino, mode)


def _channel_name(repository: str) -> str:
    if repository == _REPO_STABLE:
        return "stable"
    if repository == _REPO_NIGHTLY:
        return "nightly"
    if repository == _REPO_MASTER:
        return "master"
    return ""


def apply_update(request: UpdateRequest) -> Result[UpdateOutcome, MediaError]:
    policy = request.policy
    install: bool
    match policy:
        case UpdatePolicy_Never():
            return Ok(value=UpdateOutcome_Disabled())
        case UpdatePolicy_Check():
            install = False
        case UpdatePolicy_Apply() | UpdatePolicy_Nightly() | UpdatePolicy_Master():
            install = True
    resolved: Result[str, MediaError] = resolve_update_repository(policy, request.channel)
    match resolved:
        case Err(error=resolve_error):
            return Err(error=resolve_error)
        case Ok(value=repository):
            channel: str = _channel_name(repository)
    if channel == "":
        return Err(error=MediaError_UpdateUnavailable(message="no official update repository selected"))
    target: Path = Path(request.target)
    shown: str = str(target)
    opened: Result[tuple[int, str], MediaError] = _open_parent(target)
    match opened:
        case Err(error=open_error):
            return Err(error=open_error)
        case Ok(value=(dfd, name)):
            ran: Result[UpdateOutcome, MediaError] = _run(dfd, name, shown, repository, channel, install)
            if not _close(dfd):
                return Err(error=MediaError_OutputFailure(message=f"cannot close directory of {shown}"))
            return ran
