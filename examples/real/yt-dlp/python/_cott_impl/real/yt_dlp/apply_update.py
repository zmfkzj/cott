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

import cott_runtime
from cott_runtime import Result
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


def _close_fd(fd: int) -> bool:
    try:
        os.close(fd)
    except (OSError, AttributeError, RuntimeError):
        return False
    return True


def _platform_safe() -> bool:
    try:
        return (
            os.name == "posix"
            and os.O_NOFOLLOW != 0
            and os.O_DIRECTORY != 0
            and os.O_CLOEXEC != 0
            and os.O_NONBLOCK != 0
            and os.O_NOATIME != 0
            and os.open in os.supports_dir_fd
            and os.stat in os.supports_dir_fd
            and os.rename in os.supports_dir_fd
            and os.unlink in os.supports_dir_fd
            and os.stat in os.supports_follow_symlinks
            and os.fsync is not None
            and os.fchmod is not None
            and os.replace is not None
        )
    except (AttributeError, TypeError):
        return False


def _open_parent(target: Path) -> Result[tuple[int, str], MediaError]:
    shown: str = str(target)
    name: str = target.name
    if not _platform_safe():
        return cott_runtime.Err(error=MediaError_OutputFailure(message="safe update filesystem operations are unavailable"))
    if shown in ("", ".", "/") or name in ("", ".", "..") or "\x00" in shown or target.anchor not in ("", "/"):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="invalid update target path"))
    components: tuple[str, ...] = target.parts[1:-1] if target.is_absolute() else target.parts[:-1]
    flags: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        directory: int = os.open("/" if target.is_absolute() else ".", flags)
    except (OSError, AttributeError, TypeError, RuntimeError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot open update base directory"))
    for component in components:
        try:
            child: int = os.open(component, flags, dir_fd=directory)
        except (OSError, AttributeError, TypeError, RuntimeError):
            _close_fd(directory)
            return cott_runtime.Err(error=MediaError_OutputFailure(message="unsafe or inaccessible update parent directory"))
        if not _close_fd(directory):
            _close_fd(child)
            return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot close update parent directory"))
        directory = child
    return cott_runtime.Ok(value=(directory, name))


def _file_state(info: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def _unchanged(directory: int, name: str, before: os.stat_result | None) -> bool:
    try:
        current: os.stat_result = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return before is None
    except (OSError, AttributeError, TypeError, RuntimeError):
        return False
    return before is not None and stat.S_ISREG(current.st_mode) and _file_state(current) == _file_state(before)


def _inspect_target(directory: int, name: str) -> Result[tuple[os.stat_result | None, str], MediaError]:
    try:
        fd: int = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
    except FileNotFoundError:
        if _unchanged(directory, name, None):
            return cott_runtime.Ok(value=(None, ""))
        return cott_runtime.Err(error=MediaError_OutputFailure(message="update target changed during inspection"))
    except (OSError, AttributeError, TypeError, RuntimeError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot open update target"))
    result: Result[tuple[os.stat_result | None, str], MediaError]
    try:
        before: os.stat_result = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            result = cott_runtime.Err(error=MediaError_OutputFailure(message="update target is not a regular file"))
        else:
            digest = hashlib.sha256()
            while True:
                block: bytes = os.read(fd, _CHUNK)
                if not block:
                    break
                digest.update(block)
            after: os.stat_result = os.fstat(fd)
            if _file_state(before) != _file_state(after) or not _unchanged(directory, name, before):
                result = cott_runtime.Err(error=MediaError_OutputFailure(message="update target changed during inspection"))
            else:
                result = cott_runtime.Ok(value=(before, digest.hexdigest()))
    except (OSError, AttributeError, TypeError, RuntimeError):
        result = cott_runtime.Err(error=MediaError_OutputFailure(message="cannot read update target"))
    if not _close_fd(fd):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot close update target"))
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


def _read_body(response: http.client.HTTPResponse, label: str, cap: int, length: int | None, out_fd: int | None) -> Result[tuple[bytes, str], MediaError]:
    manifest: bytearray | None = bytearray() if out_fd is None else None
    digest = hashlib.sha256() if out_fd is not None else None
    total: int = 0
    marker: int = 0
    bom_seen: bool = False
    while True:
        try:
            block: bytes = response.read(min(_CHUNK, cap - total + 1))
        except (OSError, TimeoutError, http.client.HTTPException, ValueError):
            return cott_runtime.Err(error=MediaError_NetworkFailure(message=f"network failure reading {label}"))
        if not block:
            break
        total += len(block)
        if total > cap:
            return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"{label} exceeds size limit"))
        if length is not None and total > length:
            return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"malformed Content-Length for {label}"))
        if marker != 3:
            for byte in block:
                if marker == 0:
                    if byte in _WHITESPACE:
                        continue
                    if byte == 0xEF and not bom_seen:
                        marker = 1
                    elif byte == ord("<"):
                        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"HTML payload for {label}"))
                    else:
                        marker = 3
                elif marker == 1:
                    marker = 2 if byte == 0xBB else 3
                else:
                    if byte == 0xBF:
                        marker = 0
                        bom_seen = True
                    else:
                        marker = 3
                if marker == 3:
                    break
        if manifest is not None:
            manifest.extend(block)
        elif out_fd is not None and digest is not None:
            digest.update(block)
            if not _write_all(out_fd, block):
                return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot write temporary update file"))
    if length is not None and total != length:
        return cott_runtime.Err(error=MediaError_NetworkFailure(message=f"incomplete response reading {label}"))
    if total == 0:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"empty release payload for {label}"))
    return cott_runtime.Ok(value=(bytes(manifest) if manifest is not None else b"", digest.hexdigest() if digest is not None else ""))


