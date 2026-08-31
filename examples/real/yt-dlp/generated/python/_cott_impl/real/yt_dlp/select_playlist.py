from random import shuffle

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp import expand_playlist_ranges
from real.yt_dlp_types import (
    MediaError,
    MediaError_InvalidInput,
    MediaError_InvalidRange,
    MediaItem,
    PlaylistMode_Flat,
    PlaylistMode_Playlist,
    PlaylistMode_Random,
    PlaylistMode_Reverse,
    PlaylistMode_Single,
    PlaylistRequest,
)


def select_playlist(items: CottList[MediaItem], request: PlaylistRequest) -> Result[CottList[MediaItem], MediaError]:
    if request.start > 0 and request.end > 0 and request.start > request.end:
        return Err(error=MediaError_InvalidRange())

    match expand_playlist_ranges(items, request.ranges):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=ranged):
            item_counts: dict[tuple[str, str, str, str, int], int] = {}
            item: MediaItem
            item_key: tuple[str, str, str, str, int]
            for item in items:
                item_key = (item.url, item.id, item.title, item.ext, item.playlist_index)
                item_counts[item_key] = item_counts.get(item_key, 0) + 1

            selected: list[MediaItem] = []
            for item in ranged:
                item_key = (item.url, item.id, item.title, item.ext, item.playlist_index)
                if item_counts.get(item_key, 0) == 0:
                    continue
                item_counts[item_key] -= 1
                if request.start > 0 and item.playlist_index < request.start:
                    continue
                if request.end > 0 and item.playlist_index > request.end:
                    continue
                selected.append(item)

    if request.items != "":
        requested_indices: set[int] = set()
        item_selector: str
        playlist_index: int
        for item_selector in request.items.split(","):
            item_selector = item_selector.strip()
            if item_selector == "" or not item_selector.isdecimal():
                return Err(error=MediaError_InvalidInput(message="playlist items must be comma-separated positive indices"))
            playlist_index = int(item_selector)
            if playlist_index == 0 or playlist_index > 18446744073709551615:
                return Err(error=MediaError_InvalidInput(message="playlist item indices must be between 1 and 18446744073709551615"))
            requested_indices.add(playlist_index)
        selected = [item for item in selected if item.playlist_index in requested_indices]

    mode_reverse: bool
    mode_random: bool
    match request.mode:
        case PlaylistMode_Single():
            selected = selected[:1]
            mode_reverse = False
            mode_random = False
        case PlaylistMode_Playlist() | PlaylistMode_Flat():
            mode_reverse = False
            mode_random = False
        case PlaylistMode_Reverse():
            mode_reverse = True
            mode_random = False
        case PlaylistMode_Random():
            mode_reverse = False
            mode_random = True

    if request.reverse or mode_reverse:
        selected.reverse()
    if request.random or mode_random:
        shuffle(selected)

    return Ok(value=CottList(values=tuple(selected)))
