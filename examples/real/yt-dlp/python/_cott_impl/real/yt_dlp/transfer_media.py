import http.client
import os
import re
import secrets
import ssl
from pathlib import Path
from typing import Final
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit

import cott_runtime
from cott_runtime import Result, U64
from real.yt_dlp_types import MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_UnsupportedUrl, TransferReceipt, TransferRequest

_CHUNK: Final[int] = 65536
_TIMEOUT: Final[float] = 30.0
_NETWORK: Final[str] = "media network transfer failed"
_OUTPUT: Final[str] = "media output operation failed"


def _valid_url(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    if any(char.isspace() or ord(char) < 32 or 127 <= ord(char) <= 159 for char in url):
        return False
    try:
        parts = urlsplit(url)
        return bool(parts.hostname) and (parts.port is None or 0 < parts.port <= 65535)
    except ValueError:
        return False


def _declared_length(response: http.client.HTTPResponse, limit: U64) -> Result[U64 | None, MediaError]:
    header: str | None = response.getheader("Content-Length")
    if header is None:
        return cott_runtime.Ok(value=None)
    value: str = header.strip()
    if not value or not value.isascii() or not value.isdecimal():
        return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
    digits: str = value.lstrip("0") or "0"
    bound: str = str(limit)
    if len(digits) > len(bound) or (len(digits) == len(bound) and digits > bound):
        return cott_runtime.Err(error=MediaError_SizeLimit())
    return cott_runtime.Ok(value=int(digits))


def _stream_response(response: http.client.HTTPResponse, fd: int, limit: U64, declared: U64 | None) -> Result[U64, MediaError]:
    written: U64 = 0
    while True:
        try:
            block: bytes = response.read(min(_CHUNK, limit - written + 1))
        except (OSError, http.client.HTTPException, ValueError):
            return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
        if not block:
            if declared is not None and written != declared:
                return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
            return cott_runtime.Ok(value=written)
        if written + len(block) > limit:
            return cott_runtime.Err(error=MediaError_SizeLimit())
        view: memoryview = memoryview(block)
        offset: int = 0
        while offset < len(view):
            try:
                size: int = os.write(fd, view[offset:])
            except OSError:
                return cott_runtime.Err(error=MediaError_OutputFailure(message=_OUTPUT))
            if size <= 0:
                return cott_runtime.Err(error=MediaError_OutputFailure(message=_OUTPUT))
            offset += size
        written += len(block)


def _receive_response(request: TransferRequest, response: http.client.HTTPResponse, declared: U64 | None) -> Result[TransferReceipt, MediaError]:
    destination: Path = request.destination
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path = destination.parent / ("." + destination.name + "." + secrets.token_hex(16) + ".tmp")
        fd: int = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except (OSError, ValueError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message=_OUTPUT))

    failure: MediaError | None = None
    written: U64 = 0
    try:
        streamed: Result[U64, MediaError] = _stream_response(response, fd, request.max_bytes, declared)
        match streamed:
            case cott_runtime.Err(error=error):
                failure = error
            case cott_runtime.Ok(value=count):
                written = count
                try:
                    os.fsync(fd)
                except OSError:
                    failure = MediaError_OutputFailure(message=_OUTPUT)
    finally:
        try:
            os.close(fd)
        except OSError:
            failure = MediaError_OutputFailure(message=_OUTPUT)

    if failure is None:
        try:
            response.close()
        except (OSError, http.client.HTTPException, ValueError):
            failure = MediaError_NetworkFailure(message=_NETWORK)
    if failure is None:
        try:
            os.replace(temporary, destination)
        except (OSError, ValueError):
            failure = MediaError_OutputFailure(message=_OUTPUT)
    if failure is not None:
        try:
            temporary.unlink()
        except OSError:
            return cott_runtime.Err(error=MediaError_OutputFailure(message=_OUTPUT))
        return cott_runtime.Err(error=failure)
    return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=destination, bytes_written=written, simulated=False))


def _close_connection(connection: http.client.HTTPConnection) -> None:
    try:
        connection.close()
    except (OSError, http.client.HTTPException, ValueError):
        return


def _host_transfer(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    try:
        context: ssl.SSLContext = ssl.create_default_context()
    except (OSError, ValueError):
        return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
    current: str = request.url
    redirects: int = 0
    while True:
        connection: http.client.HTTPConnection | None = None
        try:
            parts = urlsplit(current)
            host: str | None = parts.hostname
            if host is None:
                return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
            if parts.scheme == "https":
                connection = http.client.HTTPSConnection(host, parts.port, timeout=_TIMEOUT, context=context)
            else:
                connection = http.client.HTTPConnection(host, parts.port, timeout=_TIMEOUT)
            target: str = parts.path or "/"
            if parts.query:
                target += "?" + parts.query
            connection.request("GET", target, headers={"Accept-Encoding": "identity"})
            response: http.client.HTTPResponse = connection.getresponse()
            status: int = response.status
            if status in (301, 302, 303, 307, 308):
                location: str | None = response.getheader("Location")
                if not location or redirects >= 5:
                    return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
                following: str = urljoin(current, location)
                if not _valid_url(following):
                    return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
                current = following
                redirects += 1
                continue
            if not 200 <= status < 300:
                return cott_runtime.Err(error=MediaError_HttpStatus(status=status))
            length_result: Result[U64 | None, MediaError] = _declared_length(response, request.max_bytes)
            match length_result:
                case cott_runtime.Err(error=error):
                    return cott_runtime.Err(error=error)
                case cott_runtime.Ok(value=declared):
                    return _receive_response(request, response, declared)
        except (OSError, http.client.HTTPException, ValueError, UnicodeError):
            return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
        finally:
            if connection is not None:
                _close_connection(connection)


def _fixture_http_error(failure: cott_runtime.CottContractViolation) -> Result[TransferReceipt, MediaError]:
    cause: BaseException | None = failure.__cause__
    if isinstance(cause, HTTPError):
        return cott_runtime.Err(error=MediaError_HttpStatus(status=cause.code))
    status: re.Match[str] | None = re.fullmatch(r"HTTP(?: response)?(?: status)?[ :]+([0-9]{3})", failure.message, re.IGNORECASE)
    if status is not None:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=int(status.group(1))))
    return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))


def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    if request.max_bytes == 0:
        return cott_runtime.Err(error=MediaError_InvalidInput(message="max_bytes must be greater than zero"))
    if not _valid_url(request.url):
        return cott_runtime.Err(error=MediaError_UnsupportedUrl())
    if request.simulate:
        return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=0, simulated=True))
    if not request.destination.name:
        return cott_runtime.Err(error=MediaError_OutputFailure(message=_OUTPUT))
    try:
        body: bytes = cott_runtime._cott_fixture_http(request.url)
    except cott_runtime.CottContractViolation as failure:
        if failure.message == "fixture adapters are inactive":
            return _host_transfer(request)
        return _fixture_http_error(failure)
    except HTTPError as http_error:
        return cott_runtime.Err(error=MediaError_HttpStatus(status=http_error.code))
    except OSError:
        return cott_runtime.Err(error=MediaError_NetworkFailure(message=_NETWORK))
    if len(body) > request.max_bytes:
        return cott_runtime.Err(error=MediaError_SizeLimit())
    try:
        cott_runtime._cott_fixture_replace(request.destination, body)
    except (cott_runtime.CottContractViolation, OSError):
        return cott_runtime.Err(error=MediaError_OutputFailure(message=_OUTPUT))
    return cott_runtime.Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=len(body), simulated=False))
