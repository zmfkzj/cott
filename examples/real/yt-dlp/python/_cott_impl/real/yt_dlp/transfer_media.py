import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Final

from cott_runtime import Err, Ok, Result, U64
from real.yt_dlp_types import MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_UnsupportedUrl, TransferReceipt, TransferRequest

_CHUNK_SIZE: Final[int] = 65536
_TIMEOUT_SECONDS: Final[float] = 30.0


def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    if request.max_bytes == 0:
        return Err(error=MediaError_InvalidInput(message="max_bytes must be greater than zero"))
    parsed = urllib.parse.urlparse(request.url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return Err(error=MediaError_UnsupportedUrl())
    if request.simulate:
        return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=0, simulated=True))
    destination: Path = Path(request.destination)
    try:
        response = urllib.request.urlopen(request.url, timeout=_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as http_error:
        return Err(error=MediaError_HttpStatus(status=http_error.code))
    except (urllib.error.URLError, OSError, ValueError) as network_error:
        return Err(error=MediaError_NetworkFailure(message=str(network_error)))
    with response:
        status: int = response.status
        if status < 200 or status >= 300:
            return Err(error=MediaError_HttpStatus(status=status))
        declared_length: str | None = response.headers.get("Content-Length")
        if declared_length is not None and declared_length.isdigit() and int(declared_length) > request.max_bytes:
            return Err(error=MediaError_SizeLimit())
        temp_path: Path = destination.parent / f".part-{uuid.uuid4().hex}-{destination.name}"
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            handle = temp_path.open("xb")
        except OSError as mk_error:
            return Err(error=MediaError_OutputFailure(message=str(mk_error)))
        written: U64 = 0
        failure: MediaError | None = None
        try:
            with handle:
                while True:
                    try:
                        chunk: bytes = response.read(_CHUNK_SIZE)
                    except (OSError, ValueError) as read_error:
                        failure = MediaError_NetworkFailure(message=str(read_error))
                        break
                    if not chunk:
                        break
                    if written + len(chunk) > request.max_bytes:
                        failure = MediaError_SizeLimit()
                        break
                    handle.write(chunk)
                    written = written + len(chunk)
            if failure is None:
                temp_path.replace(destination)
        except OSError as write_error:
            failure = MediaError_OutputFailure(message=str(write_error))
        if failure is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                return Err(error=MediaError_OutputFailure(message=f"failed to remove partial file {temp_path}: {cleanup_error}"))
            return Err(error=failure)
    return Ok(value=TransferReceipt(url=request.url, destination=request.destination, bytes_written=written, simulated=False))
