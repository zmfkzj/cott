from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput, MediaItem, VideoFilterRequest

_UNSUPPORTED: Final[str] = "unsupported video filter: media items carry no date, view, age or live metadata"


def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    if len(request.date_after) > 0 or len(request.date_before) > 0 or len(request.match_filter) > 0 or request.min_views > 0 or request.max_views > 0 or request.age_limit > 0 or request.reject_live:
        return Err(error=MediaError_InvalidInput(message=_UNSUPPORTED))
    return Ok(value=items)