def _release_body(response: http.client.HTTPResponse, label: str, cap: int, out_fd: int | None) -> Result[tuple[bytes, str], MediaError]:
    content_type: str = (response.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
    encoding: str = (response.getheader("Content-Encoding") or "identity").strip().lower()
    if content_type in ("text/html", "application/xhtml+xml") or encoding != "identity":
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"invalid release payload metadata for {label}"))
    declared: str | None = response.getheader("Content-Length")
    if declared is None:
        return _read_body(response, label, cap, None, out_fd)
    raw_length: str = declared.strip()
    if not raw_length or not raw_length.isascii() or not raw_length.isdecimal():
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"malformed Content-Length for {label}"))
    digits: str = raw_length.lstrip("0") or "0"
    if len(digits) > len(str(cap)) or int(digits) > cap:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"{label} exceeds size limit"))
    return _read_body(response, label, cap, int(digits), out_fd)


def _close_connection(connection: http.client.HTTPSConnection | None, response: http.client.HTTPResponse | None) -> bool:
    closed: bool = True
    if response is not None:
        try:
            response.close()
        except (OSError, http.client.HTTPException, ValueError):
            closed = False
    if connection is not None:
        try:
            connection.close()
        except (OSError, http.client.HTTPException, ValueError):
            closed = False
    return closed


def _exchange(url: str, context: ssl.SSLContext, label: str, cap: int, out_fd: int | None) -> Result[tuple[str | None, bytes, str], MediaError]:
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 or character == "\\" for character in url):
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect fetching {label}"))
    try:
        parts = urlsplit(url)
        host: str = parts.hostname or ""
        port: int | None = parts.port
    except ValueError:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect fetching {label}"))
    if parts.scheme != "https" or host not in (_GITHUB, _RELEASE_ASSETS) or parts.username is not None or parts.password is not None or port not in (None, 443) or parts.fragment:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"forbidden redirect fetching {label}"))
    request_target: str = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    connection: http.client.HTTPSConnection | None = None
    response: http.client.HTTPResponse | None = None
    result: Result[tuple[str | None, bytes, str], MediaError]
    try:
        try:
            connection = http.client.HTTPSConnection(host, 443, timeout=_TIMEOUT, context=context)
            connection.request("GET", request_target, headers={"User-Agent": "yt-dlp-updater", "Accept": "application/octet-stream", "Accept-Encoding": "identity"})
            response = connection.getresponse()
            status: int = response.status
            if status in (301, 302, 303, 307, 308):
                location: str | None = response.getheader("Location")
                if location is None:
                    result = cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"missing redirect location fetching {label}"))
                else:
                    result = cott_runtime.Ok(value=(location, b"", ""))
            elif status == 404:
                result = cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"missing release asset {label}"))
            elif status != 200:
                result = cott_runtime.Err(error=MediaError_NetworkFailure(message=f"HTTP {status} fetching {label}"))
            else:
                body: Result[tuple[bytes, str], MediaError] = _release_body(response, label, cap, out_fd)
                match body:
                    case cott_runtime.Err(error=body_error):
                        result = cott_runtime.Err(error=body_error)
                    case cott_runtime.Ok(value=(data, digest)):
                        result = cott_runtime.Ok(value=(None, data, digest))
        except (OSError, TimeoutError, http.client.HTTPException):
            result = cott_runtime.Err(error=MediaError_NetworkFailure(message=f"network failure fetching {label}"))
        except (ValueError, UnicodeError):
            result = cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"malformed release metadata for {label}"))
    finally:
        closed: bool = _close_connection(connection, response)
    if not closed:
        return cott_runtime.Err(error=MediaError_NetworkFailure(message=f"cannot close release connection for {label}"))
    return result


