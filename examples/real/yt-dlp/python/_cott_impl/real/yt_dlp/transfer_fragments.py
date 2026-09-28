import http.client
import os
import re
import ssl
import stat
import time
from pathlib import Path
from typing import Final
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit

import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import FragmentPolicy, MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_RetryExhausted, MediaError_SizeLimit, TransferReceipt, TransferRequest

_TIMEOUT: Final[float] = 30.0
_MAX_REDIRECTS: Final[int] = 5


def _network_error() -> MediaError:
    return MediaError_NetworkFailure(message="fragment network transfer failed")


def _output_error() -> MediaError:
    return MediaError_OutputFailure(message="fragment output operation failed")


def _valid_url(url: str) -> bool:
    if any(ch.isspace() or ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in url):
        return False
    try:
        parts = urlsplit(url)
        port = parts.port
        return parts.scheme in ("http", "https") and bool(parts.hostname) and (port is None or 0 < port <= 65535)
    except ValueError:
        return False


def _backoff(attempt: int) -> None:
    time.sleep(min(0.5 * (2 ** min(attempt, 4)), 8.0))


def _supported() -> bool:
    try:
        return (os.name == "posix" and bool(os.O_NOFOLLOW) and bool(os.O_DIRECTORY)
                and os.open in os.supports_dir_fd and os.mkdir in os.supports_dir_fd
                and os.stat in os.supports_dir_fd and os.stat in os.supports_follow_symlinks
                and os.rename in os.supports_dir_fd and os.fsync is not None)
    except (AttributeError, TypeError):
        return False


def _parent(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    directory = os.open("/" if path.is_absolute() else ".", flags)
    try:
        parents = path.parts[1:-1] if path.is_absolute() else path.parts[:-1]
        for part in parents:
            try:
                child = os.open(part, flags, dir_fd=directory)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o755, dir_fd=directory)
                except FileExistsError:
                    child = os.open(part, flags, dir_fd=directory)
                else:
                    child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        return directory
    except (OSError, ValueError):
        os.close(directory)
        raise


def _open_work(directory: int, name: str, resume: bool) -> tuple[int, int, bool]:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    try:
        fd = os.open(name, flags, dir_fd=directory)
        existing = True
    except FileNotFoundError:
        fd = os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
        existing = False
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError("work file is not regular")
        if not (existing and resume):
            os.ftruncate(fd, 0)
        return fd, info.st_size if existing and resume else 0, existing and resume
    except (OSError, ValueError):
        os.close(fd)
        raise


def _connect(url: str, resume: bool, offset: int) -> Result[tuple[http.client.HTTPConnection, http.client.HTTPResponse], MediaError]:
    try:
        context = ssl.create_default_context()
        current = url
        for redirect in range(_MAX_REDIRECTS + 1):
            if not _valid_url(current):
                return cott_runtime.Err(error=_network_error())
            parts = urlsplit(current)
            host = parts.hostname or ""
            target = (parts.path or "/") + ("?" + parts.query if parts.query else "")
            connection: http.client.HTTPConnection = (http.client.HTTPSConnection(host, parts.port, timeout=_TIMEOUT, context=context)
                                                     if parts.scheme == "https" else http.client.HTTPConnection(host, parts.port, timeout=_TIMEOUT))
            try:
                headers = {"Accept-Encoding": "identity"}
                if resume:
                    headers["Range"] = f"bytes={offset}-"
                connection.request("GET", target, headers=headers)
                response = connection.getresponse()
            except (OSError, ValueError, UnicodeError, http.client.HTTPException):
                connection.close()
                raise
            if response.status not in (301, 302, 303, 307, 308):
                return cott_runtime.Ok(value=(connection, response))
            location = response.getheader("Location")
            status = response.status
            response.close()
            connection.close()
            if not location:
                return cott_runtime.Err(error=MediaError_HttpStatus(status=status))
            if redirect == _MAX_REDIRECTS:
                return cott_runtime.Err(error=_network_error())
            current = urljoin(current, location)
    except (OSError, ValueError, UnicodeError, http.client.HTTPException):
        return cott_runtime.Err(error=_network_error())
    return cott_runtime.Err(error=_network_error())


def _length(text: str | None) -> int | None:
    if text is None:
        return None
    if not text.isascii() or not text.isdecimal() or len(text) > 20:
        raise ValueError("invalid length")
    return int(text)


