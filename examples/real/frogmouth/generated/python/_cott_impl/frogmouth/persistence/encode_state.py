import json

from frogmouth.model_types import BrowserState


def encode_state(current: BrowserState) -> str:
    return json.dumps(
        {"history": list(current.history), "bookmarks": list(current.bookmarks)},
        ensure_ascii=True,
        separators=(",", ":"),
    )
