from pathlib import Path
from typing import Final

from cott_runtime import Err, Ok, Result
from frogmouth.document_types import (
    LoadError,
    LoadError_InvalidEncoding,
    LoadError_InvalidLocation,
    LoadError_NotFound,
    LoadError_PermissionDenied,
    LoadError_TooLarge,
)

_MAX_MARKDOWN_BYTES: Final[int] = 5242880


def load_local_markdown(path: str) -> Result[str, LoadError]:
    if not path:
        return Err(error=LoadError_InvalidLocation(message="local path must not be empty"))
    if "\x00" in path:
        return Err(error=LoadError_InvalidLocation(message="local path must not contain a null character"))

    source = Path(path)
    if not source.exists():
        return Err(error=LoadError_NotFound(source=path))
    if not source.is_file():
        return Err(error=LoadError_InvalidLocation(message="local path must refer to a regular file"))

    metadata = source.stat()
    if metadata.st_mode & 0o444 == 0:
        return Err(error=LoadError_PermissionDenied(source=path))
    if metadata.st_size > _MAX_MARKDOWN_BYTES:
        return Err(error=LoadError_TooLarge(source=path))

    with open(source, "rb") as markdown_file:
        body = markdown_file.read(_MAX_MARKDOWN_BYTES + 1)
    if len(body) > _MAX_MARKDOWN_BYTES:
        return Err(error=LoadError_TooLarge(source=path))

    markdown = body.decode("utf-8", errors="surrogateescape")
    for character in markdown:
        if 0xDC80 <= ord(character) <= 0xDCFF:
            return Err(error=LoadError_InvalidEncoding(source=path))
    return Ok(value=markdown)
