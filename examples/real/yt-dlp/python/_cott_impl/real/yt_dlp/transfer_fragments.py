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
_BACKOFF_CAP: Final[float] = 8.0


def _network_failure() -> MediaError:
    return MediaError_NetworkFailure(message="fragment network transfer failed")


def _output_failure() -> MediaError:
    return MediaError_OutputFailure(message="fragment output operation failed")


def _url_ok(url: str) -> bool:
    if any(character.isspace() or ord(character) < 32 or 127 <= ord(character) <= 159 for character in url):
        return False
    try:
        parsed = urlsplit(url)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname) and (parsed.port is None or 0 < parsed.port <= 65535)
    except ValueError:
        return False


def _backoff(attempt: int) -> None:
    time.sleep(min(0.5 * (2 ** min(attempt, 4)), _BACKOFF_CAP))


def _close_fd(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _close_response(connection: http.client.HTTPConnection, response: http.client.HTTPResponse) -> bool:
    closed = True
    try:
        response.close()
    except (OSError, ValueError, http.client.HTTPException):
        closed = False
    try:
        connection.close()
    except (OSError, ValueError, http.client.HTTPException):
        closed = False
    return closed


def _filesystem_supported() -> bool:
    try:
        return (os.name == "posix" and bool(os.O_NOFOLLOW) and bool(os.O_DIRECTORY) and bool(os.O_CLOEXEC) and bool(os.O_NONBLOCK)
                and os.open in os.supports_dir_fd and os.mkdir in os.supports_dir_fd
                and os.stat in os.supports_dir_fd and os.stat in os.supports_follow_symlinks
                and os.rename in os.supports_dir_fd and os.fsync is not None)
    except (AttributeError, TypeError):
        return False


def _open_parent_once(destination: Path) -> Result[int, MediaError]:
    if not _filesystem_supported():
        return cott_runtime.Err(error=_output_failure())
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        directory = os.open("/" if destination.is_absolute() else ".", flags)
    except (OSError, ValueError):
        return cott_runtime.Err(error=_output_failure())
    components = destination.parts[1:-1] if destination.is_absolute() else destination.parts[:-1]
    for component in components:
        try:
            child = os.open(component, flags, dir_fd=directory)
        except FileNotFoundError:
            try:
                os.mkdir(component, 0o755, dir_fd=directory)
            except (OSError, ValueError) as creation_error:
                if not isinstance(creation_error, FileExistsError):
                    _close_fd(directory)
                    return cott_runtime.Err(error=_output_failure())
            try:
                child = os.open(component, flags, dir_fd=directory)
            except (OSError, ValueError):
                _close_fd(directory)
                return cott_runtime.Err(error=_output_failure())
        except (OSError, ValueError):
            _close_fd(directory)
            return cott_runtime.Err(error=_output_failure())
        if not _close_fd(directory):
            _close_fd(child)
            return cott_runtime.Err(error=_output_failure())
        directory = child
    return cott_runtime.Ok(value=directory)


def _open_parent(destination: Path, retries: int) -> Result[int, MediaError]:
    for attempt in range(retries + 1):
        opened = _open_parent_once(destination)
        if isinstance(opened, cott_runtime.Ok):
            return opened
        if attempt < retries:
            _backoff(attempt)
    return cott_runtime.Err(error=_output_failure())


def _open_work_once(directory: int, name: str, resume: bool) -> Result[tuple[int, int], MediaError]:
    flags = os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    try:
        fd = os.open(name, flags, dir_fd=directory)
    except FileNotFoundError:
        try:
            fd = os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o644, dir_fd=directory)
        except FileExistsError:
            try:
                fd = os.open(name, flags, dir_fd=directory)
            except (OSError, ValueError):
                return cott_runtime.Err(error=_output_failure())
        except (OSError, ValueError):
            return cott_runtime.Err(error=_output_failure())
    except (OSError, ValueError):
        return cott_runtime.Err(error=_output_failure())
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            _close_fd(fd)
            return cott_runtime.Err(error=_output_failure())
    except OSError:
        _close_fd(fd)
        return cott_runtime.Err(error=_output_failure())
    return cott_runtime.Ok(value=(fd, info.st_size if resume else 0))


