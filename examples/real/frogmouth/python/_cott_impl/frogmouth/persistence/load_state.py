from pathlib import Path

from cott_runtime import Err, Result
from frogmouth.model_types import BrowserState
from frogmouth.persistence import decode_state
from frogmouth.persistence_types import (
    StateError,
    StateError_InvalidData,
    StateError_IoFailure,
    StateError_PermissionDenied,
)


def load_state(path: Path) -> Result[BrowserState, StateError]:
    if not path.exists():
        return Err(error=StateError_IoFailure(path=path, message="state file does not exist"))
    if not path.is_file():
        return Err(error=StateError_IoFailure(path=path, message="state path must refer to a regular file"))

    metadata = path.stat()
    if metadata.st_mode & 0o444 == 0:
        return Err(error=StateError_PermissionDenied(path=path))

    with open(path, "rb") as state_file:
        body = state_file.read()

    source = body.decode("utf-8", errors="surrogateescape")
    for character in source:
        if 0xDC80 <= ord(character) <= 0xDCFF:
            return Err(error=StateError_InvalidData(path=path))
    return decode_state(source, path)
