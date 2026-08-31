from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    LiveMode_Default,
    LiveMode_FromStart,
    LiveMode_Wait,
    LiveRequest,
    MediaError,
    MediaError_InvalidInput,
    MediaError_RetryExhausted,
    MediaItem,
)


def resolve_live_media(items: CottList[MediaItem], request: LiveRequest) -> Result[CottList[MediaItem], MediaError]:
    if request.concurrent_fragments == 0:
        return Err(error=MediaError_InvalidInput(message="concurrent fragments must be greater than zero"))

    match request.mode:
        case LiveMode_Default() | LiveMode_FromStart():
            return Ok(value=items)
        case LiveMode_Wait():
            if request.wait_for_video_ms == 0:
                return Err(error=MediaError_InvalidInput(message="wait for video must be greater than zero"))
            if len(items) == 0:
                return Err(error=MediaError_RetryExhausted(attempts=1))
            return Ok(value=items)
