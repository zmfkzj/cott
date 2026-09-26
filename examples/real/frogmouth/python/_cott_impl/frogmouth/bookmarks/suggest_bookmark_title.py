from urllib.parse import urlsplit

from frogmouth.model_types import Location, LocationKind_Remote


def suggest_bookmark_title(location: Location) -> str:
    text = location.target
    if isinstance(location.kind, LocationKind_Remote):
        text = urlsplit(text).path
    return text.rstrip("/").rsplit("/", 1)[-1]
