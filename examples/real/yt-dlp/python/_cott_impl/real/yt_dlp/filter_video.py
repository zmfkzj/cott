import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput, MediaItem, VideoFilterRequest


def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    if (
        request.date_after != ""
        or request.date_before != ""
        or request.match_filter != ""
        or request.min_views != 0
        or request.max_views != 0
        or request.age_limit != 0
        or request.reject_live
    ):
        return cott_runtime.Err(error=MediaError_InvalidInput(message="unsupported video filter: media items carry no date, view, age or live metadata"))
    return cott_runtime.Ok(value=items)
