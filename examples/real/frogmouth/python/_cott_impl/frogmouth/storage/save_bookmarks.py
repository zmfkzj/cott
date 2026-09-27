import json
import os
import tempfile

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, _cott_fixture_replace
from frogmouth.bookmarks_types import Bookmark
from frogmouth.storage_types import StoreError, StoreError_WriteFailed, StoredFile


def _discard(temporary: str) -> None:
    try:
        os.unlink(temporary)
    except OSError:
        return


def _host_replace(directory: str, path: str, data: bytes) -> None:
    os.makedirs(directory, exist_ok=True)
    handle, temporary = tempfile.mkstemp(".tmp", ".bookmarks-", directory)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        _discard(temporary)
        raise


def _store(directory: str, path: str, data: bytes) -> None:
    try:
        _cott_fixture_replace(path, data)
        return
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            raise
    _host_replace(directory, path, data)


def save_bookmarks(data_directory: str, bookmarks: CottList[Bookmark]) -> Result[StoredFile, StoreError]:
    directory = data_directory
    path = directory + "/bookmarks.json"
    document = [[bookmark.title, bookmark.location.target] for bookmark in bookmarks]
    data = json.dumps(document, indent=4).encode("utf-8")
    try:
        _store(directory, path, data)
    except (OSError, ValueError, CottContractViolation) as error:
        return Err(error=StoreError_WriteFailed(path=path, message=str(error)))
    return Ok(value=StoredFile(path=path, bytes_written=len(data)))
