from cott_runtime import CottList
from real.harlequin.core_types import QueryHistory, QueryHistoryEntry


def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory:
    capacity = history.capacity
    items = [item for item in history.entries]
    items.append(entry)
    if capacity == 0:
        items = []
    elif len(items) > capacity:
        items = items[len(items) - capacity :]
    return QueryHistory(entries=CottList(values=items), capacity=capacity)
