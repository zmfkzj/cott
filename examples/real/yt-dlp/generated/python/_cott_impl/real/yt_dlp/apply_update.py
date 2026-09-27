import hashlib
import http.client
import os
import re
import secrets
import ssl
import stat
from pathlib import Path
from typing import Final
from urllib.parse import urljoin, urlsplit

from cott_runtime import Err, Ok, Result
from real.yt_dlp import resolve_update_repository
from real.yt_dlp_types import MediaError, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_UpdateUnavailable, UpdateOutcome, UpdateOutcome_Available, UpdateOutcome_Current, UpdateOutcome_Disabled, UpdateOutcome_Installed, UpdatePolicy_Apply, UpdatePolicy_Check, UpdatePolicy_Master, UpdatePolicy_Never, UpdatePolicy_Nightly, UpdateRequest

_ASSET: Final[str] = "yt-dlp"
_MANIFEST: Final[str] = "SHA2-256SUMS"
_MANIFEST_CAP: Final[int] = 1048576
_ASSET_CAP: Final[int] = 67108864
_CHUNK: Final[int] = 65536
_TIMEOUT: Final[float] = 30.0
_MAX_REDIRECTS: Final[int] = 5
_GITHUB: Final[str] = "github.com"
_RELEASE_ASSETS: Final[str] = "release-assets.githubusercontent.com"
_STABLE: Final[str] = "yt-dlp/yt-dlp"
_NIGHTLY: Final[str] = "yt-dlp/yt-dlp-nightly-builds"
_MASTER: Final[str] = "yt-dlp/yt-dlp-master-builds"
_WHITESPACE: Final[bytes] = b" \t\r\n\f\v"
_BOM: Final[bytes] = b"\xef\xbb\xbf"


def _close_fd(fd: int) -> bool:
    try:
        os.close(fd)
    except (OSError, AttributeError, RuntimeError):
        return False
    return True


def _platform_safe() -> bool:
    try:
        return (os.name == "posix" and os.O_NOFOLLOW != 0 and os.O_DIRECTORY != 0 and os.O_CLOEXEC != 0 and os.O_NONBLOCK != 0 and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd and os.rename in os.supports_dir_fd and os.unlink in os.supports_dir_fd and os.stat in os.supports_follow_symlinks and os.fsync is not None and os.fchmod is not None)
    except (AttributeError, TypeError):
        return False


def _open_parent(target: Path) -> Result[tuple[int, str], MediaError]:
    shown: str = str(target)
    name: str = target.name
    if not _platform_safe():
        return Err(error=MediaError_OutputFailure(message="safe update filesystem operations are unavailable"))
    if shown in ("", ".", "/") or name in ("", ".", "..") or "\x00" in shown or target.anchor not in ("", "/"):
        return Err(error=MediaError_OutputFailure(message="invalid update target path"))
    components: tuple[str, ...] = target.parts[1:-1] if target.is_absolute() else target.parts[:-1]
    flags: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        directory: int = os.open("/" if target.is_absolute() else ".", flags)
    except (OSError, AttributeError, TypeError, RuntimeError):
        return Err(error=MediaError_OutputFailure(message="cannot open update base directory"))
    for component in components:
        try:
            child: int = os.open(component, flags, dir_fd=directory)
        except (OSError, AttributeError, TypeError, RuntimeError):
            _close_fd(directory)
            return Err(error=MediaError_OutputFailure(message="unsafe or inaccessible update parent directory"))
        if not _close_fd(directory):
            _close_fd(child)
            return Err(error=MediaError_OutputFailure(message="cannot close update parent directory"))
        directory = child
    return Ok(value=(directory, name))


def _same_leaf(directory: int, name: str, device: int, inode: int) -> bool:
    try:
        current: os.stat_result = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return device < 0
    except (OSError, AttributeError, TypeError, RuntimeError):
        return False
    return device >= 0 and stat.S_ISREG(current.st_mode) and current.st_dev == device and current.st_ino == inode