def _stream(response: http.client.HTTPResponse, fd: int, offset: int, resumed: bool, request: TransferRequest, policy: FragmentPolicy) -> Result[int, MediaError]:
    status = response.status
    if status == 416 and resumed:
        try:
            os.fsync(fd)
            return cott_runtime.Ok(value=os.fstat(fd).st_size)
        except OSError:
            return cott_runtime.Err(error=_output_error())
    if not 200 <= status < 300:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=status))
    if status == 206 and not resumed:
        return cott_runtime.Err(error=_network_error())
    base = offset if status == 206 else 0
    try:
        expected = _length(response.getheader("Content-Length"))
        if status == 206:
            match = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/([0-9]+|\*)", response.getheader("Content-Range") or "")
            if match is None:
                return cott_runtime.Err(error=_network_error())
            first = _length(match.group(1))
            last = _length(match.group(2))
            total = _length(match.group(3)) if match.group(3) != "*" else None
            if total is not None and total > request.max_bytes:
                return cott_runtime.Err(error=MediaError_SizeLimit())
            if first != offset or last is None or last < offset or (total is not None and last + 1 != total) or (expected is not None and expected != last - offset + 1):
                return cott_runtime.Err(error=_network_error())
            expected = last - offset + 1
        if expected is not None and base + expected > request.max_bytes:
            return cott_runtime.Err(error=MediaError_SizeLimit())
    except (ValueError, OSError, http.client.HTTPException):
        return cott_runtime.Err(error=_network_error())
    try:
        if status == 206 and os.fstat(fd).st_size != offset:
            return cott_runtime.Err(error=_output_error())
        if status != 206:
            os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_END)
    except OSError:
        return cott_runtime.Err(error=_output_error())
    read_size = min(policy.buffer_size, policy.chunk_size) if policy.chunk_size else policy.buffer_size
    started = time.monotonic()
    received = 0
    while True:
        try:
            block = response.read(min(read_size, request.max_bytes - base - received + 1))
        except (OSError, ValueError, http.client.HTTPException):
            return cott_runtime.Err(error=_network_error())
        if not block:
            break
        received += len(block)
        if base + received > request.max_bytes:
            return cott_runtime.Err(error=MediaError_SizeLimit())
        if policy.rate_limit_bytes_per_second:
            delay = received / policy.rate_limit_bytes_per_second - (time.monotonic() - started)
            if delay > 0:
                time.sleep(delay)
        try:
            view = memoryview(block)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    return cott_runtime.Err(error=_output_error())
                view = view[count:]
        except OSError:
            return cott_runtime.Err(error=_output_error())
    if expected is not None and received != expected:
        return cott_runtime.Err(error=_network_error())
    try:
        os.fsync(fd)
        size = os.fstat(fd).st_size
        if size != base + received:
            return cott_runtime.Err(error=_output_error())
        return cott_runtime.Ok(value=size)
    except OSError:
        return cott_runtime.Err(error=_output_error())


def _download_to_work(fd: int, offset: int, resumed: bool, request: TransferRequest, policy: FragmentPolicy) -> Result[int, MediaError]:
    connected = _connect(request.url, resumed, offset)
    if isinstance(connected, cott_runtime.Err):
        return cott_runtime.Err(error=connected.error)
    connection, response = connected.value
    try:
        result = _stream(response, fd, offset, resumed, request, policy)
    except (OSError, ValueError, http.client.HTTPException):
        result = cott_runtime.Err(error=_network_error())
    close_failed = False
    try:
        response.close()
    except (OSError, ValueError, http.client.HTTPException):
        close_failed = True
    try:
        connection.close()
    except (OSError, ValueError, http.client.HTTPException):
        close_failed = True
    if close_failed:
        return cott_runtime.Err(error=_network_error())
    return result


def _same(directory: int, name: str, saved: tuple[int, int, int]) -> bool:
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        return stat.S_ISREG(info.st_mode) and (info.st_size, info.st_dev, info.st_ino) == saved
    except (OSError, ValueError):
        return False


def _publish(directory: int, work: str, request: TransferRequest, policy: FragmentPolicy, saved: tuple[int, int, int]) -> Result[TransferReceipt, MediaError]:
    name = request.destination.name
    if not _same(directory, work, saved):
        return cott_runtime.Err(error=_output_error())
    if work != name:
        for attempt in range(policy.file_access_retries + 1):
            try:
                try:
                    target = os.stat(name, dir_fd=directory, follow_symlinks=False)
                except FileNotFoundError:
                    target = None
                if target is not None and not stat.S_ISREG(target.st_mode):
                    return cott_runtime.Err(error=_output_error())
                if not _same(directory, work, saved):
                    return cott_runtime.Err(error=_output_error())
                os.replace(work, name, src_dir_fd=directory, dst_dir_fd=directory)
                break
            except (OSError, ValueError):
                if attempt == policy.file_access_retries:
                    return cott_runtime.Err(error=_output_error())
                _backoff(attempt)
    if not _same(directory, name, saved):
        return cott_runtime.Err(error=_output_error())
    try:
        os.fsync(directory)
    except OSError:
        return cott_runtime.Err(error=_output_error())
    return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=saved[0], simulated=False))


