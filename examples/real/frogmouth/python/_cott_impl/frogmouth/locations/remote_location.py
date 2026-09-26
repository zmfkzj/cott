from cott_runtime import Nothing, Option, Some
from frogmouth.model_types import Location, LocationKind_Remote


def remote_location(candidate: str) -> Option[Location]:
    scheme, separator, rest = candidate.partition("://")
    if not separator or not scheme.isascii():
        return Nothing()
    lowered = scheme.lower()
    if lowered not in ("http", "https"):
        return Nothing()
    end = len(rest)
    for delimiter in ("/", "?", "#"):
        index = rest.find(delimiter)
        if index != -1 and index < end:
            end = index
    host = rest[:end].rpartition("@")[2]
    colon = host.rfind(":")
    if colon != -1 and "]" not in host[colon:]:
        host = host[:colon]
    if not host:
        return Nothing()
    return Some(value=Location(kind=LocationKind_Remote(), target=lowered + separator + rest))
