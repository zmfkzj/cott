from pathlib import Path

import boto3
from cott_runtime import Err, Ok, Result
from real.harlequin.core_types import (
    FileError,
    FileError_PermissionDenied,
    FileLocation_Local,
    FileLocation_S3,
    FileReference,
    SavedFile,
)


def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]:
    if not reference.writable:
        return Err(error=FileError_PermissionDenied(reference=reference))

    content = source.encode("utf-8")
    match reference.location:
        case FileLocation_Local(path=path):
            Path(path).write_bytes(content)
        case FileLocation_S3(bucket=bucket, key=key):
            boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=content)

    return Ok(value=SavedFile(reference=reference, bytes_written=len(content)))
