from json import dumps

from cott_runtime import CottList
from real.yt_dlp_types import JsonMode, JsonMode_Lines, JsonMode_Single, MediaItem


def _render_item(item: MediaItem) -> str:
    return dumps(
        {
            "url": item.url,
            "id": item.id,
            "title": item.title,
            "ext": item.ext,
            "playlist_index": item.playlist_index,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    match mode:
        case JsonMode_Lines():
            return "\n".join(_render_item(item) for item in items)
        case JsonMode_Single():
            return "[" + ",".join(_render_item(item) for item in items) + "]"
