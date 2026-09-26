from cott_runtime import Nothing, Option, Some
from frogmouth.history_types import History
from frogmouth.model_types import Location


def current_location(history: History) -> Option[Location]:
    if len(history.locations) == 0:
        return Nothing()
    return Some(value=history.locations[history.current])
