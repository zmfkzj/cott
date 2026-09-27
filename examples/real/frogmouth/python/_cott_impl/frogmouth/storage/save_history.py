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
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temporary = os.path.join(directory, f".history.{uuid.uuid4().hex}.tmp")
    stream = open(temporary, "xb")
    try:
        with stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        _remove_quietly(temporary)
        raise


def _replace_file(path: str, data: bytes) -> None:
    try:
        _cott_fixture_replace(path, data)
        return
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            raise
    _host_replace(path, data)


def save_history(data_directory: str, locations: CottList[Location]) -> Result[StoredFile, StoreError]:
    path = data_directory + "/history.json"
    data = json.dumps([location.target for location in locations], indent=4).encode("utf-8")
    try:
        _replace_file(path, data)
    except CottContractViolation as violation:
        return Err(error=StoreError_WriteFailed(path=path, message=str(violation.__cause__ or violation.message)))
    except (OSError, ValueError) as error:
        return Err(error=StoreError_WriteFailed(path=path, message=str(error)))
    return Ok(value=StoredFile(path=path, bytes_written=len(data)))
