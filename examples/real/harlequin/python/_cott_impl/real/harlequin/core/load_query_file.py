from pathlib import Path
from typing import Any, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from cott_runtime import Err, Ok, Result

from real.harlequin.core_types import FileError, FileError_InvalidEncoding, FileError_NotFound, FileError_PermissionDenied, FileError_TransferFailed, FileLocation_Local, FileReference, LoadedFile


def _decode(reference: FileReference, data: bytes) -> Result[LoadedFile, FileError]:
    try:
        source: str = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=FileError_InvalidEncoding(reference=reference))
    return Ok(value=LoadedFile(reference=reference, source=source))


def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]:
    location = reference.location
    if isinstance(location, FileLocation_Local):
        try:
            data: bytes = Path(location.path).read_bytes()
        except FileNotFoundError:
            return Err(error=FileError_NotFound(reference=reference))
        except PermissionError:
            return Err(error=FileError_PermissionDenied(reference=reference))
        except IsADirectoryError:
            return Err(error=FileError_TransferFailed(reference=reference, message="path is a directory"))
        except OSError:
            return Err(error=FileError_TransferFailed(reference=reference, message="local file read failed"))
        return _decode(reference, data)
    try:
        sdk: Any = boto3
        client: Any = sdk.client("s3")
        response: object = cast(object, client.get_object(Bucket=location.bucket, Key=location.key))
        if not isinstance(response, dict):
            return Err(error=FileError_TransferFailed(reference=reference, message="S3 response was not a mapping"))
        body: object = cast(dict[str, object], response).get("Body")
        if body is None:
            return Err(error=FileError_TransferFailed(reference=reference, message="S3 response missing body"))
        stream: Any = body
        raw: object = cast(object, stream.read())
    except ClientError as exc:
        error_info = cast(object, exc.response.get("Error", {}))
        code: str = str(cast(dict[str, object], error_info).get("Code", "")) if isinstance(error_info, dict) else ""
        if code in ("NoSuchKey", "NoSuchBucket", "404", "NotFound"):
            return Err(error=FileError_NotFound(reference=reference))
        if code in ("AccessDenied", "403", "Forbidden"):
            return Err(error=FileError_PermissionDenied(reference=reference))
        return Err(error=FileError_TransferFailed(reference=reference, message=f"S3 error: {code or 'unknown'}"))
    except BotoCoreError:
        return Err(error=FileError_TransferFailed(reference=reference, message="S3 transfer failed"))
    if not isinstance(raw, (bytes, bytearray)):
        return Err(error=FileError_TransferFailed(reference=reference, message="S3 body was not bytes"))
    payload: bytes = bytes(cast(bytes, raw))
    return _decode(reference, payload)