def _fetch(repository: str, channel: str, asset: str, cap: int, out_fd: int | None) -> Result[tuple[bytes, str], MediaError]:
    try:
        context: ssl.SSLContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    except (OSError, ValueError):
        return cott_runtime.Err(error=MediaError_NetworkFailure(message="cannot establish verifying TLS"))
    url: str = f"https://{_GITHUB}/{repository}/releases/latest/download/{asset}"
    label: str = f"{asset} ({channel})"
    redirects: int = 0
    while True:
        fetched: Result[tuple[str | None, bytes, str], MediaError] = _exchange(url, context, label, cap, out_fd)
        match fetched:
            case cott_runtime.Err(error=fetch_error):
                return cott_runtime.Err(error=fetch_error)
            case cott_runtime.Ok(value=(location, data, digest)):
                if location is None:
                    return cott_runtime.Ok(value=(data, digest))
                if redirects >= _MAX_REDIRECTS or any(character.isspace() or ord(character) < 32 or ord(character) == 127 or character == "\\" for character in location):
                    return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"invalid or excessive redirect fetching {label}"))
                try:
                    url = urljoin(url, location)
                except ValueError:
                    return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"malformed redirect fetching {label}"))
                redirects += 1


def _parse_manifest(data: bytes, channel: str) -> Result[str, MediaError]:
    try:
        text: str = data.decode("utf-8")
    except UnicodeDecodeError:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"invalid checksum manifest ({channel})"))
    found: str | None = None
    for raw_line in text.split("\n"):
        if not raw_line:
            continue
        line: str = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if not line:
            continue
        entry: re.Match[str] | None = re.fullmatch(r"([0-9a-fA-F]{64}) [ *]([^\r\n]+)", line)
        if entry is None or any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in entry.group(2)):
            return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"malformed checksum manifest ({channel})"))
        if entry.group(2) == _ASSET:
            if found is not None:
                return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"duplicate checksum for {_ASSET} ({channel})"))
            found = entry.group(1).lower()
    if found is None:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message=f"missing checksum for {_ASSET} ({channel})"))
    return cott_runtime.Ok(value=found)


