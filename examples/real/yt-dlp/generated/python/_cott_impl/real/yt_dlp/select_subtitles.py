from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_SubtitleUnavailable, MediaItem, SubtitleMode_All, SubtitleMode_Automatic, SubtitleMode_Manual, SubtitleMode_None, SubtitleRequest

_MAX_SUBTITLES: Final[int] = 100000


def select_subtitles(item: MediaItem, request: SubtitleRequest) -> Result[CottList[str], MediaError]:
    match request.mode:
        case SubtitleMode_None():
            empty: list[str] = []
            return Ok(value=CottList(values=empty))
        case SubtitleMode_Manual() | SubtitleMode_Automatic() | SubtitleMode_All():
            selected: list[str] = []
            for language in request.languages:
                if len(selected) >= _MAX_SUBTITLES:
                    return Err(error=MediaError_SubtitleUnavailable(language=language))
                selected.append(language)
            return Ok(value=CottList(values=selected))
