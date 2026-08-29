from cott_runtime import Nothing, Some
from frogmouth.model_types import (
    Location,
    LocationKind_Codeberg,
    LocationKind_GitHub,
    LocationKind_Local,
    LocationKind_Remote,
)


def display_location(location: Location) -> str:
    match location.kind:
        case LocationKind_Local():
            displayed = location.target
        case LocationKind_Remote():
            displayed = location.target
        case LocationKind_GitHub():
            displayed = f"gh {location.target}"
        case LocationKind_Codeberg():
            displayed = f"cb {location.target}"

    match location.fragment:
        case Some(value=fragment):
            suffix = f"#{fragment}"
        case Nothing():
            suffix = ""

    displayed = f"{displayed}{suffix}"

    if displayed:
        return displayed
    return "location"
