from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import (
    MediaError,
    MediaError_InvalidShortcut,
    ShortcutKind_Search,
    ShortcutKind_SearchAll,
    ShortcutKind_Url,
    ShortcutRequest,
)


def build_shortcut_url(request: ShortcutRequest) -> Result[str, MediaError]:
    if request.query == "":
        return Err(error=MediaError_InvalidShortcut(value=request.query))

    match request.kind:
        case ShortcutKind_Search():
            if request.limit == 0:
                return Err(error=MediaError_InvalidShortcut(value=request.query))
            return Ok(value=f"ytsearch{request.limit}:{request.query}")
        case ShortcutKind_SearchAll():
            return Ok(value=f"ytsearchall:{request.query}")
        case ShortcutKind_Url():
            return Ok(value=request.query)
