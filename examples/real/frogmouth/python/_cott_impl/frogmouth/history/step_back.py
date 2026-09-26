from cott_runtime import Nothing, Option, Some
from frogmouth.history_types import History


def step_back(history: History) -> Option[History]:
    if history.current == 0:
        return Nothing()
    return Some(value=History(locations=history.locations, current=history.current - 1))
