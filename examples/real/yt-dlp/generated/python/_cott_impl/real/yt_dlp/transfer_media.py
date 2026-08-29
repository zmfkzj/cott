import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_UnsupportedUrl, TransferReceipt, TransferRequest


def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    if request.max_bytes == 0:
        return Err(error=MediaError_InvalidInput(message="max_bytes must be greater than zero"))

    try:
        parsed = urllib.parse.urlsplit(request.url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return Err(error=MediaError_UnsupportedUrl())

    if parsed.scheme not in ("http", "https") or hostname is None or hostname == "":
        return Err(error=MediaError_UnsupportedUrl())

    url_index = 0
    while url_index < len(request.url):
        character = request.url[url_index]
        if character.isspace() or ord(character) < 32 or ord(character) == 127:
            return Err(error=MediaError_UnsupportedUrl())
        if character == "%":
            if url_index + 2 >= len(request.url):
                return Err(error=MediaError_UnsupportedUrl())
            if request.url[url_index + 1] not in "0123456789abcdefABCDEF" or request.url[url_index + 2] not in "0123456789abcdefABCDEF":
                return Err(error=MediaError_UnsupportedUrl())
            url_index += 3
        else:
            url_index += 1

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
    transfer_error: MediaError | None = None
    bytes_written = 0
    try:
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("wb", -1, None, None, None, ".cott-transfer-", request.destination.parent, False) as output:
            temporary_path = Path(output.name)
            try:
                with urllib.request.urlopen(request.url) as response:
                    status = response.getcode()
                    if status is None:
                        transfer_error = MediaError_NetworkFailure(message="HTTP response has no status")
                    elif status < 200 or status > 299:
                        transfer_error = MediaError_HttpStatus(status=status)
                    else:
                        while transfer_error is None:
                            try:
                                chunk = response.read(65536)
                            except (urllib.error.URLError, OSError) as error:
                                transfer_error = MediaError_NetworkFailure(message=str(error))
                                break
                            if chunk == b"":
                                break
                            next_size = bytes_written + len(chunk)
                            if next_size > request.max_bytes:
                                transfer_error = MediaError_SizeLimit()
                                break
                            try:
                                written = output.write(chunk)
                                if written != len(chunk):
                                    transfer_error = MediaError_OutputFailure(message="temporary file write was incomplete")
                                    break
                            except OSError as error:
                                transfer_error = MediaError_OutputFailure(message=str(error))
                                break
                            bytes_written = next_size
            except urllib.error.HTTPError as error:
                transfer_error = MediaError_HttpStatus(status=error.code)
            except urllib.error.URLError as error:
                transfer_error = MediaError_NetworkFailure(message=str(error))
            except ValueError:
                transfer_error = MediaError_UnsupportedUrl()
            except OSError as error:
                transfer_error = MediaError_NetworkFailure(message=str(error))

        if transfer_error is None:
            os.replace(temporary_path, request.destination)
            temporary_path = None
    except OSError as error:
        transfer_error = MediaError_OutputFailure(message=str(error))
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as error:
                transfer_error = MediaError_OutputFailure(message=str(error))

    if transfer_error is not None:
        return Err(error=transfer_error)
    return Ok(
        value=TransferReceipt(
            url=request.url,
            destination=request.destination,
            bytes_written=bytes_written,
            simulated=False,
        )
    )
