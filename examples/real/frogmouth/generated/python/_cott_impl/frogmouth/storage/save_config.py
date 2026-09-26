import json
import os
import tempfile

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_replace

from frogmouth.config_types import Config, Dock_Left, Theme_Light
from frogmouth.storage_types import StoreError, StoreError_WriteFailed, StoredFile


def _remove_temporary(temporary: str) -> None:
    if os.path.lexists(temporary):
        os.unlink(temporary)


def _host_replace(path: str, data: bytes) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(".tmp", ".configuration.", directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException as failure:
        try:
            _remove_temporary(temporary)
        except OSError:
            raise failure
        raise


def save_config(config_directory: str, config: Config) -> Result[StoredFile, StoreError]:
    stripped = config_directory.rstrip("/")
    path = (stripped if stripped or not config_directory else "") + "/configuration.json"
    extensions: list[str] = [str(item) for item in config.markdown_extensions]
    document: dict[str, bool | list[str]] = {
        "light_mode": isinstance(config.theme, Theme_Light),
        "markdown_extensions": extensions,
        "navigation_left": isinstance(config.navigation_dock, Dock_Left),
    }
    data = json.dumps(document, indent=4).encode("utf-8")
    try:
        _cott_fixture_replace(path, data)
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            return Err(error=StoreError_WriteFailed(path=path, message=str(violation.__cause__ or violation.message)))
        try:
            _host_replace(path, data)
        except OSError as error:
            return Err(error=StoreError_WriteFailed(path=path, message=str(error)))
    except OSError as error:
        return Err(error=StoreError_WriteFailed(path=path, message=str(error)))
    return Ok(value=StoredFile(path=path, bytes_written=len(data)))
