from pathlib import Path
from urllib.parse import urlparse

from cott_runtime import Err, Ok, Result
from frogmouth.model_types import Location, LocationKind_Http, LocationKind_Local
from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput, NavigationError_UnsupportedScheme


def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]:
    normalized = value.strip()
    if not normalized:
        return Err(error=NavigationError_EmptyInput())

    parsed = urlparse(normalized)
    if parsed.scheme in ("http", "https"):
        return Ok(value=Location(kind=LocationKind_Http(), target=normalized))
    if parsed.scheme:
        return Err(error=NavigationError_UnsupportedScheme(scheme=parsed.scheme))

    path = Path(normalized).expanduser()
    if not path.is_absolute():
        path = working_directory / path
    return Ok(value=Location(kind=LocationKind_Local(), target=str(path.resolve())))