def _inspect_target(directory: int, name: str) -> Result[tuple[int, int, int, str], MediaError]:
    try:
        fd: int = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
    except FileNotFoundError:
        if _same_leaf(directory, name, -1, -1):
            return Ok(value=(-1, -1, 0, ""))
        return Err(error=MediaError_OutputFailure(message="update target changed during inspection"))
    except (OSError, AttributeError, TypeError, RuntimeError):
        return Err(error=MediaError_OutputFailure(message="cannot open update target"))
    result: Result[tuple[int, int, int, str], MediaError]
    try:
        before: os.stat_result = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            result = Err(error=MediaError_OutputFailure(message="update target is not a regular file"))
        else:
            digest = hashlib.sha256()
            while True:
                block: bytes = os.read(fd, _CHUNK)
                if not block:
                    break
                digest.update(block)
            after: os.stat_result = os.fstat(fd)
            if (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns) or not _same_leaf(directory, name, before.st_dev, before.st_ino):
                result = Err(error=MediaError_OutputFailure(message="update target changed during inspection"))
            else:
                result = Ok(value=(before.st_dev, before.st_ino, before.st_mode, digest.hexdigest()))
    except (OSError, AttributeError, TypeError, RuntimeError):
        result = Err(error=MediaError_OutputFailure(message="cannot read update target"))
    if not _close_fd(fd):
        return Err(error=MediaError_OutputFailure(message="cannot close update target"))
    return result


def _write_all(fd: int, data: bytes) -> bool:
    remaining: memoryview = memoryview(data)
    try:
        while remaining:
            written: int = os.write(fd, remaining)
            if written <= 0:
                return False
            remaining = remaining[written:]
    except (OSError, AttributeError, TypeError, RuntimeError):
        return False
    return True


def _read_body(response: http.client.HTTPResponse, label: str, cap: int, length: int | None, out_fd: int) -> Result[tuple[bytes, str], MediaError]:
    digest = hashlib.sha256()
    manifest: bytearray | None = bytearray() if out_fd < 0 else None
    total: int = 0
    at_start: bool = True
    saw_bom: bool = False
    pending: bytes = b""
    while True:
        try:
            block: bytes = response.read(min(_CHUNK, cap - total + 1))
        except (OSError, http.client.HTTPException, ValueError):
            return Err(error=MediaError_NetworkFailure(message=f"network failure reading {label}"))
        if not block:
            break
        total += len(block)
        if total > cap:
            return Err(error=MediaError_UpdateUnavailable(message=f"{label} exceeds size limit"))
        if at_start:
            head: bytes = pending + block.lstrip(_WHITESPACE)
            pending = b""
            if not saw_bom and head and _BOM.startswith(head) and len(head) < len(_BOM):
                pending = head
            else:
                if not saw_bom and head.startswith(_BOM):
                    head = head[len(_BOM):].lstrip(_WHITESPACE)
                    saw_bom = True
                if head.startswith(b"<"):
                    return Err(error=MediaError_UpdateUnavailable(message=f"HTML payload for {label}"))
                if head:
                    at_start = False
        digest.update(block)
        if manifest is not None:
            manifest.extend(block)
        elif not _write_all(out_fd, block):
            return Err(error=MediaError_OutputFailure(message="cannot write temporary update file"))
    if length is not None and total != length:
        return Err(error=MediaError_NetworkFailure(message=f"incomplete response reading {label}"))
    if total == 0:
        return Err(error=MediaError_UpdateUnavailable(message=f"empty release payload for {label}"))
    return Ok(value=(bytes(manifest) if manifest is not None else b"", digest.hexdigest()))