def _host_attempt(request: TransferRequest, policy: FragmentPolicy, directory: int, work: str) -> Result[TransferReceipt, MediaError]:
    opened: tuple[int, int, bool] | None = None
    for attempt in range(policy.file_access_retries + 1):
        try:
            opened = _open_work(directory, work, policy.continue_download)
            break
        except (OSError, ValueError):
            if attempt == policy.file_access_retries:
                return cott_runtime.Err(error=_output_error())
            _backoff(attempt)
    if opened is None:
        return cott_runtime.Err(error=_output_error())
    fd, offset, resumed = opened
    saved: tuple[int, int, int] | None = None
    try:
        transferred = (cott_runtime.Err(error=MediaError_SizeLimit()) if offset > request.max_bytes
                       else _download_to_work(fd, offset, resumed, request, policy))
        if isinstance(transferred, cott_runtime.Ok):
            try:
                info = os.fstat(fd)
                saved = (transferred.value, info.st_dev, info.st_ino)
            except OSError:
                transferred = cott_runtime.Err(error=_output_error())
    finally:
        try:
            os.close(fd)
            closed = True
        except OSError:
            closed = False
    if not closed:
        return cott_runtime.Err(error=_output_error())
    if isinstance(transferred, cott_runtime.Err):
        return cott_runtime.Err(error=transferred.error)
    if saved is None:
        return cott_runtime.Err(error=_output_error())
    return _publish(directory, work, request, policy, saved)


def _retryable(error: MediaError) -> bool:
    return isinstance(error, MediaError_NetworkFailure) or (isinstance(error, MediaError_HttpStatus) and (error.status == 429 or 500 <= error.status < 600))


def _host_one(request: TransferRequest, policy: FragmentPolicy, retries: int) -> Result[TransferReceipt, MediaError]:
    if not _supported():
        return cott_runtime.Err(error=_output_error())
    directory: int | None = None
    for access in range(policy.file_access_retries + 1):
        try:
            directory = _parent(request.destination)
            break
        except (OSError, ValueError):
            if access == policy.file_access_retries:
                return cott_runtime.Err(error=_output_error())
            _backoff(access)
    if directory is None:
        return cott_runtime.Err(error=_output_error())
    work = request.destination.name + ".part" if policy.part_files else request.destination.name
    outcome: Result[TransferReceipt, MediaError] = cott_runtime.Err(error=_output_error())
    try:
        for attempt in range(retries + 1):
            outcome = _host_attempt(request, policy, directory, work)
            if isinstance(outcome, cott_runtime.Ok) or not _retryable(outcome.error):
                break
            if attempt == retries:
                if retries:
                    outcome = cott_runtime.Err(error=MediaError_RetryExhausted(attempts=attempt + 1))
            else:
                _backoff(attempt)
    finally:
        try:
            os.close(directory)
        except OSError:
            outcome = cott_runtime.Err(error=_output_error())
    return outcome


def _fixture_fetch(url: str) -> Result[bytes, MediaError] | None:
    try:
        return cott_runtime.Ok(value=cott_runtime._cott_fixture_http(url))
    except HTTPError as error:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=error.code))
    except cott_runtime.CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return None
        if isinstance(error.__cause__, HTTPError):
            return cott_runtime.Err(error=MediaError_HttpStatus(status=error.__cause__.code))
        status = re.search(r"(?:HTTP |status[ =])([1-5][0-9][0-9])\b", error.message)
        if status is not None:
            return cott_runtime.Err(error=MediaError_HttpStatus(status=int(status.group(1))))
        return cott_runtime.Err(error=_network_error())
    except (OSError, ValueError, http.client.HTTPException):
        return cott_runtime.Err(error=_network_error())


def _fixture_work(path: Path, retries: int) -> Result[bytes | None, MediaError]:
    for attempt in range(retries + 1):
        try:
            return cott_runtime.Ok(value=cott_runtime._cott_fixture_read(path))
        except cott_runtime.CottContractViolation as error:
            if isinstance(error.__cause__, FileNotFoundError):
                return cott_runtime.Ok(value=None)
            retryable = isinstance(error.__cause__, (PermissionError, NotADirectoryError))
        except FileNotFoundError:
            return cott_runtime.Ok(value=None)
        except (PermissionError, NotADirectoryError):
            retryable = True
        except OSError:
            retryable = False
        if not retryable or attempt == retries:
            return cott_runtime.Err(error=_output_error())
        _backoff(attempt)
    return cott_runtime.Err(error=_output_error())


