import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import MediaError, MediaError_SubtitleUnavailable, MediaItem, SubtitleMode_All, SubtitleMode_Automatic, SubtitleMode_Manual, SubtitleMode_None, SubtitleRequest


def select_subtitles(item: MediaItem, request: SubtitleRequest) -> Result[CottList[str], MediaError]:
    match request.mode:
        case SubtitleMode_None():
            empty: list[str] = []
            return cott_runtime.Ok(value=CottList(values=empty))
        case SubtitleMode_Manual() | SubtitleMode_Automatic() | SubtitleMode_All():
            if len(request.languages) == 0:
                return cott_runtime.Err(error=MediaError_SubtitleUnavailable(language=""))
            selected: list[str] = []
            for language in request.languages:
                if language == "":
                    return cott_runtime.Err(error=MediaError_SubtitleUnavailable(language=""))
                selected.append(language)
            return cott_runtime.Ok(value=CottList(values=selected))
