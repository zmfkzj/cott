import json
from typing import cast

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, Some, _cott_fixture_read
from frogmouth.history import start_history
from frogmouth.history_types import History
from frogmouth.locations import remote_location
from frogmouth.model_types import Location, LocationKind_Local
from frogmouth.storage_types import StoreError, StoreError_Malformed, StoreError_ReadFailed


def _read_bytes(path: str) -> bytes:
    """Read path from the active fs fixture, or from the host file system when no fixture is active.

    Fixture file-system errors surface as a CottContractViolation carrying the OSError as its cause;
    injected fixture failures and host failures are raised unwrapped.
    """
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            raise
    with open(path, "rb") as handle:
        return handle.read()


def _unreadable(path: str, failure: BaseException) -> Result[History, StoreError]:
    """Result for a history file that could not be read: a missing file is an empty history, anything else ReadFailed."""
    if isinstance(failure, (FileNotFoundError, NotADirectoryError)):
        return Ok(value=start_history(CottList(values=[])))
    return Err(error=StoreError_ReadFailed(path=path, message=str(failure)))


def _parse_history(path: str, data: bytes) -> Result[History, StoreError]:
    """Decode the strict UTF-8 JSON array of non-empty location strings read from path."""
    try:
        document: object = json.loads(data.decode("utf-8"))
    except (ValueError, RecursionError) as error:
        return Err(error=StoreError_Malformed(path=path, message=str(error)))
    if not isinstance(document, list):
        return Err(error=StoreError_Malformed(path=path, message="history is not a JSON array"))
    locations: list[Location] = []
    for entry in cast(list[object], document):
        if not isinstance(entry, str) or not entry:
            return Err(error=StoreError_Malformed(path=path, message="history entry is not a non-empty string"))
        remote = remote_location(entry)
        if isinstance(remote, Some):
            locations.append(remote.value)
        else:
            locations.append(Location(kind=LocationKind_Local(), target=entry))
    return Ok(value=start_history(CottList(values=locations)))


def load_history(data_directory: str) -> Result[History, StoreError]:
    path = data_directory + "/history.json"
    try:
        data = _read_bytes(path)
    except CottContractViolation as violation:
        return _unreadable(path, violation if violation.__cause__ is None else violation.__cause__)
    except (OSError, ValueError) as error:
        return _unreadable(path, error)
    return _parse_history(path, data)
