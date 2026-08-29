import os
from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import CollectionEntry, PostingError, PostingError_CollectionRootMissing, PostingError_ReadFailed


def discover_collections(root: Path) -> Result[CottList[CollectionEntry], PostingError]:
    if not os.path.isdir(root):
        return Err(error=PostingError_CollectionRootMissing(path=root))

    read_errors: list[OSError] = []
    paths: list[Path] = []
    for directory, _, filenames in os.walk(root, onerror=read_errors.append):
        for filename in filenames:
            if filename.endswith(".posting.yaml"):
                paths.append(Path(directory) / filename)
                if len(paths) > 100000:
                    return Err(error=PostingError_ReadFailed(path=root, message="collection count exceeds 100000"))

    if read_errors:
        failure = read_errors[0]
        failed_path = root if failure.filename is None else Path(os.fsdecode(failure.filename))
        return Err(error=PostingError_ReadFailed(path=failed_path, message=str(failure)))

    paths.sort()
    entries = [CollectionEntry(path=path, name=path.name.removesuffix(".posting.yaml")) for path in paths]
    return Ok(value=CottList(values=entries))
