from pathlib import Path

from cott_runtime import Err, Ok, Result, UNIT, Unit
from frogmouth.model_types import BrowserState
from frogmouth.persistence import encode_state
from frogmouth.persistence_types import StateError, StateError_IoFailure, StateError_PermissionDenied


def save_state(path: Path, current: BrowserState) -> Result[Unit, StateError]:
    if "\x00" in str(path):
        return Err(error=StateError_IoFailure(path=path, message="state path must not contain a null character"))

    parent = path.parent
    destination_exists = path.exists()

    if destination_exists:
        if not path.is_file():
            return Err(error=StateError_IoFailure(path=path, message="state path must refer to a regular file"))
        if path.stat().st_mode & 0o222 == 0:
            return Err(error=StateError_PermissionDenied(path=path))
    elif path.is_symlink():
        return Err(error=StateError_IoFailure(path=path, message="state path points to a missing file"))

    existing_parent = parent
    while not existing_parent.exists():
        if existing_parent.is_symlink():
            return Err(error=StateError_IoFailure(path=path, message="state parent path points to a missing directory"))
        next_parent = existing_parent.parent
        if next_parent == existing_parent:
            return Err(error=StateError_IoFailure(path=path, message="state parent directory does not exist"))
        existing_parent = next_parent

    if not existing_parent.is_dir():
        return Err(error=StateError_IoFailure(path=path, message="state parent path must refer to a directory"))
    parent_mode = existing_parent.stat().st_mode
    if parent_mode & 0o111 == 0 or (not destination_exists and parent_mode & 0o222 == 0):
        return Err(error=StateError_PermissionDenied(path=path))

    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    elif not parent.is_dir():
        return Err(error=StateError_IoFailure(path=path, message="state parent path must refer to a directory"))

    encoded = encode_state(current)
    with open(path, "w", encoding="utf-8", newline="\n") as state_file:
        written = state_file.write(encoded)
    if written != len(encoded):
        return Err(error=StateError_IoFailure(path=path, message="state file write was incomplete"))
    return Ok(value=UNIT)
