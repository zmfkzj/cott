from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    MediaError,
    MediaError_SubtitleUnavailable,
    MediaItem,
    SubtitleMode_All,
    SubtitleMode_Automatic,
    SubtitleMode_Manual,
    SubtitleMode_None,
    SubtitleRequest,
)


def select_subtitles(item: MediaItem, request: SubtitleRequest) -> Result[CottList[str], MediaError]:
    match request.mode:
        case SubtitleMode_None():
            subtitles: CottList[str] = CottList(values=())
            return Ok(value=subtitles)
        case SubtitleMode_Manual() | SubtitleMode_Automatic() | SubtitleMode_All():
            if len(request.languages) > 100000:
                return Err(error=MediaError_SubtitleUnavailable(language=request.languages[100000]))

            language: str
            for language in request.languages:
                if language == "":
                    return Err(error=MediaError_SubtitleUnavailable(language=language))

            return Ok(value=request.languages)
