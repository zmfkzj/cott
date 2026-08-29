from cott_runtime import Err, Ok, Result
from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput


def normalize_location_input(value: str) -> Result[str, NavigationError]:
    normalized = value.strip()
    if not normalized:
        return Err(error=NavigationError_EmptyInput())
    return Ok(value=normalized)
