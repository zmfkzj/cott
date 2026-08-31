from __future__ import annotations

import http.client
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import (
    MediaError,
    MediaError_HttpStatus,
    MediaError_InvalidInput,
    MediaError_NetworkFailure,
    MediaError_OutputFailure,
    MediaError_SizeLimit,
    MediaError_UnsupportedUrl,
    TransferReceipt,
    TransferRequest,
)


def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    invalid_url = _validate_url(request)
    if invalid_url is not None:
        return Err(error=invalid_url)

    if request.simulate:
        return Ok(
            value=TransferReceipt(
                url=request.url,
                destination=request.destination,
                bytes_written=0,
                simulated=True,
            )
        )

    temporary_path: Path | None = None
    failure: MediaError | None = None
    bytes_written = 0
    try:
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp("", ".cott-transfer-", request.destination.parent)
        temporary_path = Path(name)
        with os.fdopen(fd, "wb") as output:
            try:
                with urllib.request.urlopen(request.url) as response:
                    status = response.getcode()
                    if status is None:
                        failure = MediaError_NetworkFailure(message="HTTP response has no status")
                    elif status < 200 or status > 299:
                        failure = MediaError_HttpStatus(status=status)
                    else:
                        while failure is None:
                            try:
                                chunk = response.read(65536)
                            except (http.client.HTTPException, OSError) as error:
                                failure = MediaError_NetworkFailure(message=str(error))
                                break
                            if chunk == b"":
                                break
                            if bytes_written + len(chunk) > request.max_bytes:
                                failure = MediaError_SizeLimit()
                                break
                            try:
                                if output.write(chunk) != len(chunk):
                                    failure = MediaError_OutputFailure(message="temporary file write was incomplete")
                                    break
                            except OSError as error:
                                failure = MediaError_OutputFailure(message=str(error))
                                break
                            bytes_written += len(chunk)
            except urllib.error.HTTPError as error:
                failure = MediaError_HttpStatus(status=error.code)
            except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
                failure = MediaError_NetworkFailure(message=str(error))

        if failure is None:
            os.replace(temporary_path, request.destination)
            temporary_path = None
    except OSError as error:
        failure = MediaError_OutputFailure(message=str(error))
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as error:
                if failure is None:
                    failure = MediaError_OutputFailure(message=str(error))

    if failure is not None:
        return Err(error=failure)
    return Ok(
        value=TransferReceipt(
            url=request.url,
            destination=request.destination,
            bytes_written=bytes_written,
            simulated=False,
        )
    )


def _validate_url(request: TransferRequest) -> MediaError | None:
    if request.max_bytes == 0:
        return MediaError_InvalidInput(message="max_bytes must be greater than zero")
    try:
        parsed = urllib.parse.urlsplit(request.url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return MediaError_UnsupportedUrl()
    if parsed.scheme not in ("http", "https") or hostname is None or hostname == "":
        return MediaError_UnsupportedUrl()

    index = 0
    while index < len(request.url):
        character = request.url[index]
        if character.isspace() or ord(character) < 32 or ord(character) == 127:
            return MediaError_UnsupportedUrl()
        if character == "%":
            if index + 2 >= len(request.url) or request.url[index + 1] not in "0123456789abcdefABCDEF" or request.url[index + 2] not in "0123456789abcdefABCDEF":
                return MediaError_UnsupportedUrl()
            index += 3
        else:
            index += 1
    return None