def _install(directory: int, name: str, repository: str, channel: str, expected: str, before: os.stat_result | None) -> Result[UpdateOutcome, MediaError]:
    try:
        os.fsync(directory)
    except (OSError, AttributeError, RuntimeError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot sync update directory"))
    try:
        temp_name: str = f".yt-dlp-update-{secrets.token_hex(16)}"
    except (OSError, RuntimeError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot generate temporary update file name"))
    try:
        fd: int = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
    except (OSError, AttributeError, TypeError, RuntimeError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot create temporary update file"))
    failure: MediaError | None = None
    temporary: os.stat_result | None = None
    fetched: Result[tuple[bytes, str], MediaError] = _fetch(repository, channel, _ASSET, _ASSET_CAP, fd)
    match fetched:
        case cott_runtime.Err(error=fetch_error):
            failure = fetch_error
        case cott_runtime.Ok(value=(_, digest)):
            if not secrets.compare_digest(digest, expected):
                failure = MediaError_UpdateUnavailable(message=f"checksum mismatch for {_ASSET} ({channel})")
    if failure is None:
        try:
            os.fsync(fd)
            os.fchmod(fd, (before.st_mode & 0o777) if before is not None else 0o755)
            os.fsync(fd)
            temporary = os.fstat(fd)
            if not stat.S_ISREG(temporary.st_mode):
                failure = MediaError_OutputFailure(message="temporary update file is not regular")
        except (OSError, AttributeError, TypeError, RuntimeError):
            failure = MediaError_OutputFailure(message="cannot sync or set update permissions")
    if not _close_fd(fd):
        failure = MediaError_OutputFailure(message="cannot close temporary update file")
    if failure is None:
        if temporary is None or not _unchanged(directory, temp_name, temporary) or not _unchanged(directory, name, before):
            failure = MediaError_OutputFailure(message="update target or temporary file changed before replacement")
        else:
            try:
                os.replace(temp_name, name, src_dir_fd=directory, dst_dir_fd=directory)
            except (OSError, AttributeError, TypeError, RuntimeError):
                failure = MediaError_OutputFailure(message="cannot atomically replace update target")
            else:
                if not _unchanged(directory, name, temporary):
                    return cott_runtime.Err(error=MediaError_OutputFailure(message="published update target changed"))
                try:
                    os.fsync(directory)
                except (OSError, AttributeError, RuntimeError):
                    return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot sync published update directory"))
                return cott_runtime.Ok(value=UpdateOutcome_Installed())
    try:
        os.unlink(temp_name, dir_fd=directory)
    except (OSError, AttributeError, TypeError, RuntimeError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot clean up temporary update file"))
    return cott_runtime.Err(error=failure)


def _run(directory: int, name: str, repository: str, channel: str, install: bool) -> Result[UpdateOutcome, MediaError]:
    manifest: Result[tuple[bytes, str], MediaError] = _fetch(repository, channel, _MANIFEST, _MANIFEST_CAP, None)
    match manifest:
        case cott_runtime.Err(error=manifest_error):
            return cott_runtime.Err(error=manifest_error)
        case cott_runtime.Ok(value=(data, _)):
            parsed: Result[str, MediaError] = _parse_manifest(data, channel)
    match parsed:
        case cott_runtime.Err(error=parse_error):
            return cott_runtime.Err(error=parse_error)
        case cott_runtime.Ok(value=expected):
            inspected: Result[tuple[os.stat_result | None, str], MediaError] = _inspect_target(directory, name)
    match inspected:
        case cott_runtime.Err(error=inspect_error):
            return cott_runtime.Err(error=inspect_error)
        case cott_runtime.Ok(value=(before, actual)):
            if before is not None and secrets.compare_digest(actual, expected):
                if not _unchanged(directory, name, before):
                    return cott_runtime.Err(error=MediaError_OutputFailure(message="update target changed during check"))
                return cott_runtime.Ok(value=UpdateOutcome_Current())
            if not install:
                if not _unchanged(directory, name, before):
                    return cott_runtime.Err(error=MediaError_OutputFailure(message="update target changed during check"))
                return cott_runtime.Ok(value=UpdateOutcome_Available())
            return _install(directory, name, repository, channel, expected, before)


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
            return cott_runtime.Ok(value=UpdateOutcome_Disabled())
        case UpdatePolicy_Check():
            install = False
        case UpdatePolicy_Apply() | UpdatePolicy_Nightly() | UpdatePolicy_Master():
            install = True
    resolved: Result[str, MediaError] = resolve_update_repository(policy, request.channel)
    match resolved:
        case cott_runtime.Err(error=resolve_error):
            return cott_runtime.Err(error=resolve_error)
        case cott_runtime.Ok(value=repository):
            channel: str = _channel_name(repository)
    if not channel:
        return cott_runtime.Err(error=MediaError_UpdateUnavailable(message="no official update channel selected"))
    opened: Result[tuple[int, str], MediaError] = _open_parent(request.target)
    match opened:
        case cott_runtime.Err(error=open_error):
            return cott_runtime.Err(error=open_error)
        case cott_runtime.Ok(value=(directory, name)):
            outcome: Result[UpdateOutcome, MediaError] = _run(directory, name, repository, channel, install)
            if not _close_fd(directory):
                return cott_runtime.Err(error=MediaError_OutputFailure(message="cannot close update directory"))
            return outcome
