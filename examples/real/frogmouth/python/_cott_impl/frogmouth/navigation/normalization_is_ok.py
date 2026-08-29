from cott_runtime import Err, Ok, Result
from frogmouth.navigation_types import NavigationError


def normalization_is_ok(result: Result[str, NavigationError]) -> bool:
    """Report whether location normalization succeeded."""
    match result:
        case Ok():
            return True
        case Err():
            return False
