from cott_runtime import Err, Ok, Result
from frogmouth.model_types import Location
from frogmouth.navigation_types import NavigationError


def location_resolution_is_ok(result: Result[Location, NavigationError]) -> bool:
    """Report whether location resolution succeeded."""
    match result:
        case Ok():
            return True
        case Err():
            return False
