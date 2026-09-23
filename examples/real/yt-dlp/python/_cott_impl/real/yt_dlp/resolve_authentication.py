import cott_runtime
from cott_runtime import Result
from real.yt_dlp_types import Authentication, MediaError


def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]:
    return cott_runtime.Ok(value=request)
