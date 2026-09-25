import os
import tempfile
from typing import Any, Final, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_replace
from real.harlequin.core_types import FileError, FileError_PermissionDenied, FileError_TransferFailed, FileLocation_Local, FileReference, SavedFile

_INACTIVE: Final[str] = "fixture adapters are inactive"
_LOCAL_FAILED: Final[str] = "local file write failed"
_S3_FAILED: Final[str] = "S3 upload failed"


def _is_denied_code(code: str) -> bool:
    return code in ("AccessDenied", "403", "Forbidden", "AllAccessDisabled", "InvalidAccessKeyId", "SignatureDoesNotMatch")


def _discard(temp_path: str) -> bool:
    try:
        os.unlink(temp_path)
    except OSError:
        return False
    return True


def _host_replace(path: str, data: bytes) -> None:
    folder = os.path.split(os.path.abspath(path))[0]
    fd, temp_path = tempfile.mkstemp("", ".cott-save-", folder)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except BaseException:
        _discard(temp_path)
        raise


def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]:
    if not reference.writable:
        return Err(error=FileError_PermissionDenied(reference=reference))
    data = source.encode("utf-8")
    location = reference.location
    if isinstance(location, FileLocation_Local):
        path = os.fspath(location.path)
        try:
            _cott_fixture_replace(path, data)
        except CottContractViolation as exc:
            if exc.message != _INACTIVE:
                if isinstance(exc.__cause__, PermissionError):
                    return Err(error=FileError_PermissionDenied(reference=reference))
                return Err(error=FileError_TransferFailed(reference=reference, message=_LOCAL_FAILED))
            try:
                _host_replace(path, data)
            except PermissionError:
                return Err(error=FileError_PermissionDenied(reference=reference))
            except OSError:
                return Err(error=FileError_TransferFailed(reference=reference, message=_LOCAL_FAILED))
        except PermissionError:
            return Err(error=FileError_PermissionDenied(reference=reference))
        except Exception:
            return Err(error=FileError_TransferFailed(reference=reference, message=_LOCAL_FAILED))
        return Ok(value=SavedFile(reference=reference, bytes_written=len(data)))
    try:
        sdk: Any = boto3
        client: Any = sdk.client("s3")
        client.put_object(Bucket=location.bucket, Key=location.key, Body=data)
    except ClientError as exc:
        error_info = cast(object, cast(Any, exc).response.get("Error", {}))
        code = ""
        if isinstance(error_info, dict):
            raw_code = cast(dict[str, object], error_info).get("Code")
            if isinstance(raw_code, str):
                code = raw_code
        if _is_denied_code(code):
            return Err(error=FileError_PermissionDenied(reference=reference))
        return Err(error=FileError_TransferFailed(reference=reference, message=_S3_FAILED))
    except (BotoCoreError, OSError):
        return Err(error=FileError_TransferFailed(reference=reference, message=_S3_FAILED))
    return Ok(value=SavedFile(reference=reference, bytes_written=len(data)))