def _release_body(response: http.client.HTTPResponse, label: str, cap: int, out_fd: int) -> Result[tuple[bytes, str], MediaError]:
    content_type: str = (response.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
    encoding: str = (response.getheader("Content-Encoding") or "identity").strip().lower()
    if content_type in ("text/html", "application/xhtml+xml") or encoding != "identity":
        return Err(error=MediaError_UpdateUnavailable(message=f"invalid release payload metadata for {label}"))
    declared: str | None = response.getheader("Content-Length")
    if declared is None:
        return _read_body(response, label, cap, None, out_fd)
    raw_length: str = declared.strip()
    if not raw_length or not raw_length.isascii() or not raw_length.isdecimal():
        return Err(error=MediaError_UpdateUnavailable(message=f"malformed Content-Length for {label}"))
    digits: str = raw_length.lstrip("0") or "0"
    if len(digits) > len(str(cap)) or int(digits) > cap:
        return Err(error=MediaError_UpdateUnavailable(message=f"{label} exceeds size limit"))
    return _read_body(response, label, cap, int(digits), out_fd)


def _close_connection(connection: http.client.HTTPSConnection, response: http.client.HTTPResponse | None) -> bool:
    closed: bool = True
    if response is not None:
        try:
            response.close()
        except (OSError, http.client.HTTPException, ValueError):
            closed = False
    try:
        connection.close()
    except (OSError, http.client.HTTPException, ValueError):
        closed = False
    return closed


def _exchange(url: str, context: ssl.SSLContext, label: str, cap: int, out_fd: int) -> Result[tuple[str | None, bytes, str], MediaError]:
    try:
        parts = urlsplit(url)
        host: str = parts.hostname or ""
        port: int | None = parts.port
    except ValueError:
        return Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect fetching {label}"))
    if parts.scheme != "https" or host not in (_GITHUB, _RELEASE_ASSETS) or parts.username is not None or parts.password is not None or port not in (None, 443) or parts.fragment:
        return Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect fetching {label}"))
    request_target: str = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    connection = http.client.HTTPSConnection(host, 443, timeout=_TIMEOUT, context=context)
    response: http.client.HTTPResponse | None = None
    result: Result[tuple[str | None, bytes, str], MediaError]
    try:
        try:
            connection.request("GET", request_target, headers={"User-Agent": "yt-dlp-updater", "Accept": "application/octet-stream", "Accept-Encoding": "identity"})
            response = connection.getresponse()
            status: int = response.status
            if status in (301, 302, 303, 307, 308):
                location: str | None = response.getheader("Location")
                if location is None:
                    result = Err(error=MediaError_UpdateUnavailable(message=f"missing redirect location fetching {label}"))
                else:
                    result = Ok(value=(location, b"", ""))
            elif status == 404:
                result = Err(error=MediaError_UpdateUnavailable(message=f"missing release asset {label}"))
            elif status != 200:
                result = Err(error=MediaError_NetworkFailure(message=f"HTTP {status} fetching {label}"))
            else:
                body: Result[tuple[bytes, str], MediaError] = _release_body(response, label, cap, out_fd)
                match body:
                    case Err(error=body_error):
                        result = Err(error=body_error)
                    case Ok(value=(data, digest)):
                        result = Ok(value=(None, data, digest))
        except (OSError, http.client.HTTPException):
            result = Err(error=MediaError_NetworkFailure(message=f"network failure fetching {label}"))
        except (ValueError, UnicodeError):
            result = Err(error=MediaError_UpdateUnavailable(message=f"malformed release metadata for {label}"))
    finally:
        closed: bool = _close_connection(connection, response)
    if not closed:
        return Err(error=MediaError_NetworkFailure(message=f"cannot close release connection for {label}"))
    return result


def _fetch(repository: str, channel: str, asset: str, cap: int, out_fd: int) -> Result[tuple[bytes, str], MediaError]:
    try:
        context: ssl.SSLContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    except (OSError, ValueError):
        return Err(error=MediaError_NetworkFailure(message="cannot establish verifying TLS"))
    url: str = f"https://{_GITHUB}/{repository}/releases/latest/download/{asset}"
    label: str = f"{asset} ({channel})"
    redirects: int = 0
    while True:
        fetched: Result[tuple[str | None, bytes, str], MediaError] = _exchange(url, context, label, cap, out_fd)
        match fetched:
            case Err(error=fetch_error):
                return Err(error=fetch_error)
            case Ok(value=(location, data, digest)):
                if location is None:
                    return Ok(value=(data, digest))
                if redirects >= _MAX_REDIRECTS or not location.isascii() or not location.isprintable() or any(character.isspace() or character == "\\" for character in location):
                    return Err(error=MediaError_UpdateUnavailable(message=f"invalid or excessive redirect fetching {label}"))
                try:
                    url = urljoin(url, location)
                except ValueError:
                    return Err(error=MediaError_UpdateUnavailable(message=f"malformed redirect fetching {label}"))
                redirects += 1


def _parse_manifest(data: bytes, channel: str) -> Result[str, MediaError]:
    try:
        text: str = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=MediaError_UpdateUnavailable(message=f"invalid checksum manifest ({channel})"))
    found: str | None = None
    for raw_line in text.split("\n"):
        if not raw_line:
            continue
        line: str = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if not line:
            continue
        entry: re.Match[str] | None = re.fullmatch(r"([0-9a-fA-F]{64}) [ *]([^\r\n]+)", line)
        if entry is None:
            return Err(error=MediaError_UpdateUnavailable(message=f"malformed checksum manifest ({channel})"))
        if entry.group(2) == _ASSET:
            if found is not None:
                return Err(error=MediaError_UpdateUnavailable(message=f"duplicate checksum for {_ASSET} ({channel})"))
            found = entry.group(1).lower()
    if found is None:
        return Err(error=MediaError_UpdateUnavailable(message=f"missing checksum for {_ASSET} ({channel})"))
    return Ok(value=found)


