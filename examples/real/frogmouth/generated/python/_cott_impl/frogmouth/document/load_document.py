import http.client
import urllib.error
import urllib.request
from typing import Final

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_read
from frogmouth.document import derive_title
from frogmouth.document_types import LoadError, LoadError_InvalidEncoding, LoadError_NetworkFailed, LoadError_NotFound, LoadError_ReadFailed, LoadError_TooLarge
from frogmouth.model_types import Document, Location, LocationKind_Http

_MAX_BYTES: Final[int] = 5242880
_TIMEOUT_SECONDS: Final[float] = 30.0
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _status_error(target: str, status: int) -> LoadError:
    if status in (404, 410):
        return LoadError_NotFound(source=target)
    return LoadError_NetworkFailed(source=target, message=f"HTTP status {status}")


def _read_http(target: str) -> Result[bytes, LoadError]:
    try:
        with urllib.request.urlopen(target, timeout=_TIMEOUT_SECONDS) as response:
            status: int = response.status
            if status < 200 or status > 299:
                return Err(error=_status_error(target, status))
            chunks: list[bytes] = []
            total: int = 0
            while total <= _MAX_BYTES:
                chunk: bytes = response.read(_MAX_BYTES + 1 - total)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            data: bytes = b"".join(chunks)
    except urllib.error.HTTPError as error:
        return Err(error=_status_error(target, error.code))
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as error:
        return Err(error=LoadError_NetworkFailed(source=target, message=str(error)))
    return Ok(value=data)


def _read_host(target: str) -> Result[bytes, LoadError]:
    try:
        with open(target, "rb") as handle:
            data: bytes = handle.read(_MAX_BYTES + 1)
    except FileNotFoundError:
        return Err(error=LoadError_NotFound(source=target))
    except (OSError, ValueError) as error:
        return Err(error=LoadError_ReadFailed(source=target, message=str(error)))
    return Ok(value=data)


def _read_local(target: str) -> Result[bytes, LoadError]:
    try:
        data: bytes = _cott_fixture_read(target)
    except CottContractViolation as violation:
        if violation.message == _INACTIVE:
            return _read_host(target)
        cause: BaseException | None = violation.__cause__
        if isinstance(cause, FileNotFoundError):
            return Err(error=LoadError_NotFound(source=target))
        if isinstance(cause, OSError):
            return Err(error=LoadError_ReadFailed(source=target, message=str(cause)))
        raise
    except OSError as error:
        return Err(error=LoadError_ReadFailed(source=target, message=str(error)))
    return Ok(value=data)


def load_document(location: Location) -> Result[Document, LoadError]:
    target = location.target
    if isinstance(location.kind, LocationKind_Http):
        read = _read_http(target)
    else:
        read = _read_local(target)
    if isinstance(read, Err):
        return read
    data = read.value
    if len(data) > _MAX_BYTES:
        return Err(error=LoadError_TooLarge(source=target))
    try:
        markdown = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return Err(error=LoadError_InvalidEncoding(source=target))
    if markdown.startswith("\ufeff"):
        markdown = markdown[1:]
    title = derive_title(location, markdown)
    return Ok(value=Document(location=location, title=title, markdown=markdown))
