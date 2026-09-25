from pathlib import Path

from cott_runtime import Err, Ok, Result
from frogmouth.model_types import Location, LocationKind_Http, LocationKind_Local
from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput, NavigationError_UnsupportedScheme


def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]:
    if value == "":
        return Err(error=NavigationError_EmptyInput())
    if value.startswith("http://") or value.startswith("https://"):
        return Ok(value=Location(kind=LocationKind_Http(), target=value))
    scheme, separator, _ = value.partition("://")
    if separator:
        return Err(error=NavigationError_UnsupportedScheme(scheme=scheme))
    if value.startswith("/"):
        return Ok(value=Location(kind=LocationKind_Local(), target=value))
    base = str(working_directory)
    joiner = "" if base.endswith("/") else "/"
    return Ok(value=Location(kind=LocationKind_Local(), target=base + joiner + value))
