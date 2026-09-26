from cott_runtime import CottList
from frogmouth.model_types import Location, LocationKind_Remote


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def _path_text(location: Location) -> str:
    target = location.target
    if not isinstance(location.kind, LocationKind_Remote):
        return target
    rest = target.split("://", 1)[1] if "://" in target else target
    end = len(rest)
    for marker in ("?", "#"):
        index = rest.find(marker)
        if index != -1 and index < end:
            end = index
    rest = rest[:end]
    slash = rest.find("/")
    return "" if slash == -1 else rest[slash:]


def is_markdown_location(location: Location, extensions: CottList[str]) -> bool:
    name = _path_text(location).rstrip("/").rsplit("/", 1)[-1].lstrip(".")
    dot = name.rfind(".")
    if dot == -1:
        return False
    suffix = _ascii_lower(name[dot:])
    return any(suffix == extension for extension in extensions)