def _open_work(directory: int, name: str, resume: bool, retries: int) -> Result[tuple[int, int], MediaError]:
    for attempt in range(retries + 1):
        opened = _open_work_once(directory, name, resume)
        if isinstance(opened, cott_runtime.Ok):
            return opened
        if attempt < retries:
            _backoff(attempt)
    return cott_runtime.Err(error=_output_failure())


def _write_all(fd: int, data: bytes) -> bool:
    remaining = memoryview(data)
    try:
        while remaining:
            count = os.write(fd, remaining)
            if count <= 0:
                return False
            remaining = remaining[count:]
    except OSError:
        return False
    return True


def _decimal(text: str) -> int | None:
    if not text or not text.isascii() or not text.isdecimal():
        return None
    digits = text.lstrip("0") or "0"
    if len(digits) > 20:
        return None
    return int(digits)


def _declared_length(response: http.client.HTTPResponse, base: int, limit: int) -> Result[int | None, MediaError]:
    header = response.getheader("Content-Length")
    if header is None:
        return cott_runtime.Ok(value=None)
    text = header.strip()
    if not text or not text.isascii() or not text.isdecimal():
        return cott_runtime.Err(error=_network_failure())
    length = _decimal(text)
    if length is None or base + length > limit:
        return cott_runtime.Err(error=MediaError_SizeLimit())
    return cott_runtime.Ok(value=length)


def _partial_range(response: http.client.HTTPResponse, offset: int, limit: int, length: int | None) -> Result[int, MediaError]:
    header = response.getheader("Content-Range") or ""
    matched = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/([0-9]+)", header.strip())
    if matched is None:
        return cott_runtime.Err(error=_network_failure())
    first = _decimal(matched.group(1))
    last = _decimal(matched.group(2))
    total = _decimal(matched.group(3))
    if first is None or last is None or total is None:
        return cott_runtime.Err(error=_network_failure())
    if total > limit:
        return cott_runtime.Err(error=MediaError_SizeLimit())
    span = last - first + 1
    if first != offset or span <= 0 or last + 1 != total or (length is not None and length != span):
        return cott_runtime.Err(error=_network_failure())
    return cott_runtime.Ok(value=span)


def _connect(url: str, offset: int) -> Result[tuple[http.client.HTTPConnection, http.client.HTTPResponse], MediaError]:
    try:
        context = ssl.create_default_context()
    except (OSError, ValueError):
        return cott_runtime.Err(error=_network_failure())
    current = url
    for redirect in range(_MAX_REDIRECTS + 1):
        if not _url_ok(current):
            return cott_runtime.Err(error=_network_failure())
        connection: http.client.HTTPConnection | None = None
        try:
            parts = urlsplit(current)
            host = parts.hostname or ""
            target = (parts.path or "/") + ("?" + parts.query if parts.query else "")
            if parts.scheme == "https":
                connection = http.client.HTTPSConnection(host, parts.port, timeout=_TIMEOUT, context=context)
            else:
                connection = http.client.HTTPConnection(host, parts.port, timeout=_TIMEOUT)
            headers = {"Accept-Encoding": "identity", "User-Agent": "yt-dlp"}
            if offset > 0:
                headers["Range"] = f"bytes={offset}-"
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
            if response.status not in (301, 302, 303, 307, 308):
                return cott_runtime.Ok(value=(connection, response))
            location = response.getheader("Location")
            status = response.status
            if not _close_response(connection, response):
                return cott_runtime.Err(error=_network_failure())
            if redirect == _MAX_REDIRECTS:
                return cott_runtime.Err(error=_network_failure())
            if not location:
                return cott_runtime.Err(error=MediaError_HttpStatus(status=status))
            current = urljoin(current, location)
        except (OSError, ValueError, http.client.HTTPException):
            if connection is not None:
                try:
                    connection.close()
                except (OSError, ValueError, http.client.HTTPException):
                    return cott_runtime.Err(error=_network_failure())
            return cott_runtime.Err(error=_network_failure())
    return cott_runtime.Err(error=_network_failure())


