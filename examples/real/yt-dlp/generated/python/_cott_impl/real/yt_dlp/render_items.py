import json

from cott_runtime import CottList
from real.yt_dlp_types import JsonMode, JsonMode_Lines, JsonMode_Single, MediaItem


def _item_dict(item: MediaItem) -> dict[str, str | int]:
    return {"url": item.url, "id": item.id, "title": item.title, "ext": item.ext, "playlist_index": item.playlist_index}


def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    match mode:
        case JsonMode_Lines():
            return "\n".join(json.dumps(_item_dict(item), ensure_ascii=False, separators=(",", ":")) for item in items)
        case JsonMode_Single():
            return json.dumps([_item_dict(item) for item in items], ensure_ascii=False, separators=(",", ":"))
