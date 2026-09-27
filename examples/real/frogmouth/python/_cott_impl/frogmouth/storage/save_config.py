import json
import os
import tempfile
from typing import Final

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_replace

from frogmouth.config_types import Config, Dock_Left, Theme_Light
from frogmouth.storage_types import StoreError, StoreError_WriteFailed, StoredFile

_FILE_SUFFIX: Final[str] = "/configuration.json"
_INACTIVE_FIXTURES: Final[str] = "fixture adapters are inactive"


def _encode(config: Config) -> bytes:
    extensions: list[str] = [str(extension) for extension in config.markdown_extensions]
    document: dict[str, bool | list[str]] = {
        "light_mode": isinstance(config.theme, Theme_Light),
        "markdown_extensions": extensions,
        "navigation_left": isinstance(config.navigation_dock, Dock_Left),
    }
    return json.dumps(document, indent=4).encode("utf-8")


def _fixture_replace(path: str, data: bytes) -> bool:
    """Replace path inside the active fs fixture; False when fixture adapters are inactive."""
    try:
        _cott_fixture_replace(path, data)
    except CottContractViolation as violation:
        if violation.message == _INACTIVE_FIXTURES:
            return False
        raise
    return True


def _host_replace(path: str, data: bytes) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(".tmp", ".configuration.", directory)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException as failure:
        try:
            os.unlink(temporary)
        except OSError:
            raise failure
        raise


def save_config(config_directory: str, config: Config) -> Result[StoredFile, StoreError]:
    path = config_directory + _FILE_SUFFIX
    data = _encode(config)
    try:
        if not _fixture_replace(path, data):
            _host_replace(path, data)
    except CottContractViolation as violation:
        cause = violation.__cause__
        message = violation.message if cause is None else str(cause)
        return Err(error=StoreError_WriteFailed(path=path, message=message))
    except (OSError, ValueError) as error:
        return Err(error=StoreError_WriteFailed(path=path, message=str(error)))
    return Ok(value=StoredFile(path=path, bytes_written=len(data)))