def _stream(response: http.client.HTTPResponse, fd: int, offset: int, request: TransferRequest, policy: FragmentPolicy) -> Result[tuple[int, int, int], MediaError]:
    status = response.status
    if status == 416 and offset > 0:
        try:
            os.fsync(fd)
            info = os.fstat(fd)
        except OSError:
            return cott_runtime.Err(error=_output_failure())
        if not stat.S_ISREG(info.st_mode) or info.st_size != offset:
            return cott_runtime.Err(error=_output_failure())
        return cott_runtime.Ok(value=(offset, info.st_dev, info.st_ino))
    if not 200 <= status < 300 or (status == 206 and offset == 0):
        return cott_runtime.Err(error=MediaError_HttpStatus(status=status))
    resumed = status == 206
    base = offset if resumed else 0
    declared = _declared_length(response, base, request.max_bytes)
    if isinstance(declared, cott_runtime.Err):
        return cott_runtime.Err(error=declared.error)
    expected = declared.value
    if resumed:
        partial = _partial_range(response, offset, request.max_bytes, expected)
        if isinstance(partial, cott_runtime.Err):
            return cott_runtime.Err(error=partial.error)
        expected = partial.value
    try:
        if resumed:
            if os.fstat(fd).st_size != offset:
                return cott_runtime.Err(error=_output_failure())
            os.lseek(fd, 0, os.SEEK_END)
        else:
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
    except OSError:
        return cott_runtime.Err(error=_output_failure())
    read_size = min(policy.buffer_size, policy.chunk_size) if policy.chunk_size else policy.buffer_size
    started = time.monotonic()
    received = 0
    while True:
        try:
            block = response.read(min(read_size, request.max_bytes - base - received + 1))
        except (OSError, ValueError, http.client.HTTPException):
            return cott_runtime.Err(error=_network_failure())
        if not block:
            break
        received += len(block)
        if base + received > request.max_bytes:
            return cott_runtime.Err(error=MediaError_SizeLimit())
        if policy.rate_limit_bytes_per_second:
            delay = received / policy.rate_limit_bytes_per_second - (time.monotonic() - started)
            if delay > 0:
                time.sleep(delay)
        if not _write_all(fd, block):
            return cott_runtime.Err(error=_output_failure())
    if expected is not None and received != expected:
        return cott_runtime.Err(error=_network_failure())
    try:
        os.fsync(fd)
        info = os.fstat(fd)
    except OSError:
        return cott_runtime.Err(error=_output_failure())
    if not stat.S_ISREG(info.st_mode) or info.st_size != base + received:
        return cott_runtime.Err(error=_output_failure())
    return cott_runtime.Ok(value=(info.st_size, info.st_dev, info.st_ino))


def _same_work(directory: int, name: str, size: int, device: int, inode: int) -> bool:
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except (OSError, ValueError):
        return False
    return stat.S_ISREG(info.st_mode) and info.st_size == size and info.st_dev == device and info.st_ino == inode


def _destination_regular(directory: int, name: str) -> bool:
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return True
    except (OSError, ValueError):
        return False
    return stat.S_ISREG(info.st_mode)


