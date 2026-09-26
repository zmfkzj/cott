import json
from typing import cast

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, Some, _cott_fixture_read
from frogmouth.history import start_history
from frogmouth.history_types import History
from frogmouth.locations import remote_location
from frogmouth.model_types import Location, LocationKind_Local
from frogmouth.storage_types import StoreError, StoreError_Malformed, StoreError_ReadFailed


def _read_bytes(path: str) -> bytes | None:
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message != "fixture adapters are inactive":
            cause = error.__cause__
            if isinstance(cause, (FileNotFoundError, NotADirectoryError)):
                return None
            raise OSError(str(cause) if cause is not None else error.message) from error
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (FileNotFoundError, NotADirectoryError):
        return None


def load_history(data_directory: str) -> Result[History, StoreError]:
    path = data_directory + "/history.json"
    try:
        data = _read_bytes(path)
    except OSError as error:
        return Err(error=StoreError_ReadFailed(path=path, message=str(error)))
    if data is None:
        return Ok(value=start_history(CottList(values=[])))
    try:
        document: object = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        return Err(error=StoreError_Malformed(path=path, message=str(error)))
    if not isinstance(document, list):
        return Err(error=StoreError_Malformed(path=path, message="history is not a JSON array"))
    entries = cast(list[object], document)
    locations: list[Location] = []
    for item in entries:
        if not isinstance(item, str) or not item:
            return Err(error=StoreError_Malformed(path=path, message="history entry is not a non-empty string"))
        remote = remote_location(item)
        if isinstance(remote, Some):
            locations.append(remote.value)
        else:
            locations.append(Location(kind=LocationKind_Local(), target=item))
    return Ok(value=start_history(CottList(values=locations)))
