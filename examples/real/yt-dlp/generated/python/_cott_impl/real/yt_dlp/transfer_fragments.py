import http.client
import os
import socket
import ssl
import stat
import time
from pathlib import Path
from typing import Final
from urllib.parse import urljoin, urlsplit

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import FragmentPolicy, MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_RetryExhausted, MediaError_SizeLimit, TransferReceipt, TransferRequest

_TIMEOUT: Final[float] = 30.0
_MAX_REDIRECTS: Final[int] = 5
_BACKOFF: Final[float] = 0.5
_BACKOFF_CAP: Final[float] = 8.0


def _url_ok(url: str) -> bool:
    if url == "" or any(ord(c) < 0x21 or ord(c) == 0x7F for c in url):
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    try:
        parts.port
    except ValueError:
        return False
    return True


def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(_BACKOFF * (2 ** attempt), _BACKOFF_CAP))


def _is_regular_fd(fd: int) -> bool:
    try:
        return stat.S_ISREG(os.fstat(fd).st_mode)
    except OSError:
        return False


def _open_file(path: Path, append: bool, file_retries: int) -> Result[int, MediaError]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW | (os.O_APPEND if append else os.O_TRUNC)
    attempt = 0
    while True:
        try:
            fd = os.open(path, flags, 0o644)
        except OSError:
            if attempt >= file_retries:
                return Err(error=MediaError_OutputFailure(message=f"cannot open {path}"))
            _sleep_backoff(attempt)
            attempt += 1
            continue
        if not _is_regular_fd(fd):
            os.close(fd)
            return Err(error=MediaError_OutputFailure(message=f"not a regular file {path}"))
        return Ok(value=fd)


def _write_all(fd: int, chunk: bytes) -> bool:
    view = memoryview(chunk)
    try:
        while view:
            view = view[os.write(fd, view):]
    except OSError:
        return False
    return True


def _connect(url: str, offset: int) -> Result[http.client.HTTPResponse, MediaError]:
    current = url
    for _ in range(_MAX_REDIRECTS + 1):
        if not _url_ok(current):
            return Err(error=MediaError_NetworkFailure(message="redirect to unsupported URL"))
        parts = urlsplit(current)
        host = parts.hostname or ""
        port = parts.port
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        headers = {"User-Agent": "yt-dlp", "Accept-Encoding": "identity"}
        if offset > 0:
            headers["Range"] = f"bytes={offset}-"
        connection: http.client.HTTPConnection
        if parts.scheme == "https":
            connection = http.client.HTTPSConnection(host, port, timeout=_TIMEOUT, context=ssl.create_default_context())
        else:
            connection = http.client.HTTPConnection(host, port, timeout=_TIMEOUT)
        try:
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
        except (OSError, ValueError, http.client.HTTPException, socket.timeout):
            connection.close()
            return Err(error=MediaError_NetworkFailure(message=f"connection failure fetching from {host}"))
        if response.status in (301, 302, 303, 307, 308):
            location = response.getheader("Location")
            status = response.status
            connection.close()
            if location is None:
                return Err(error=MediaError_HttpStatus(status=status))
            current = urljoin(current, location)
            continue
        return Ok(value=response)
    return Err(error=MediaError_NetworkFailure(message="too many redirects"))


def _stream(response: http.client.HTTPResponse, fd: int, policy: FragmentPolicy, work: Path, start_total: int, limit: int) -> Result[tuple[int, int], MediaError]:
    read_size = policy.buffer_size if policy.chunk_size == 0 else min(policy.buffer_size, policy.chunk_size)
    rate = policy.rate_limit_bytes_per_second
    started = time.monotonic()
    received = 0
    total = start_total
    while True:
        try:
            chunk = response.read(read_size)
        except (OSError, http.client.HTTPException, socket.timeout):
            return Err(error=MediaError_NetworkFailure(message="connection failure while reading"))
        if not chunk:
            break
        total += len(chunk)
        received += len(chunk)
        if limit > 0 and total > limit:
            return Err(error=MediaError_SizeLimit())
        if not _write_all(fd, chunk):
            return Err(error=MediaError_OutputFailure(message=f"cannot write {work}"))
        if rate > 0:
            ahead = received / rate - (time.monotonic() - started)
            if ahead > 0:
                time.sleep(ahead)
    try:
        os.fsync(fd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message=f"cannot flush {work}"))
    return Ok(value=(total, received))