def _publish(directory: int, work: str, request: TransferRequest, policy: FragmentPolicy, saved: tuple[int, int, int]) -> Result[TransferReceipt, MediaError]:
    size, device, inode = saved
    name = request.destination.name
    if not _same_work(directory, work, size, device, inode):
        return cott_runtime.Err(error=_output_failure())
    if work != name:
        for attempt in range(policy.file_access_retries + 1):
            if not _destination_regular(directory, name) or not _same_work(directory, work, size, device, inode):
                return cott_runtime.Err(error=_output_failure())
            try:
                os.replace(work, name, src_dir_fd=directory, dst_dir_fd=directory)
                break
            except (OSError, ValueError):
                if attempt == policy.file_access_retries:
                    return cott_runtime.Err(error=_output_failure())
                _backoff(attempt)
    if not _same_work(directory, name, size, device, inode):
        return cott_runtime.Err(error=_output_failure())
    try:
        os.fsync(directory)
    except OSError:
        return cott_runtime.Err(error=_output_failure())
    return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=size, simulated=False))


def _host_attempt(request: TransferRequest, policy: FragmentPolicy, directory: int, work: str) -> Result[tuple[int, int, int], MediaError]:
    opened = _open_work(directory, work, policy.continue_download, policy.file_access_retries)
    if isinstance(opened, cott_runtime.Err):
        return cott_runtime.Err(error=opened.error)
    fd, offset = opened.value
    if offset > request.max_bytes:
        result: Result[tuple[int, int, int], MediaError] = cott_runtime.Err(error=MediaError_SizeLimit())
    else:
        fetched = _connect(request.url, offset)
        if isinstance(fetched, cott_runtime.Err):
            result = cott_runtime.Err(error=fetched.error)
        else:
            connection, response = fetched.value
            try:
                result = _stream(response, fd, offset, request, policy)
            finally:
                closed = _close_response(connection, response)
            if not closed:
                result = cott_runtime.Err(error=_network_failure())
    if not _close_fd(fd):
        return cott_runtime.Err(error=_output_failure())
    return result


def _retryable(error: MediaError) -> bool:
    return isinstance(error, MediaError_NetworkFailure) or (isinstance(error, MediaError_HttpStatus) and (error.status == 429 or 500 <= error.status < 600))


def _host_one(request: TransferRequest, policy: FragmentPolicy, retries: int) -> Result[TransferReceipt, MediaError]:
    parent = _open_parent(request.destination, policy.file_access_retries)
    if isinstance(parent, cott_runtime.Err):
        return cott_runtime.Err(error=parent.error)
    directory = parent.value
    work = request.destination.name + ".part" if policy.part_files else request.destination.name
    attempt = 0
    while True:
        transferred = _host_attempt(request, policy, directory, work)
        if isinstance(transferred, cott_runtime.Ok):
            outcome: Result[TransferReceipt, MediaError] = _publish(directory, work, request, policy, transferred.value)
            break
        if not _retryable(transferred.error):
            outcome = cott_runtime.Err(error=transferred.error)
            break
        if attempt >= retries:
            if retries:
                outcome = cott_runtime.Err(error=MediaError_RetryExhausted(attempts=attempt + 1))
            else:
                outcome = cott_runtime.Err(error=transferred.error)
            break
        _backoff(attempt)
        attempt += 1
    if not _close_fd(directory):
        return cott_runtime.Err(error=_output_failure())
    return outcome


def _fixture_fetch(url: str) -> Result[bytes, MediaError] | None:
    try:
        return cott_runtime.Ok(value=cott_runtime._cott_fixture_http(url))
    except HTTPError as error:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=error.code))
    except cott_runtime.CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return None
        cause = error.__cause__
        if isinstance(cause, HTTPError):
            return cott_runtime.Err(error=MediaError_HttpStatus(status=cause.code))
        matched = re.search(r"(?:HTTP |status[ =])([1-5][0-9][0-9])\b", error.message)
        if matched is not None:
            return cott_runtime.Err(error=MediaError_HttpStatus(status=int(matched.group(1))))
        return cott_runtime.Err(error=_network_failure())
    except (OSError, ValueError, http.client.HTTPException):
        return cott_runtime.Err(error=_network_failure())


