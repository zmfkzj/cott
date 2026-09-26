from cott_runtime import CottList

from frogmouth.history_types import MAXIMUM_HISTORY_LENGTH, History
from frogmouth.model_types import Location


def start_history(locations: CottList[Location]) -> History:
    kept = list(locations)
    if len(kept) > MAXIMUM_HISTORY_LENGTH:
        kept = kept[len(kept) - MAXIMUM_HISTORY_LENGTH:]
    current = len(kept) - 1 if kept else 0
    return History(locations=CottList(values=kept), current=current)
