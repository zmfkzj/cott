from pathlib import Path
from typing import Any

import boto3
from cott_runtime import Ok, Result
from real.harlequin.core_types import (
    FileError,
    FileLocation_Local,
    FileLocation_S3,
    FileReference,
    LoadedFile,
)


def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]:
    source: str
    match reference.location:
        case FileLocation_Local(path=path):
            source = Path(path).read_text(encoding="utf-8")
        case FileLocation_S3(bucket=bucket, key=key):
            sdk: Any = boto3
            client: Any = sdk.client("s3")
            response = client.get_object(Bucket=bucket, Key=key)
            source = response["Body"].read().decode("utf-8")

    return Ok(value=LoadedFile(reference=reference, source=source))
