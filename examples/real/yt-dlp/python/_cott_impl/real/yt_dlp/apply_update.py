from pathlib import Path
from urllib.request import Request, urlopen

from cott_runtime import Err, Ok, Result, UNIT, Unit, _cott_fixture_write
from real.yt_dlp_types import (
    MediaError,
    MediaError_NetworkFailure,
    MediaError_OutputFailure,
    MediaError_UpdateUnavailable,
    UpdatePolicy_Apply,
    UpdatePolicy_Check,
    UpdatePolicy_Master,
    UpdatePolicy_Never,
    UpdatePolicy_Nightly,
    UpdateRequest,
)


def apply_update(request: UpdateRequest) -> Result[Unit, MediaError]:
    match request.policy:
        case UpdatePolicy_Never():
            return Ok(value=UNIT)
        case UpdatePolicy_Check():
            if request.channel == "" or not (request.channel.startswith("http://") or request.channel.startswith("https://")):
                return Err(error=MediaError_UpdateUnavailable(message="update channel must be an HTTP or HTTPS URL"))

            check_request: Request = Request(url=request.channel, method="HEAD")
            with urlopen(check_request) as check_response:
                check_status: int = check_response.status

            if check_status <= 0:
                return Err(error=MediaError_NetworkFailure(message="update check did not return a valid HTTP status"))
            if check_status < 200 or check_status >= 400:
                return Err(error=MediaError_UpdateUnavailable(message=f"update channel returned HTTP status {check_status}"))
            return Ok(value=UNIT)
        case UpdatePolicy_Apply() | UpdatePolicy_Nightly() | UpdatePolicy_Master():
            if request.channel == "" or not (request.channel.startswith("http://") or request.channel.startswith("https://")):
                return Err(error=MediaError_UpdateUnavailable(message="update channel must be an HTTP or HTTPS URL"))
            if request.target == Path() or "\x00" in str(request.target):
                return Err(error=MediaError_OutputFailure(message="update target must name a file"))

            download_request: Request = Request(url=request.channel, method="GET")
            with urlopen(download_request) as download_response:
                download_status: int = download_response.status
                if download_status <= 0:
                    return Err(error=MediaError_NetworkFailure(message="update download did not return a valid HTTP status"))
                if download_status < 200 or download_status >= 400:
                    return Err(error=MediaError_UpdateUnavailable(message=f"update channel returned HTTP status {download_status}"))
                update_content: bytes = download_response.read()
            if update_content == b"":
                return Err(error=MediaError_UpdateUnavailable(message="update channel returned an empty update"))

            _cott_fixture_write(request.target, update_content)
            return Ok(value=UNIT)
