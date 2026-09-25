from cott_runtime import CottList
from real.harlequin.core_types import QueryHistory, QueryHistoryEntry


def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory:
    capacity = history.capacity
    if capacity == 0:
        return QueryHistory(entries=CottList(values=[]), capacity=capacity)
    items = [item for item in history.entries]
    items.append(entry)
    if len(items) > capacity:
        items = items[len(items) - capacity :]
    return QueryHistory(entries=CottList(values=items), capacity=capacity)
