from pathlib import Path
from urllib.parse import urljoin

from cott_runtime import Err, Nothing, Ok, Option, Result, Some
from frogmouth.model_types import (
    Location,
    LocationKind_Codeberg,
    LocationKind_GitHub,
    LocationKind_Local,
    LocationKind_Remote,
)
from frogmouth.navigation import resolve_absolute_location
from frogmouth.navigation_types import (
    NavigationError,
    NavigationError_InvalidLocation,
    NavigationError_MissingBase,
)


def resolve_relative_location(value: str, base: Option[Location], working_directory: Path) -> Result[Location, NavigationError]:
    if not value:
        return Err(error=NavigationError_InvalidLocation(value=value))

    fragment_position = value.find("#")
    if fragment_position >= 0:
        target_value = value[:fragment_position]
        fragment_value = value[fragment_position + 1 :]
    else:
        target_value = value
        fragment_value = ""

    if fragment_value:
        fragment = Some(value=fragment_value)
    else:
        fragment = Nothing()

    if not target_value:
        match base:
            case Some(value=base_location):
                if not base_location.target:
                    return Err(error=NavigationError_InvalidLocation(value=value))
                return Ok(value=Location(kind=base_location.kind, target=base_location.target, fragment=fragment))
            case Nothing():
                return Err(error=NavigationError_MissingBase())

    if "\x00" in target_value:
        return Err(error=NavigationError_InvalidLocation(value=value))

    target_path = Path(target_value)
    if target_path.is_absolute():
        return Ok(value=Location(kind=LocationKind_Local(), target=str(target_path), fragment=fragment))

    match base:
        case Nothing():
            local_target = working_directory / target_path
        case Some(value=base_location):
            match base_location.kind:
                case LocationKind_Local():
                    local_target = Path(base_location.target).parent / target_path
                case LocationKind_Remote():
                    return resolve_absolute_location(urljoin(base_location.target, value))
                case LocationKind_GitHub():
                    local_target = working_directory / target_path
                case LocationKind_Codeberg():
                    local_target = working_directory / target_path

    return Ok(value=Location(kind=LocationKind_Local(), target=str(local_target), fragment=fragment))
