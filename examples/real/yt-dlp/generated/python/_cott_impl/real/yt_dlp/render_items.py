import json

from cott_runtime import CottList
from real.yt_dlp_types import JsonMode, JsonMode_Lines, JsonMode_Single, MediaItem



def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    objects = (
        {
            "url": item.url,
            "id": item.id,
            "title": item.title,
            "ext": item.ext,
            "playlist_index": item.playlist_index,
        }
        for item in items
    )
    match mode:
        case JsonMode_Lines():
            return "\n".join(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) for obj in objects)
        case JsonMode_Single():
            return json.dumps(list(objects), ensure_ascii=False, separators=(",", ":"))