def _fixture_replace(path: Path, body: bytes, retries: int) -> bool:
    for attempt in range(retries + 1):
        try:
            cott_runtime._cott_fixture_replace(path, body, create_parents=True)
            return True
        except cott_runtime.CottContractViolation as error:
            retryable = isinstance(error.__cause__, (FileNotFoundError, NotADirectoryError, PermissionError))
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            retryable = True
        except OSError:
            retryable = False
        if not retryable or attempt == retries:
            return False
        _backoff(attempt)
    return False


def _fixture_finish(request: TransferRequest, policy: FragmentPolicy, body: bytes, write_work: bool) -> Result[TransferReceipt, MediaError]:
    if len(body) > request.max_bytes:
        return cott_runtime.Err(error=MediaError_SizeLimit())
    destination = request.destination
    work = destination.with_name(destination.name + ".part") if policy.part_files else destination
    if policy.rate_limit_bytes_per_second and write_work:
        read_size = min(policy.buffer_size, policy.chunk_size) if policy.chunk_size else policy.buffer_size
        started = time.monotonic()
        for position in range(0, len(body), read_size):
            delay = min(position + read_size, len(body)) / policy.rate_limit_bytes_per_second - (time.monotonic() - started)
            if delay > 0:
                time.sleep(delay)
    if write_work and not _fixture_replace(work, body, policy.file_access_retries):
        return cott_runtime.Err(error=_output_error())
    if policy.part_files:
        if not _fixture_replace(destination, body, policy.file_access_retries):
            return cott_runtime.Err(error=_output_error())
        try:
            cott_runtime._cott_fixture_remove(work)
        except (cott_runtime.CottContractViolation, OSError):
            return cott_runtime.Err(error=_output_error())
    return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=len(body), simulated=False))


def _fixture_one(request: TransferRequest, policy: FragmentPolicy, retries: int, first: Result[bytes, MediaError]) -> Result[TransferReceipt, MediaError]:
    existing: bytes | None = None
    if policy.continue_download:
        work = request.destination.with_name(request.destination.name + ".part") if policy.part_files else request.destination
        read = _fixture_work(work, policy.file_access_retries)
        if isinstance(read, cott_runtime.Err):
            return cott_runtime.Err(error=read.error)
        existing = read.value
        if existing is not None and len(existing) > request.max_bytes:
            return cott_runtime.Err(error=MediaError_SizeLimit())
    for attempt in range(retries + 1):
        fetched = first if attempt == 0 else _fixture_fetch(request.url)
        if fetched is None:
            return cott_runtime.Err(error=_network_error())
        if isinstance(fetched, cott_runtime.Ok):
            return _fixture_finish(request, policy, fetched.value, True)
        if isinstance(fetched.error, MediaError_HttpStatus) and fetched.error.status == 416 and existing is not None:
            return _fixture_finish(request, policy, existing, False)
        if not _retryable(fetched.error):
            return cott_runtime.Err(error=fetched.error)
        if attempt == retries:
            return cott_runtime.Err(error=MediaError_RetryExhausted(attempts=attempt + 1) if retries else fetched.error)
        _backoff(attempt)
    return cott_runtime.Err(error=_network_error())


def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
    if policy.concurrent_fragments == 0 or policy.buffer_size == 0:
        return cott_runtime.Err(error=MediaError_InvalidInput(message="fragment concurrency and buffer size must be positive"))
    destinations: set[str] = set()
    for fragment in fragments:
        if not _valid_url(fragment.url):
            return cott_runtime.Err(error=MediaError_InvalidInput(message="invalid fragment URL"))
        destination = fragment.destination
        if destination.name in ("", ".", "..") or "\x00" in str(destination):
            return cott_runtime.Err(error=MediaError_InvalidInput(message="fragment destination must name a file"))
        try:
            key = os.path.abspath(destination)
        except (OSError, ValueError):
            return cott_runtime.Err(error=MediaError_InvalidInput(message="invalid fragment destination"))
        if key in destinations:
            return cott_runtime.Err(error=MediaError_InvalidInput(message="duplicate fragment destination"))
        destinations.add(key)
    retries = policy.fragment_retries if len(fragments) > 1 else policy.retries
    receipts: list[TransferReceipt] = []
    for fragment in fragments:
        if fragment.simulate:
            receipts.append(TransferReceipt(url=fragment.url, destination=fragment.destination, bytes_written=0, simulated=True))
            continue
        fixture = _fixture_fetch(fragment.url)
        outcome = _host_one(fragment, policy, retries) if fixture is None else _fixture_one(fragment, policy, retries, fixture)
        if isinstance(outcome, cott_runtime.Err):
            return cott_runtime.Err(error=outcome.error)
        receipts.append(outcome.value)
    return cott_runtime.Ok(value=CottList(values=receipts))