def _consume(response: http.client.HTTPResponse, policy: FragmentPolicy, work: Path, offset: int, limit: int) -> Result[int, MediaError]:
    status = response.status
    if status == 416 and offset > 0:
        return Ok(value=offset)
    if status not in (200, 206):
        return Err(error=MediaError_HttpStatus(status=status))
    append = status == 206 and offset > 0
    start_total = offset if append else 0
    length = response.getheader("Content-Length")
    stripped = length.strip() if length is not None else ""
    expected = int(stripped) if stripped.isascii() and stripped.isdigit() else -1
    if limit > 0 and expected >= 0 and start_total + expected > limit:
        return Err(error=MediaError_SizeLimit())
    opened = _open_file(work, append, policy.file_access_retries)
    match opened:
        case Err(error=open_error):
            return Err(error=open_error)
        case Ok(value=fd):
            try:
                streamed = _stream(response, fd, policy, work, start_total, limit)
            finally:
                os.close(fd)
    match streamed:
        case Err(error=stream_error):
            return Err(error=stream_error)
        case Ok(value=(total, received)):
            if expected >= 0 and received != expected:
                return Err(error=MediaError_NetworkFailure(message="incomplete response body"))
            return Ok(value=total)


def _existing_size(work: Path) -> Result[int, MediaError]:
    try:
        info = os.stat(work, follow_symlinks=False)
    except FileNotFoundError:
        return Ok(value=0)
    except OSError:
        return Err(error=MediaError_OutputFailure(message=f"cannot inspect {work}"))
    if not stat.S_ISREG(info.st_mode):
        return Err(error=MediaError_OutputFailure(message=f"not a regular file {work}"))
    return Ok(value=info.st_size)


def _attempt(request: TransferRequest, policy: FragmentPolicy, work: Path) -> Result[int, MediaError]:
    offset = 0
    if policy.continue_download:
        sized = _existing_size(work)
        match sized:
            case Err(error=size_error):
                return Err(error=size_error)
            case Ok(value=size):
                offset = size
    limit = request.max_bytes
    if limit > 0 and offset > limit:
        return Err(error=MediaError_SizeLimit())
    connected = _connect(request.url, offset)
    match connected:
        case Err(error=connect_error):
            return Err(error=connect_error)
        case Ok(value=response):
            try:
                return _consume(response, policy, work, offset, limit)
            finally:
                response.close()


def _finish(request: TransferRequest, policy: FragmentPolicy, work: Path, destination: Path, written: int) -> Result[TransferReceipt, MediaError]:
    if work != destination:
        tries = 0
        while True:
            try:
                os.replace(work, destination)
                break
            except OSError:
                if tries >= policy.file_access_retries:
                    return Err(error=MediaError_OutputFailure(message=f"cannot rename to {destination}"))
                _sleep_backoff(tries)
                tries += 1
    return Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=written, simulated=False))


def _transfer_one(request: TransferRequest, policy: FragmentPolicy, retries: int) -> Result[TransferReceipt, MediaError]:
    destination = Path(request.destination)
    if request.simulate:
        return Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=0, simulated=True))
    work = destination.with_name(destination.name + ".part") if policy.part_files else destination
    attempt = 0
    while True:
        outcome = _attempt(request, policy, work)
        match outcome:
            case Ok(value=written):
                return _finish(request, policy, work, destination, written)
            case Err(error=error):
                retryable = isinstance(error, MediaError_NetworkFailure) or (isinstance(error, MediaError_HttpStatus) and (error.status >= 500 or error.status == 429))
                if not retryable:
                    return Err(error=error)
                if attempt >= retries:
                    if retries == 0:
                        return Err(error=error)
                    return Err(error=MediaError_RetryExhausted(attempts=attempt + 1))
                _sleep_backoff(attempt)
                attempt += 1


def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
    if policy.concurrent_fragments == 0:
        return Err(error=MediaError_InvalidInput(message="concurrent_fragments must be positive"))
    if policy.buffer_size == 0:
        return Err(error=MediaError_InvalidInput(message="buffer_size must be positive"))
    seen: set[str] = set()
    requests: list[TransferRequest] = []
    for fragment in fragments:
        if not _url_ok(fragment.url):
            return Err(error=MediaError_InvalidInput(message="invalid fragment URL"))
        destination = Path(fragment.destination)
        if destination.name in ("", ".", ".."):
            return Err(error=MediaError_InvalidInput(message=f"invalid destination {destination}"))
        key = os.path.abspath(destination)
        if key in seen:
            return Err(error=MediaError_InvalidInput(message=f"duplicate destination {destination}"))
        seen.add(key)
        requests.append(fragment)
    retries = policy.fragment_retries if len(requests) > 1 else policy.retries
    receipts: list[TransferReceipt] = []
    for request in requests:
        outcome: Result[TransferReceipt, MediaError]
        try:
            outcome = _transfer_one(request, policy, retries)
        except Exception:
            outcome = Err(error=MediaError_OutputFailure(message="unexpected failure transferring fragment"))
        match outcome:
            case Err(error=failure):
                return Err(error=failure)
            case Ok(value=receipt):
                receipts.append(receipt)
    return Ok(value=CottList(values=receipts))
