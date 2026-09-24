import json
from typing import assert_never

from cott_runtime import CottList
from real.yt_dlp_types import JsonMode, JsonMode_Lines, JsonMode_Single, MediaItem


def _item_dict(item: MediaItem) -> dict[str, str | int]:
    return {"url": item.url, "id": item.id, "title": item.title, "ext": item.ext, "playlist_index": item.playlist_index}


def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    objects: list[dict[str, str | int]] = [_item_dict(item) for item in items]
    match mode:
        case JsonMode_Lines():
            return "\n".join(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) for obj in objects)
        case JsonMode_Single():
            return json.dumps(objects, ensure_ascii=False, separators=(",", ":"))
        case _:
            assert_never(mode)
