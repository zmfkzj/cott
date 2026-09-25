import http.client
import ssl
import urllib.parse
import uuid
from pathlib import Path
from typing import BinaryIO, Final

from cott_runtime import Err, Ok, Result, U64
from real.yt_dlp_types import MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_UnsupportedUrl, TransferReceipt, TransferRequest

_CHUNK_SIZE: Final[int] = 65536
_TIMEOUT_SECONDS: Final[float] = 30.0
_MAX_REDIRECTS: Final[int] = 5


def _valid_url(url: str) -> bool:
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.hostname)


def _connect(url: str) -> http.client.HTTPConnection | MediaError:
    try:
        parsed = urllib.parse.urlsplit(url)
        host: str | None = parsed.hostname
        port: int | None = parsed.port
    except ValueError:
        return MediaError_NetworkFailure(message="invalid redirect target")
    if host is None:
        return MediaError_NetworkFailure(message="invalid redirect target")
    if parsed.scheme == "https":
        return http.client.HTTPSConnection(host, port, timeout=_TIMEOUT_SECONDS, context=ssl.create_default_context())
    return http.client.HTTPConnection(host, port, timeout=_TIMEOUT_SECONDS)


def _open(url: str) -> tuple[http.client.HTTPConnection, http.client.HTTPResponse] | MediaError:
    current: str = url
    redirects: int = 0
    while True:
        conn = _connect(current)
        if not isinstance(conn, http.client.HTTPConnection):
            return conn
        parsed = urllib.parse.urlsplit(current)
        target: str = parsed.path or "/"
        if parsed.query:
            target = target + "?" + parsed.query
        try:
            conn.request("GET", target)
            response: http.client.HTTPResponse = conn.getresponse()
        except ssl.SSLError:
            conn.close()
            return MediaError_NetworkFailure(message="TLS handshake or certificate verification failed")
        except TimeoutError:
            conn.close()
            return MediaError_NetworkFailure(message="connection timed out")
        except (OSError, http.client.HTTPException, ValueError):
            conn.close()
            return MediaError_NetworkFailure(message="connection failed")
        if response.status in (301, 302, 303, 307, 308):
            location: str | None = response.getheader("Location")
            conn.close()
            if location is None:
                return MediaError_NetworkFailure(message="redirect without location")
            redirects = redirects + 1
            if redirects > _MAX_REDIRECTS:
                return MediaError_NetworkFailure(message="too many redirects")
            next_url: str = urllib.parse.urljoin(current, location)
            if not _valid_url(next_url):
                return MediaError_NetworkFailure(message="invalid redirect target")
            current = next_url
            continue
        return (conn, response)


def _stream(response: http.client.HTTPResponse, handle: BinaryIO, max_bytes: int) -> int | MediaError:
    written: int = 0
    while True:
        try:
            chunk: bytes = response.read(_CHUNK_SIZE)
        except TimeoutError:
            return MediaError_NetworkFailure(message="read timed out")
        except (OSError, http.client.HTTPException, ValueError):
            return MediaError_NetworkFailure(message="failed to read response body")
        if not chunk:
            return written
        if written + len(chunk) > max_bytes:
            return MediaError_SizeLimit()
        try:
            handle.write(chunk)
        except OSError:
            return MediaError_OutputFailure(message="failed to write temporary file")
        written = written + len(chunk)


def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    if request.max_bytes == 0:
        return Err(error=MediaError_InvalidInput(message="max_bytes must be greater than zero"))
    if not _valid_url(request.url):
        return Err(error=MediaError_UnsupportedUrl())
    if request.simulate:
        return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=0, simulated=True))
    destination: Path = Path(request.destination)
    opened = _open(request.url)
    if not isinstance(opened, tuple):
        return Err(error=opened)
    conn, response = opened
    try:
        status: int = response.status
        if status < 200 or status >= 300:
            return Err(error=MediaError_HttpStatus(status=status))
        declared: str | None = response.getheader("Content-Length")
        if declared is not None and declared.strip().isdigit() and int(declared.strip()) > request.max_bytes:
            return Err(error=MediaError_SizeLimit())
        temp_path: Path = destination.parent / f".{destination.name}.{uuid.uuid4().hex}.part"
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            return Err(error=MediaError_OutputFailure(message="failed to create destination directory"))
        try:
            handle: BinaryIO = temp_path.open("xb")
        except OSError:
            return Err(error=MediaError_OutputFailure(message="failed to open temporary file"))
        outcome: int | MediaError
        try:
            with handle:
                outcome = _stream(response, handle, request.max_bytes)
        except OSError:
            outcome = MediaError_OutputFailure(message="failed to write temporary file")
        if isinstance(outcome, int):
            try:
                temp_path.replace(destination)
            except OSError:
                outcome = MediaError_OutputFailure(message="failed to replace destination")
        if not isinstance(outcome, int):
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                return Err(error=MediaError_OutputFailure(message="failed to remove temporary file"))
            return Err(error=outcome)
        written: U64 = outcome
        return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=written, simulated=False))
    finally:
        conn.close()
