from cott_runtime import CottList
from real.harlequin.core_types import QueryHistory, QueryHistoryEntry


def append_query_history(history: QueryHistory, entry: QueryHistoryEntry) -> QueryHistory:
    entries: list[QueryHistoryEntry] = []
    if history.capacity > 0:
        first_retained = max(0, len(history.entries) - history.capacity + 1)
        for index, existing_entry in enumerate(history.entries):
            if index >= first_retained:
                entries.append(existing_entry)
        entries.append(entry)
    return QueryHistory(entries=CottList(values=entries), capacity=history.capacity)
