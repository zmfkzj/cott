import json
import os
import uuid

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, _cott_fixture_replace
from frogmouth.model_types import Location
from frogmouth.storage_types import StoreError, StoreError_WriteFailed, StoredFile


def _remove_quietly(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        return


def _host_replace(path: str, data: bytes) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    temporary = os.path.join(directory, ".history." + uuid.uuid4().hex + ".tmp")
    handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        _remove_quietly(temporary)
        raise


def save_history(data_directory: str, locations: CottList[Location]) -> Result[StoredFile, StoreError]:
    path = data_directory + "/history.json"
    try:
        text = json.dumps([location.target for location in locations], indent=4)
        data = text.encode("utf-8")
    except (TypeError, ValueError) as error:
        return Err(error=StoreError_WriteFailed(path=path, message=str(error)))
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
