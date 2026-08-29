from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidRange, MediaItem, PlaylistRange


def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]:
    """Expand one-based inclusive playlist ranges deterministically."""
    if len(ranges) == 0:
        return Ok(value=CottList(values=tuple(items)))

    selected: list[MediaItem] = []
    item_count = len(items)
    for playlist_range in ranges:
        if playlist_range.first == 0 or playlist_range.last == 0:
            return Err(error=MediaError_InvalidRange())
        if playlist_range.first > playlist_range.last:
            return Err(error=MediaError_InvalidRange())
        if playlist_range.first > item_count or playlist_range.last > item_count:
            return Err(error=MediaError_InvalidRange())

        for index in range(playlist_range.first - 1, playlist_range.last):
            selected.append(items[index])

    return Ok(value=CottList(values=tuple(selected)))
