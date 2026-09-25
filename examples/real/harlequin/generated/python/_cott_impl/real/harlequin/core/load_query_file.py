from pathlib import Path
from typing import Any, cast

import boto3
import cott_runtime
from botocore.exceptions import BotoCoreError, ClientError
from cott_runtime import CottContractViolation, Result

from real.harlequin.core_types import FileError, FileError_InvalidEncoding, FileError_NotFound, FileError_PermissionDenied, FileError_TransferFailed, FileLocation_Local, FileReference, LoadedFile


def _decode(reference: FileReference, data: bytes) -> Result[LoadedFile, FileError]:
    try:
        source: str = data.decode("utf-8")
    except UnicodeDecodeError:
        return cott_runtime.Err(error=FileError_InvalidEncoding(reference=reference))
    return cott_runtime.Ok(value=LoadedFile(reference=reference, source=source))


def _os_error(reference: FileReference, error: BaseException | None) -> Result[LoadedFile, FileError]:
    if isinstance(error, FileNotFoundError):
        return cott_runtime.Err(error=FileError_NotFound(reference=reference))
    if isinstance(error, PermissionError):
        return cott_runtime.Err(error=FileError_PermissionDenied(reference=reference))
    return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="local file read failed"))


def _read_host(reference: FileReference, path: Path) -> Result[LoadedFile, FileError]:
    try:
        data: bytes = path.read_bytes()
    except OSError as exc:
        return _os_error(reference, exc)
    return _decode(reference, data)


def load_query_file(reference: FileReference) -> Result[LoadedFile, FileError]:
    location = reference.location
    if isinstance(location, FileLocation_Local):
        path = Path(location.path)
        try:
            data: bytes = cott_runtime._cott_fixture_read(path)
        except CottContractViolation as exc:
            if exc.message == "fixture adapters are inactive":
                return _read_host(reference, path)
            return _os_error(reference, exc.__cause__)
        except OSError as exc:
            return _os_error(reference, exc)
        except Exception:
            return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="local file read failed"))
        return _decode(reference, data)
    try:
        sdk: Any = boto3
        client: Any = sdk.client("s3")
        response: object = cast(object, client.get_object(Bucket=location.bucket, Key=location.key))
        if not isinstance(response, dict):
            return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="S3 response was not a mapping"))
        body: object = cast(dict[str, object], response).get("Body")
        if body is None:
            return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="S3 response missing body"))
        stream: Any = body
        raw: object = cast(object, stream.read())
    except ClientError as exc:
        error_info = cast(object, exc.response.get("Error", {}))
        code: str = str(cast(dict[str, object], error_info).get("Code", "")) if isinstance(error_info, dict) else ""
        if code in ("NoSuchKey", "NoSuchBucket", "404", "NotFound"):
            return cott_runtime.Err(error=FileError_NotFound(reference=reference))
        if code in ("AccessDenied", "403", "Forbidden"):
            return cott_runtime.Err(error=FileError_PermissionDenied(reference=reference))
        return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="S3 request failed"))
    except (BotoCoreError, OSError):
        return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="S3 transfer failed"))
    except Exception:
        return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="S3 transfer failed"))
    if not isinstance(raw, (bytes, bytearray)):
        return cott_runtime.Err(error=FileError_TransferFailed(reference=reference, message="S3 body was not bytes"))
    return _decode(reference, bytes(raw))
