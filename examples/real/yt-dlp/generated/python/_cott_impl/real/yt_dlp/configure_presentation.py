from cott_runtime import Ok, Result, UNIT, Unit
from real.yt_dlp_types import MediaError, PresentationRequest


def configure_presentation(request: PresentationRequest) -> Result[Unit, MediaError]:
    return Ok(value=UNIT)
