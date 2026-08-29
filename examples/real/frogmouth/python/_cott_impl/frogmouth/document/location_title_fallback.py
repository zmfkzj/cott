from frogmouth.model_types import (
    Location,
    LocationKind_Codeberg,
    LocationKind_GitHub,
    LocationKind_Local,
    LocationKind_Remote,
)


def location_title_fallback(location: Location) -> str:
    match location.kind:
        case LocationKind_Local():
            target = location.target.rstrip("/\\")
            if target:
                title = target.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                if title:
                    return title
            return "Document"
        case LocationKind_Remote():
            target = location.target.split("#", 1)[0].split("?", 1)[0].rstrip("/")
            if target:
                title = target.rsplit("/", 1)[-1]
                if title:
                    return title
            return "Document"
        case LocationKind_GitHub():
            target = location.target.rstrip("/")
            if target:
                title = target.rsplit("/", 1)[-1]
                if title:
                    return title
            return "Document"
        case LocationKind_Codeberg():
            target = location.target.rstrip("/")
            if target:
                title = target.rsplit("/", 1)[-1]
                if title:
                    return title
            return "Document"
