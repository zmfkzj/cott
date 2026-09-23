from typing import Final

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidShortcut, ShortcutKind_Search, ShortcutKind_SearchAll, ShortcutRequest

_URL_SCHEMES: Final[str] = "http https ftp ftps rtmp rtmpe rtmps rtmpt rtmpte rtmpts rtmfp ws wss"


def _is_valid_url(url: str) -> bool:
    for ch in url:
        code: int = ord(ch)
        if ch.isspace() or code < 0x20 or 0x7F <= code <= 0x9F:
            return False
    rest: str
    if url.startswith("//"):
        rest = url[2:]
    else:
        scheme, sep, remainder = url.partition("://")
        if not sep or scheme not in _URL_SCHEMES.split(" "):
            return False
        rest = remainder
    end: int = len(rest)
    for delim in "/?#":
        idx: int = rest.find(delim)
        if idx != -1 and idx < end:
            end = idx
    return end > 0


def build_shortcut_url(request: ShortcutRequest) -> Result[str, MediaError]:
    query: str = request.query
    if len(query) == 0:
        return Err(error=MediaError_InvalidShortcut(value=query))
    kind = request.kind
    if isinstance(kind, ShortcutKind_Search):
        if request.limit == 0:
            return Err(error=MediaError_InvalidShortcut(value=query))
        return Ok(value=f"ytsearch{request.limit:d}:{query}")
    if isinstance(kind, ShortcutKind_SearchAll):
        return Ok(value=f"ytsearchall:{query}")
    stripped: str = query.strip()
    if not _is_valid_url(stripped):
        return Err(error=MediaError_InvalidShortcut(value=query))
    return Ok(value=stripped)
