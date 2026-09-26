from cott_runtime import CottList

from frogmouth.history_types import History, MAXIMUM_HISTORY_LENGTH
from frogmouth.model_types import Location


def remember_location(history: History, location: Location) -> History:
    locations: list[Location] = [*history.locations, location]
    if len(locations) > MAXIMUM_HISTORY_LENGTH:
        locations = locations[len(locations) - MAXIMUM_HISTORY_LENGTH:]
    return History(locations=CottList(values=locations), current=len(locations) - 1)