def _install(directory: int, name: str, repository: str, channel: str, expected: str, device: int, inode: int, mode: int) -> Result[UpdateOutcome, MediaError]:
    try:
        os.fsync(directory)
    except (OSError, AttributeError, RuntimeError):
        return Err(error=MediaError_OutputFailure(message="cannot sync update directory"))
    try:
        temp_name: str = f".yt-dlp-update-{secrets.token_hex(16)}"
    except (OSError, RuntimeError):
        return Err(error=MediaError_OutputFailure(message="cannot generate temporary update file name"))
    try:
        fd: int = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
    except (OSError, AttributeError, TypeError, RuntimeError):
        return Err(error=MediaError_OutputFailure(message="cannot create temporary update file"))
    failure: MediaError | None = None
    temp_device: int = -1
    temp_inode: int = -1
    fetched: Result[tuple[bytes, str], MediaError] = _fetch(repository, channel, _ASSET, _ASSET_CAP, fd)
    match fetched:
        case Err(error=fetch_error):
            failure = fetch_error
        case Ok(value=(_, digest)):
            if not secrets.compare_digest(digest, expected):
                failure = MediaError_UpdateUnavailable(message=f"checksum mismatch for {_ASSET} ({channel})")
    if failure is None:
        try:
            os.fsync(fd)
            os.fchmod(fd, (mode & 0o777) if device >= 0 else 0o755)
            os.fsync(fd)
            temp_info: os.stat_result = os.fstat(fd)
            if not stat.S_ISREG(temp_info.st_mode):
                failure = MediaError_OutputFailure(message="temporary update file is not regular")
            else:
                temp_device = temp_info.st_dev
                temp_inode = temp_info.st_ino
        except (OSError, AttributeError, RuntimeError):
            failure = MediaError_OutputFailure(message="cannot sync or set update permissions")
    if not _close_fd(fd):
        failure = MediaError_OutputFailure(message="cannot close temporary update file")
    if failure is None:
        if not _same_leaf(directory, temp_name, temp_device, temp_inode) or not _same_leaf(directory, name, device, inode):
            failure = MediaError_OutputFailure(message="update target or temporary file changed before replacement")
        else:
            try:
                os.replace(temp_name, name, src_dir_fd=directory, dst_dir_fd=directory)
            except (OSError, AttributeError, TypeError, RuntimeError):
                failure = MediaError_OutputFailure(message="cannot atomically replace update target")
            else:
                if not _same_leaf(directory, name, temp_device, temp_inode):
                    return Err(error=MediaError_OutputFailure(message="published update target changed"))
                try:
                    os.fsync(directory)
                except (OSError, AttributeError, RuntimeError):
                    return Err(error=MediaError_OutputFailure(message="cannot sync published update directory"))
                return Ok(value=UpdateOutcome_Installed())
    try:
        os.unlink(temp_name, dir_fd=directory)
    except (OSError, AttributeError, TypeError, RuntimeError):
        return Err(error=MediaError_OutputFailure(message="cannot clean up temporary update file"))
    return Err(error=failure)


def _run(directory: int, name: str, repository: str, channel: str, install: bool) -> Result[UpdateOutcome, MediaError]:
    manifest: Result[tuple[bytes, str], MediaError] = _fetch(repository, channel, _MANIFEST, _MANIFEST_CAP, -1)
    match manifest:
        case Err(error=manifest_error):
            return Err(error=manifest_error)
        case Ok(value=(data, _)):
            parsed: Result[str, MediaError] = _parse_manifest(data, channel)
    match parsed:
        case Err(error=parse_error):
            return Err(error=parse_error)
        case Ok(value=expected):
            inspected: Result[tuple[int, int, int, str], MediaError] = _inspect_target(directory, name)
    match inspected:
        case Err(error=inspect_error):
            return Err(error=inspect_error)
        case Ok(value=(device, inode, mode, actual)):
            if device >= 0 and secrets.compare_digest(actual, expected):
                return Ok(value=UpdateOutcome_Current())
            if not install:
                if not _same_leaf(directory, name, device, inode):
                    return Err(error=MediaError_OutputFailure(message="update target changed during check"))
                return Ok(value=UpdateOutcome_Available())
            return _install(directory, name, repository, channel, expected, device, inode, mode)


def _channel_name(repository: str) -> str:
    if repository == _STABLE:
        return "stable"
    if repository == _NIGHTLY:
        return "nightly"
    if repository == _MASTER:
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
    if not channel:
        return Err(error=MediaError_UpdateUnavailable(message="no official update channel selected"))
    opened: Result[tuple[int, str], MediaError] = _open_parent(Path(request.target))
    match opened:
        case Err(error=open_error):
            return Err(error=open_error)
        case Ok(value=(directory, name)):
            outcome: Result[UpdateOutcome, MediaError] = _run(directory, name, repository, channel, install)
            if not _close_fd(directory):
                return Err(error=MediaError_OutputFailure(message="cannot close update directory"))
            return outcome
