import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidRange, MediaItem, PlaylistRange


def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]:
    if len(ranges) == 0:
        return cott_runtime.Ok(value=items)
    for bounds in ranges:
        if bounds.first == 0 or bounds.first > bounds.last:
            return cott_runtime.Err(error=MediaError_InvalidRange())
    selected: list[MediaItem] = []
    for span in ranges:
        for entry in items:
            if span.first <= entry.playlist_index <= span.last:
                selected.append(entry)
    return cott_runtime.Ok(value=CottList(values=selected))