def _fixture_write(path: Path, body: bytes, retries: int, replace: bool) -> bool:
    for attempt in range(retries + 1):
        try:
            if replace:
                cott_runtime._cott_fixture_replace(path, body)
            else:
                cott_runtime._cott_fixture_write(path, body)
            return True
        except cott_runtime.CottContractViolation as error:
            cause = error.__cause__
            if not isinstance(cause, (FileNotFoundError, NotADirectoryError, PermissionError)) or attempt == retries:
                return False
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            if attempt == retries:
                return False
        except OSError:
            return False
        _backoff(attempt)
    return False


def _fixture_finish(request: TransferRequest, policy: FragmentPolicy, body: bytes, write_work: bool) -> Result[TransferReceipt, MediaError]:
    destination = request.destination
    work = destination.with_name(destination.name + ".part") if policy.part_files else destination
    if policy.rate_limit_bytes_per_second and body:
        time.sleep(len(body) / policy.rate_limit_bytes_per_second)
    if write_work and not _fixture_write(work, body, policy.file_access_retries, False):
        return cott_runtime.Err(error=_output_failure())
    if policy.part_files:
        if not _fixture_write(destination, body, policy.file_access_retries, True):
            return cott_runtime.Err(error=_output_failure())
        try:
            cott_runtime._cott_fixture_remove(work)
        except (cott_runtime.CottContractViolation, OSError):
            return cott_runtime.Err(error=_output_failure())
    return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=len(body), simulated=False))


def _fixture_complete(request: TransferRequest, policy: FragmentPolicy) -> Result[TransferReceipt, MediaError]:
    work = request.destination.with_name(request.destination.name + ".part") if policy.part_files else request.destination
    try:
        body = cott_runtime._cott_fixture_read(work)
    except cott_runtime.CottContractViolation as error:
        if isinstance(error.__cause__, FileNotFoundError):
            return cott_runtime.Err(error=MediaError_HttpStatus(status=416))
        return cott_runtime.Err(error=_output_failure())
    except FileNotFoundError:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=416))
    except OSError:
        return cott_runtime.Err(error=_output_failure())
    if not body:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=416))
    if len(body) > request.max_bytes:
        return cott_runtime.Err(error=MediaError_SizeLimit())
    return _fixture_finish(request, policy, body, False)


def _fixture_one(request: TransferRequest, policy: FragmentPolicy, retries: int, first: Result[bytes, MediaError]) -> Result[TransferReceipt, MediaError]:
    attempt = 0
    while True:
        fetched = first if attempt == 0 else _fixture_fetch(request.url)
        if fetched is None:
            return cott_runtime.Err(error=_network_failure())
        if isinstance(fetched, cott_runtime.Ok):
            body = fetched.value
            if len(body) > request.max_bytes:
                return cott_runtime.Err(error=MediaError_SizeLimit())
            return _fixture_finish(request, policy, body, True)
        if isinstance(fetched.error, MediaError_HttpStatus) and fetched.error.status == 416 and policy.continue_download:
            return _fixture_complete(request, policy)
        if not _retryable(fetched.error):
            return cott_runtime.Err(error=fetched.error)
        if attempt >= retries:
            if retries:
                return cott_runtime.Err(error=MediaError_RetryExhausted(attempts=attempt + 1))
            return cott_runtime.Err(error=fetched.error)
        _backoff(attempt)
        attempt += 1


def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
    if policy.concurrent_fragments == 0 or policy.buffer_size == 0:
        return cott_runtime.Err(error=MediaError_InvalidInput(message="fragment concurrency and buffer size must be positive"))
    destinations: set[str] = set()
    for fragment in fragments:
        if not _url_ok(fragment.url):
            return cott_runtime.Err(error=MediaError_InvalidInput(message="invalid fragment URL"))
        destination = fragment.destination
        if destination.name in ("", ".", "..") or "\x00" in str(destination):
            return cott_runtime.Err(error=MediaError_InvalidInput(message="fragment destination must name a file"))
        key = os.path.abspath(destination)
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
