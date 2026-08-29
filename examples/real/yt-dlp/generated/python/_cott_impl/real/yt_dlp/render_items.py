import json

from cott_runtime import CottList, U64
from real.yt_dlp_types import JsonMode, JsonMode_Lines, JsonMode_Single, MediaItem


def _item_payload(item: MediaItem) -> dict[str, str | U64]:
    return {
        "id": item.id,
        "title": item.title,
        "ext": item.ext,
        "playlist_index": item.playlist_index,
        "url": item.url,
    }


def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    """Render items as compact JSON Lines or one compact JSON array."""
    match mode:
        case JsonMode_Lines():
            return "".join(
                json.dumps(_item_payload(item), ensure_ascii=False, separators=(",", ":")) + "\n"
                for item in items
            )
        case JsonMode_Single():
            return json.dumps(
                [_item_payload(item) for item in items],
                ensure_ascii=False,
                separators=(",", ":"),
            )
