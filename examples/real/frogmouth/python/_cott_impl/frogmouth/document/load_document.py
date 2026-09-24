import urllib.error
import urllib.request
from pathlib import PurePosixPath
from typing import Final

from cott_runtime import Err, Ok, Result
from frogmouth.document_types import LoadError, LoadError_InvalidEncoding, LoadError_NetworkFailed, LoadError_NotFound, LoadError_ReadFailed, LoadError_TooLarge
from frogmouth.model_types import Document, Location, LocationKind_Http

_MAX_BYTES: Final[int] = 5242880
_FALLBACK_TITLE: Final[str] = "Untitled"


def _heading_title(markdown: str) -> str:
    in_fence = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not line.startswith("#"):
            continue
        hashes = len(line) - len(line.lstrip("#"))
        rest = line[hashes:]
        if hashes > 6 or (rest and not rest[0].isspace()):
            continue
        title = rest.strip().rstrip("#").strip()
        if title:
            return title
    return ""


def _fallback_title(target: str) -> str:
    name = PurePosixPath(target.split("?", 1)[0].split("#", 1)[0].rstrip("/")).name
    return name if name else _FALLBACK_TITLE


def _read_http(target: str) -> Result[bytes, LoadError]:
    try:
        with urllib.request.urlopen(target) as response:
            data: bytes = response.read(_MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code in (404, 410):
            return Err(error=LoadError_NotFound(source=target))
        return Err(error=LoadError_NetworkFailed(source=target, message=str(error)))
    except (urllib.error.URLError, OSError, ValueError) as error:
        return Err(error=LoadError_NetworkFailed(source=target, message=str(error)))
    return Ok(value=data)


def _read_local(target: str) -> Result[bytes, LoadError]:
    try:
        with open(target, "rb") as handle:
            data = handle.read(_MAX_BYTES + 1)
    except (FileNotFoundError, NotADirectoryError):
        return Err(error=LoadError_NotFound(source=target))
    except (OSError, ValueError) as error:
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
        markdown = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=LoadError_InvalidEncoding(source=target))
    title = _heading_title(markdown) or _fallback_title(target)
    return Ok(value=Document(location=location, title=title, markdown=markdown))
