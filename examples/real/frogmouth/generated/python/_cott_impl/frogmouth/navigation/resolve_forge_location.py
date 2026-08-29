from cott_runtime import Err, Nothing, Ok, Result, Some
from frogmouth.model_types import Location, LocationKind_Codeberg, LocationKind_GitHub
from frogmouth.navigation_types import NavigationError, NavigationError_InvalidLocation


def resolve_forge_location(value: str) -> Result[Location, NavigationError]:
    separator = value.find(" ")
    if separator < 0:
        return Err(error=NavigationError_InvalidLocation(value=value))

    forge = value[:separator]
    repository_with_fragment = value[separator + 1 :]
    if forge == "gh":
        kind = LocationKind_GitHub()
    elif forge == "cb" or forge == "codeberg":
        kind = LocationKind_Codeberg()
    else:
        return Err(error=NavigationError_InvalidLocation(value=value))

    fragment_position = repository_with_fragment.find("#")
    if fragment_position >= 0:
        repository = repository_with_fragment[:fragment_position]
        fragment_value = repository_with_fragment[fragment_position + 1 :]
    else:
        repository = repository_with_fragment
        fragment_value = ""

    if not repository:
        return Err(error=NavigationError_InvalidLocation(value=value))

    if fragment_value:
        fragment = Some(value=fragment_value)
    else:
        fragment = Nothing()
    return Ok(value=Location(kind=kind, target=repository, fragment=fragment))
