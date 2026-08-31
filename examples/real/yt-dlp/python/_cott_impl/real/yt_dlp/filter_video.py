from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput, MediaItem, VideoFilterRequest


def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    date_value: str
    month: int
    day: int
    maximum_day: int
    for date_value in (request.date_after, request.date_before):
        if date_value == "":
            continue
        if len(date_value) != 8 or not date_value.isascii() or not date_value.isdecimal():
            return Err(error=MediaError_InvalidInput(message="video filter dates must use YYYYMMDD format"))
        month = int(date_value[4:6])
        day = int(date_value[6:8])
        if month == 2:
            maximum_day = 29 if int(date_value[:4]) % 400 == 0 or (int(date_value[:4]) % 4 == 0 and int(date_value[:4]) % 100 != 0) else 28
        elif month == 4 or month == 6 or month == 9 or month == 11:
            maximum_day = 30
        else:
            maximum_day = 31
        if month == 0 or month > 12 or day == 0 or day > maximum_day:
            return Err(error=MediaError_InvalidInput(message="video filter dates must be valid calendar dates"))

    if request.date_after != "" and request.date_before != "" and request.date_after > request.date_before:
        return Err(error=MediaError_InvalidInput(message="date after cannot be later than date before"))
    if request.min_views < 0 or request.max_views < 0 or request.min_views > 18446744073709551615 or request.max_views > 18446744073709551615:
        return Err(error=MediaError_InvalidInput(message="view limits must be unsigned 64-bit values"))
    if request.max_views > 0 and request.min_views > request.max_views:
        return Err(error=MediaError_InvalidInput(message="minimum views cannot exceed maximum views"))
    if request.age_limit < 0 or request.age_limit > 65535:
        return Err(error=MediaError_InvalidInput(message="age limit must be an unsigned 16-bit value"))

    selected: list[MediaItem] = []
    item: MediaItem
    normalized_title: str
    for item in items:
        if request.match_filter != "" and request.match_filter not in item.title:
            continue
        normalized_title = item.title.casefold()
        if request.reject_live and (normalized_title.startswith("live:") or normalized_title.startswith("[live]")):
            continue
        if not request.include_ads and (normalized_title.startswith("ad:") or normalized_title.startswith("[ad]")):
            continue
        selected.append(item)

    return Ok(value=CottList(values=tuple(selected)))
