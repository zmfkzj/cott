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
    if url == "" or any(ord(c) < 0x21 or 0x7F <= ord(c) <= 0x9F or c.isspace() for c in url):
        return False
    try:
        parts = urlsplit(url)
        _ = parts.port
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.hostname)


def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(_BACKOFF * (2 ** attempt), _BACKOFF_CAP))


def _close_quiet(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _open_parent(destination: Path) -> int | None:
    absolute = destination.is_absolute()
    components = destination.parts[1:-1] if absolute else destination.parts[:-1]
    try:
        dfd = os.open("/" if absolute else ".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return None
    for component in components:
        try:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=dfd)
        except OSError:
            _close_quiet(dfd)
            return None
        _close_quiet(dfd)
        dfd = next_fd
    return dfd


def _open_file(dfd: int, name: str, append: bool, file_retries: int) -> Result[int, MediaError]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_APPEND if append else os.O_TRUNC)
    attempt = 0
    while True:
        try:
            fd = os.open(name, flags, 0o644, dir_fd=dfd)
        except OSError:
            if attempt >= file_retries:
                return Err(error=MediaError_OutputFailure(message="cannot open output file"))
            _sleep_backoff(attempt)
            attempt += 1
            continue
        try:
            regular = stat.S_ISREG(os.fstat(fd).st_mode)
        except OSError:
            regular = False
        if not regular:
            _close_quiet(fd)
            return Err(error=MediaError_OutputFailure(message="output is not a regular file"))
        return Ok(value=fd)


def _write_all(fd: int, chunk: bytes) -> bool:
    view = memoryview(chunk)
    try:
        while view:
            written = os.write(fd, view)
            if written <= 0:
                return False
            view = view[written:]
    except OSError:
        return False
    return True


def _connect(url: str, offset: int) -> Result[tuple[http.client.HTTPConnection, http.client.HTTPResponse], MediaError]:
    current = url
    for _ in range(_MAX_REDIRECTS + 1):
        if not _url_ok(current):
            return Err(error=MediaError_NetworkFailure(message="redirect to unsupported URL"))
        parts = urlsplit(current)
        host = parts.hostname or ""
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        headers = {"User-Agent": "yt-dlp", "Accept-Encoding": "identity"}
        if offset > 0:
            headers["Range"] = f"bytes={offset}-"
        connection: http.client.HTTPConnection
        if parts.scheme == "https":
            connection = http.client.HTTPSConnection(host, parts.port, timeout=_TIMEOUT, context=ssl.create_default_context())
        else:
            connection = http.client.HTTPConnection(host, parts.port, timeout=_TIMEOUT)
        try:
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
        except (OSError, ValueError, http.client.HTTPException, socket.timeout):
            connection.close()
            return Err(error=MediaError_NetworkFailure(message="connection failure"))
        if response.status in (301, 302, 303, 307, 308):
            location = response.getheader("Location")
            status = response.status
            connection.close()
            if location is None or location.strip() == "":
                return Err(error=MediaError_HttpStatus(status=status))
            current = urljoin(current, location.strip())
            continue
        return Ok(value=(connection, response))
    return Err(error=MediaError_NetworkFailure(message="too many redirects"))


def _stream(response: http.client.HTTPResponse, fd: int, policy: FragmentPolicy, start_total: int, limit: int) -> Result[int, MediaError]:
    read_size = policy.buffer_size if policy.chunk_size == 0 else min(policy.buffer_size, policy.chunk_size)
    rate = policy.rate_limit_bytes_per_second
    started = time.monotonic()
    received = 0
    total = start_total
    while True:
        try:
            chunk = response.read(read_size)
        except (OSError, ValueError, http.client.HTTPException, socket.timeout):
            return Err(error=MediaError_NetworkFailure(message="connection failure while reading body"))
        if not chunk:
            break
        total += len(chunk)
        received += len(chunk)
        if total > limit:
            return Err(error=MediaError_SizeLimit())
        if not _write_all(fd, chunk):
            return Err(error=MediaError_OutputFailure(message="cannot write output file"))
        if rate > 0:
            ahead = received / rate - (time.monotonic() - started)
            if ahead > 0:
                time.sleep(ahead)
    try:
        os.fsync(fd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message="cannot flush output file"))
    return Ok(value=received)


def _sync_existing(dfd: int, name: str, total: int) -> Result[int, MediaError]:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dfd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message="cannot open existing output file"))
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            return Err(error=MediaError_OutputFailure(message="output is not a regular file"))
        if info.st_size != total:
            return Err(error=MediaError_HttpStatus(status=416))
        os.fsync(fd)
    except OSError:
        return Err(error=MediaError_OutputFailure(message="cannot flush output file"))
    finally:
        _close_quiet(fd)
    return Ok(value=0)


def _decimal(text: str) -> int:
    return int(text) if text != "" and text.isascii() and text.isdigit() else -1


def _range_complete(content_range: str, offset: int) -> bool:
    unit, _, spec = content_range.strip().partition(" ")
    unsat, _, total = spec.strip().partition("/")
    return unit == "bytes" and unsat == "*" and _decimal(total) == offset


def _partial_span(content_range: str, offset: int) -> tuple[int, int]:
    unit, _, spec = content_range.strip().partition(" ")
    span, _, total_text = spec.strip().partition("/")
    first_text, dash, last_text = span.partition("-")
    first = _decimal(first_text)
    last = _decimal(last_text)
    total = _decimal(total_text)
    if unit != "bytes" or dash == "" or first != offset or last < first or total <= last:
        return (-1, -1)
    return (last - first + 1, total)


