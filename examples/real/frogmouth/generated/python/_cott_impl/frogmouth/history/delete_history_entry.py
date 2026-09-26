from cott_runtime import CottList, Nothing, Some, U64
from frogmouth.history_types import History


def delete_history_entry(history: History, history_id: U64) -> Some[History] | Nothing:
    locations = list(history.locations)
    if history_id >= len(locations):
        return Nothing()
    del locations[history_id]
    current = history.current
    if history_id < current:
        current -= 1
    elif current >= len(locations):
        current = max(len(locations) - 1, 0)
    return Some(value=History(locations=CottList(values=locations), current=current))
