from os.path import abspath, join
from pathlib import Path
from re import match

from cott_runtime import Err, Ok, Result
from frogmouth.model_types import Location, LocationKind_Http, LocationKind_Local
from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput


def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]:
    target = value.strip()
    if not target:
        return Err(error=NavigationError_EmptyInput())

    scheme_match = match(r"^([A-Za-z][A-Za-z0-9+.-]*):", target)
    if scheme_match is not None:
        scheme = scheme_match.group(1).lower()
        if scheme in ("http", "https"):
            return Ok(value=Location(kind=LocationKind_Http(), target=target))

    return Ok(value=Location(kind=LocationKind_Local(), target=abspath(join(working_directory, target))))
