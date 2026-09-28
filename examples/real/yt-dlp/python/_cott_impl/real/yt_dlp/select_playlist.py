import random
from typing import Final

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, U64
from real.yt_dlp import expand_playlist_ranges
from real.yt_dlp_types import MediaError, MediaError_InvalidInput, MediaError_InvalidRange, MediaItem, PlaylistMode_Flat, PlaylistMode_Playlist, PlaylistMode_Random, PlaylistMode_Reverse, PlaylistMode_Single, PlaylistRequest

_MAX_INDEX: Final[int] = 18446744073709551615
_BAD_ITEMS: Final[str] = "invalid playlist items selector: expected comma-separated positive integer indices"


def _key(item: MediaItem) -> tuple[str, str, str, str, U64]:
    return (item.url, item.id, item.title, item.ext, item.playlist_index)


def _parse_items(spec: str) -> set[U64] | None:
    wanted: set[U64] = set()
    for raw in spec.split(","):
        token: str = raw.strip()
        if token == "" or not token.isdecimal():
            return None
        value: U64 = 0
        for digit in token:
            value = value * 10 + int(digit)
            if value > _MAX_INDEX:
                return None
        if value == 0:
            return None
        wanted.add(value)
    return wanted


def _bounded(items: CottList[MediaItem], candidates: CottList[MediaItem], start: U64, end: U64) -> list[MediaItem]:
    allowance: dict[tuple[str, str, str, str, U64], U64] = {}
    for original in items:
        key: tuple[str, str, str, str, U64] = _key(original)
        allowance[key] = allowance.get(key, 0) + 1
    selected: list[MediaItem] = []
    for candidate in candidates:
        candidate_key: tuple[str, str, str, str, U64] = _key(candidate)
        remaining: U64 = allowance.get(candidate_key, 0)
        if remaining == 0:
            continue
        allowance[candidate_key] = remaining - 1
        index: U64 = candidate.playlist_index
        if start > 0 and index < start:
            continue
        if end > 0 and index > end:
            continue
        selected.append(candidate)
    return selected


def select_playlist(items: CottList[MediaItem], request: PlaylistRequest) -> Result[CottList[MediaItem], MediaError]:
    start: U64 = request.start
    end: U64 = request.end
    if start > 0 and end > 0 and start > end:
        return Err(error=MediaError_InvalidRange())
    match expand_playlist_ranges(items, request.ranges):
        case Err(error=expand_error):
            return Err(error=expand_error)
        case Ok(value=candidates):
            selected: list[MediaItem] = _bounded(items, candidates, start, end)
    if request.items != "":
        wanted: set[U64] | None = _parse_items(request.items)
        if wanted is None:
            return Err(error=MediaError_InvalidInput(message=_BAD_ITEMS))
        selected = [entry for entry in selected if entry.playlist_index in wanted]
    do_reverse: bool
    do_random: bool
    match request.mode:
        case PlaylistMode_Single():
            del selected[1:]
            do_reverse = request.reverse
            do_random = request.random
        case PlaylistMode_Playlist() | PlaylistMode_Flat():
            do_reverse = request.reverse
            do_random = request.random
        case PlaylistMode_Reverse():
            do_reverse = True
            do_random = request.random
        case PlaylistMode_Random():
            do_reverse = request.reverse
            do_random = True
    if do_reverse:
        selected.reverse()
    if do_random:
        values: list[MediaItem] = list(selected)
        try:
            cott_runtime._cott_fixture_shuffle(values)
        except CottContractViolation as violation:
            if violation.message != "fixture adapters are inactive":
                raise
            random.shuffle(values)
        selected = values
    return Ok(value=CottList(values=selected))
