from cott_runtime import Nothing, Option, Some

from frogmouth.history_types import History


def step_forward(history: History) -> Option[History]:
    if history.current + 1 >= len(history.locations):
        return Nothing()
    return Some(value=History(locations=history.locations, current=history.current + 1))
