import datetime
import hashlib
import hmac
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Final

from cott_runtime import Err, Ok, Result
from real.harlequin.core_types import FileError, FileError_PermissionDenied, FileError_TransferFailed, FileLocation_Local, FileReference, SavedFile

_DEFAULT_REGION: Final[str] = "us-east-1"


def _hmac_sha256(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _s3_request(bucket: str, key: str, data: bytes) -> urllib.request.Request:
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or _DEFAULT_REGION
    host = bucket + ".s3." + region + ".amazonaws.com"
    canonical_uri = "/" + urllib.parse.quote(key, safe="/~")
    url = "https://" + host + canonical_uri
    payload_hash = hashlib.sha256(data).hexdigest()
    headers: dict[str, str] = {"Content-Type": "text/plain; charset=utf-8", "x-amz-content-sha256": payload_hash}
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if access_key and secret_key:
        now = datetime.datetime.now(datetime.UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        signed: dict[str, str] = {"host": host, "x-amz-content-sha256": payload_hash, "x-amz-date": amz_date}
        token = os.environ.get("AWS_SESSION_TOKEN")
        if token:
            signed["x-amz-security-token"] = token
        names = sorted(signed)
        canonical_headers = "".join(name + ":" + signed[name].strip() + "\n" for name in names)
        signed_headers = ";".join(names)
        canonical_request = "\n".join(["PUT", canonical_uri, "", canonical_headers, signed_headers, payload_hash])
        scope = date_stamp + "/" + region + "/s3/aws4_request"
        string_to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
        signing_key = _hmac_sha256(_hmac_sha256(_hmac_sha256(_hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date_stamp), region), "s3"), "aws4_request")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        headers["x-amz-date"] = amz_date
        if token:
            headers["x-amz-security-token"] = token
        headers["Authorization"] = "AWS4-HMAC-SHA256 Credential=" + access_key + "/" + scope + ", SignedHeaders=" + signed_headers + ", Signature=" + signature
    return urllib.request.Request(url, data=data, method="PUT", headers=headers)


def save_query_file(reference: FileReference, source: str) -> Result[SavedFile, FileError]:
    if not reference.writable:
        return Err(error=FileError_PermissionDenied(reference=reference))
    data = source.encode("utf-8")
    location = reference.location
    if isinstance(location, FileLocation_Local):
        try:
            with open(location.path, "wb") as handle:
                handle.write(data)
        except PermissionError:
            return Err(error=FileError_PermissionDenied(reference=reference))
        except OSError:
            return Err(error=FileError_TransferFailed(reference=reference, message="local file write failed"))
        return Ok(value=SavedFile(reference=reference, bytes_written=len(data)))
    try:
        with urllib.request.urlopen(_s3_request(location.bucket, location.key, data), timeout=30) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return Err(error=FileError_PermissionDenied(reference=reference))
        return Err(error=FileError_TransferFailed(reference=reference, message="S3 upload failed with HTTP " + str(exc.code)))
    except urllib.error.URLError:
        return Err(error=FileError_TransferFailed(reference=reference, message="S3 upload failed: connection error"))
    except OSError:
        return Err(error=FileError_TransferFailed(reference=reference, message="S3 upload failed: I/O error"))
    return Ok(value=SavedFile(reference=reference, bytes_written=len(data)))