def _consume(response: http.client.HTTPResponse, policy: FragmentPolicy, dfd: int, name: str, offset: int, limit: int, known_total: int) -> Result[int, MediaError]:
    status = response.status
    if status == 416 and offset > 0:
        if not _range_complete(response.getheader("Content-Range") or "", offset):
            return Err(error=MediaError_HttpStatus(status=status))
        return _sync_existing(dfd, name, offset)
    if status < 200 or status > 299 or (status == 206 and offset == 0):
        return Err(error=MediaError_HttpStatus(status=status))
    append = status == 206
    length = response.getheader("Content-Length")
    expected = _decimal(length.strip() if length is not None else "")
    if length is not None and expected < 0:
        return Err(error=MediaError_NetworkFailure(message="malformed Content-Length"))
    resource_total = -1
    if append:
        span, resource_total = _partial_span(response.getheader("Content-Range") or "", offset)
        if span < 0 or (expected >= 0 and expected != span) or (known_total >= 0 and resource_total != known_total):
            return Err(error=MediaError_NetworkFailure(message="unexpected partial content range"))
        if resource_total > limit:
            return Err(error=MediaError_SizeLimit())
        expected = span
    start_total = offset if append else 0
    if expected >= 0 and start_total + expected > limit:
        return Err(error=MediaError_SizeLimit())
    streamed: Result[int, MediaError]
    match _open_file(dfd, name, append, policy.file_access_retries):
        case Err(error=open_error):
            return Err(error=open_error)
        case Ok(value=fd):
            try:
                streamed = _stream(response, fd, policy, start_total, limit)
            finally:
                _close_quiet(fd)
    match streamed:
        case Err(error=stream_error):
            return Err(error=stream_error)
        case Ok(value=received):
            if expected >= 0 and received != expected:
                return Err(error=MediaError_NetworkFailure(message="incomplete response body"))
            if append and offset + received < resource_total:
                return Ok(value=resource_total)
            return Ok(value=0)


def _existing_size(dfd: int, name: str) -> Result[int, MediaError]:
    try:
        info = os.stat(name, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        return Ok(value=0)
    except OSError:
        return Err(error=MediaError_OutputFailure(message="cannot inspect output file"))
    if not stat.S_ISREG(info.st_mode):
        return Err(error=MediaError_OutputFailure(message="output is not a regular file"))
    return Ok(value=info.st_size)


def _attempt(request: TransferRequest, policy: FragmentPolicy, dfd: int, name: str) -> Result[int, MediaError]:
    resume = policy.continue_download
    limit = request.max_bytes
    known_total = -1
    while True:
        offset = 0
        if resume:
            match _existing_size(dfd, name):
                case Err(error=size_error):
                    return Err(error=size_error)
                case Ok(value=size):
                    offset = size
        if offset > limit:
            return Err(error=MediaError_SizeLimit())
        outcome: Result[int, MediaError]
        match _connect(request.url, offset):
            case Err(error=connect_error):
                return Err(error=connect_error)
            case Ok(value=(connection, response)):
                try:
                    outcome = _consume(response, policy, dfd, name, offset, limit, known_total)
                finally:
                    response.close()
                    connection.close()
        match outcome:
            case Ok(value=0):
                return outcome
            case Ok(value=total):
                known_total = total
                resume = True
            case Err():
                return outcome


def _finish(request: TransferRequest, policy: FragmentPolicy, dfd: int, work: str, destination: Path) -> Result[TransferReceipt, MediaError]:
    target = destination.name
    if work != target:
        tries = 0
        while True:
            try:
                os.replace(work, target, src_dir_fd=dfd, dst_dir_fd=dfd)
                break
            except OSError:
                if tries >= policy.file_access_retries:
                    return Err(error=MediaError_OutputFailure(message="cannot rename part file"))
                _sleep_backoff(tries)
                tries += 1
        try:
            os.fsync(dfd)
        except OSError:
            return Err(error=MediaError_OutputFailure(message="cannot flush output directory"))
    try:
        info = os.stat(target, dir_fd=dfd, follow_symlinks=False)
    except OSError:
        return Err(error=MediaError_OutputFailure(message="cannot inspect output file"))
    if not stat.S_ISREG(info.st_mode):
        return Err(error=MediaError_OutputFailure(message="output is not a regular file"))
    return Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=info.st_size, simulated=False))


def _transfer_in(request: TransferRequest, policy: FragmentPolicy, retries: int, dfd: int, destination: Path) -> Result[TransferReceipt, MediaError]:
    work = destination.name + ".part" if policy.part_files else destination.name
    attempt = 0
    while True:
        # The work file only ever holds a contiguous verbatim body prefix: 200 truncates
        # and rewrites from 0, 206 appends at the checked offset, and write/fsync errors
        # are terminal OutputFailure. A retry therefore resumes from the file's actual size.
        match _attempt(request, policy, dfd, work):
            case Ok(value=_):
                return _finish(request, policy, dfd, work, destination)
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


def _transfer_one(request: TransferRequest, policy: FragmentPolicy, retries: int) -> Result[TransferReceipt, MediaError]:
    destination = Path(request.destination)
    if request.simulate:
        return Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=0, simulated=True))
    if os.name != "posix" or not (os.O_NOFOLLOW and os.O_DIRECTORY and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd and os.rename in os.supports_dir_fd):
        return Err(error=MediaError_OutputFailure(message="platform lacks descriptor-relative file operations"))
    dfd = _open_parent(destination)
    if dfd is None:
        return Err(error=MediaError_OutputFailure(message="cannot open output directory without following symlinks"))
    try:
        return _transfer_in(request, policy, retries, dfd, destination)
    finally:
        _close_quiet(dfd)


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
            return Err(error=MediaError_InvalidInput(message="destination has no file name"))
        key = os.path.abspath(destination)
        if key in seen:
            return Err(error=MediaError_InvalidInput(message="duplicate fragment destination"))
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
