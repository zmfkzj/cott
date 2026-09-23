from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput, MediaItem, VideoFilterRequest


def _valid_date(value: str) -> bool:
    return value == "" or (len(value) == 8 and value.isascii() and value.isdigit())


def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    if not _valid_date(request.date_after):
        return Err(error=MediaError_InvalidInput(message="invalid date_after"))
    if not _valid_date(request.date_before):
        return Err(error=MediaError_InvalidInput(message="invalid date_before"))
    if request.date_after != "" and request.date_before != "" and request.date_after > request.date_before:
        return Err(error=MediaError_InvalidInput(message="date_after is later than date_before"))
    if request.max_views != 0 and request.min_views > request.max_views:
        return Err(error=MediaError_InvalidInput(message="min_views exceeds max_views"))
    selected: list[MediaItem] = [item for item in items]
    return Ok(value=CottList(values=selected))
