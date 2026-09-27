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
from cott_runtime import Err, Ok, Result, U64
from real.yt_dlp_types import MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_UnsupportedUrl, TransferReceipt, TransferRequest

_CHUNK_SIZE: Final[int] = 65536
_TIMEOUT_SECONDS: Final[float] = 30.0
_MAX_REDIRECTS: Final[int] = 5
_INACTIVE_FIXTURE: Final[str] = "fixture adapters are inactive"
_NETWORK_ERROR: Final[str] = "media network transfer failed"
_OUTPUT_ERROR: Final[str] = "media output operation failed"


def _valid_url(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    if any(character.isspace() or ord(character) < 32 or 127 <= ord(character) <= 159 for character in url):
        return False
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError:
        return False
    return bool(host) and (port is None or port > 0)


def _close_response(connection: http.client.HTTPConnection, response: http.client.HTTPResponse) -> bool:
    closed = True
    try:
        response.close()
    except (OSError, http.client.HTTPException, ValueError):
        closed = False
    try:
        connection.close()
    except (OSError, http.client.HTTPException, ValueError):
        closed = False
    return closed


def _open_response(url: str, context: ssl.SSLContext) -> tuple[http.client.HTTPConnection, http.client.HTTPResponse] | MediaError:
    current = url
    redirects = 0
    while True:
        if not _valid_url(current):
            return MediaError_NetworkFailure(message=_NETWORK_ERROR)
        connection: http.client.HTTPConnection | None = None
        try:
            parts = urlsplit(current)
            host = parts.hostname
            if host is None:
                return MediaError_NetworkFailure(message=_NETWORK_ERROR)
            if parts.scheme == "https":
                connection = http.client.HTTPSConnection(host, parts.port, timeout=_TIMEOUT_SECONDS, context=context)
            else:
                connection = http.client.HTTPConnection(host, parts.port, timeout=_TIMEOUT_SECONDS)
            target = parts.path or "/"
            if parts.query:
                target += "?" + parts.query
            connection.request("GET", target, headers={"Accept-Encoding": "identity"})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not _close_response(connection, response):
                    return MediaError_NetworkFailure(message=_NETWORK_ERROR)
                if not location or redirects >= _MAX_REDIRECTS:
                    return MediaError_NetworkFailure(message=_NETWORK_ERROR)
                current = urljoin(current, location)
                redirects += 1
                continue
            return (connection, response)
        except (OSError, http.client.HTTPException, ValueError, UnicodeError):
            if connection is not None:
                try:
                    connection.close()
                except (OSError, http.client.HTTPException, ValueError):
                    return MediaError_NetworkFailure(message=_NETWORK_ERROR)
            return MediaError_NetworkFailure(message=_NETWORK_ERROR)


def _declared_length(response: http.client.HTTPResponse, max_bytes: U64) -> tuple[U64 | None, MediaError | None]:
    try:
        header = response.getheader("Content-Length")
    except (OSError, http.client.HTTPException, ValueError):
        return (None, MediaError_NetworkFailure(message=_NETWORK_ERROR))
    if header is None:
        return (None, None)
    digits = header.strip()
    if not digits or not digits.isascii() or not digits.isdecimal():
        return (None, MediaError_NetworkFailure(message=_NETWORK_ERROR))
    significant = digits.lstrip("0") or "0"
    bound = str(max_bytes)
    if len(significant) > len(bound) or (len(significant) == len(bound) and significant > bound):
        return (None, MediaError_SizeLimit())
    return (int(significant), None)


def _write_all(fd: int, block: bytes) -> bool:
    view = memoryview(block)
    offset = 0
    while offset < len(view):
        try:
            written = os.write(fd, view[offset:])
        except OSError:
            return False
        if written <= 0:
            return False
        offset += written
    return True


def _stream(response: http.client.HTTPResponse, fd: int, max_bytes: U64, declared: U64 | None) -> U64 | MediaError:
    written = 0
    while True:
        try:
            block = response.read(min(_CHUNK_SIZE, max_bytes - written + 1))
        except (OSError, http.client.HTTPException, ValueError):
            return MediaError_NetworkFailure(message=_NETWORK_ERROR)
        if not block:
            break
        if written + len(block) > max_bytes:
            return MediaError_SizeLimit()
        if not _write_all(fd, block):
            return MediaError_OutputFailure(message=_OUTPUT_ERROR)
        written += len(block)
    if declared is not None and written != declared:
        return MediaError_NetworkFailure(message=_NETWORK_ERROR)
    return written


def _remove_temp(path: Path) -> bool:
    try:
        path.unlink()
    except (OSError, ValueError):
        return False
    return True


def _save_response(request: TransferRequest, response: http.client.HTTPResponse, declared: U64 | None) -> tuple[Path, U64] | MediaError:
    destination = request.destination
    if not destination.name:
        return MediaError_OutputFailure(message=_OUTPUT_ERROR)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.parent / ("." + destination.name + "." + secrets.token_hex(16) + ".tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except (OSError, ValueError, AttributeError):
        return MediaError_OutputFailure(message=_OUTPUT_ERROR)
    outcome = _stream(response, fd, request.max_bytes, declared)
    if isinstance(outcome, int):
        try:
            os.fsync(fd)
        except OSError:
            outcome = MediaError_OutputFailure(message=_OUTPUT_ERROR)
    try:
        os.close(fd)
    except OSError:
        outcome = MediaError_OutputFailure(message=_OUTPUT_ERROR)
    if not isinstance(outcome, int):
        if not _remove_temp(temp):
            return MediaError_OutputFailure(message=_OUTPUT_ERROR)
        return outcome
    return (temp, outcome)


def _transfer_host(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    try:
        context = ssl.create_default_context()
    except (OSError, ValueError):
        return Err(error=MediaError_NetworkFailure(message=_NETWORK_ERROR))
    opened = _open_response(request.url, context)
    if not isinstance(opened, tuple):
        return Err(error=opened)
    connection, response = opened
    if not 200 <= response.status < 300:
        status = response.status
        _close_response(connection, response)
        return Err(error=MediaError_HttpStatus(status=status))
    declared, header_error = _declared_length(response, request.max_bytes)
    if header_error is not None:
        _close_response(connection, response)
        return Err(error=header_error)
    saved = _save_response(request, response, declared)
    closed = _close_response(connection, response)
    if not isinstance(saved, tuple):
        return Err(error=saved)
    temp, written = saved
    if not closed:
        if not _remove_temp(temp):
            return Err(error=MediaError_OutputFailure(message=_OUTPUT_ERROR))
        return Err(error=MediaError_NetworkFailure(message=_NETWORK_ERROR))
    try:
        os.replace(temp, request.destination)
    except (OSError, ValueError):
        if not _remove_temp(temp):
            return Err(error=MediaError_OutputFailure(message=_OUTPUT_ERROR))
        return Err(error=MediaError_OutputFailure(message=_OUTPUT_ERROR))
    return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=written, simulated=False))


def _fixture_http_error(violation: cott_runtime.CottContractViolation) -> MediaError:
    cause = violation.__cause__
    if isinstance(cause, HTTPError):
        return MediaError_HttpStatus(status=cause.code)
    status = re.fullmatch(r"HTTP(?: response)?(?: status)?[ :]+([0-9]{3})", violation.message, re.IGNORECASE)
    if status is not None:
        return MediaError_HttpStatus(status=int(status.group(1)))
    return MediaError_NetworkFailure(message=_NETWORK_ERROR)


def _transfer_fixture(request: TransferRequest, body: bytes) -> Result[TransferReceipt, MediaError]:
    if len(body) > request.max_bytes:
        return Err(error=MediaError_SizeLimit())
    try:
        cott_runtime._cott_fixture_replace(request.destination, body)
    except (cott_runtime.CottContractViolation, OSError):
        return Err(error=MediaError_OutputFailure(message=_OUTPUT_ERROR))
    return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=len(body), simulated=False))


def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    if request.max_bytes == 0:
        return Err(error=MediaError_InvalidInput(message="max_bytes must be greater than zero"))
    if not _valid_url(request.url):
        return Err(error=MediaError_UnsupportedUrl())
    if request.simulate:
        return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=0, simulated=True))
    try:
        body = cott_runtime._cott_fixture_http(request.url)
    except cott_runtime.CottContractViolation as violation:
        if violation.message == _INACTIVE_FIXTURE:
            return _transfer_host(request)
        return Err(error=_fixture_http_error(violation))
    except HTTPError as error:
        return Err(error=MediaError_HttpStatus(status=error.code))
    except OSError:
        return Err(error=MediaError_NetworkFailure(message=_NETWORK_ERROR))
    return _transfer_fixture(request, body)
