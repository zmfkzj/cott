import json
from typing import cast

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, Some, _cott_fixture_read
from frogmouth.bookmarks_types import Bookmark
from frogmouth.locations import remote_location
from frogmouth.model_types import Location, LocationKind_Local
from frogmouth.storage_types import LoadedBookmarks, StoreError, StoreError_Malformed, StoreError_ReadFailed


def _read_host(path: str) -> bytes | None | StoreError:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError as error:
        return StoreError_ReadFailed(path=path, message=str(error))


def _read_bytes(path: str) -> bytes | None | StoreError:
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as violation:
        cause = violation.__cause__
        if cause is None and violation.message == "fixture adapters are inactive":
            return _read_host(path)
        if isinstance(cause, (FileNotFoundError, NotADirectoryError)):
            return None
        return StoreError_ReadFailed(path=path, message=str(cause) if cause is not None else violation.message)
    except OSError as error:
        return StoreError_ReadFailed(path=path, message=str(error))


def load_bookmarks(data_directory: str) -> Result[LoadedBookmarks, StoreError]:
    path = data_directory + "/bookmarks.json"
    data = _read_bytes(path)
    if data is None:
        return Ok(value=LoadedBookmarks(path=path, bookmarks=CottList(values=[])))
    if not isinstance(data, bytes):
        return Err(error=data)
    try:
        document: object = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        return Err(error=StoreError_Malformed(path=path, message=str(error)))
    if not isinstance(document, list):
        return Err(error=StoreError_Malformed(path=path, message="bookmarks document is not an array"))
    elements = cast("list[object]", document)
    bookmarks: list[Bookmark] = []
    for index, element in enumerate(elements):
        title: object = None
        target: object = None
        if isinstance(element, list):
            parts = cast("list[object]", element)
            if len(parts) == 2:
                title = parts[0]
                target = parts[1]
        if not (isinstance(title, str) and title and isinstance(target, str) and target):
            return Err(error=StoreError_Malformed(path=path, message=f"bookmark {index} is not a [title, location] pair"))
        remote = remote_location(target)
        if isinstance(remote, Some):
            location = remote.value
        else:
            location = Location(kind=LocationKind_Local(), target=target)
        bookmarks.append(Bookmark(title=title, location=location))
    return Ok(value=LoadedBookmarks(path=path, bookmarks=CottList(values=bookmarks)))
