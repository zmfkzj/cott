from cott_runtime import CottList

from real.pgcli_types import HistoryEntry, HistoryPolicy


def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]:
    items: list[HistoryEntry] = [item for item in entries]
    items.append(entry)
    if policy.unique:
        seen: set[tuple[str, str]] = set()
        kept_reversed: list[HistoryEntry] = []
        for item in reversed(items):
            key = (item.database, item.sql)
            if key in seen:
                continue
            seen.add(key)
            kept_reversed.append(item)
        kept_reversed.reverse()
        items = kept_reversed
    capacity = policy.max_entries
    if capacity == 0:
        return CottList(values=[])
    if len(items) > capacity:
        items = items[len(items) - capacity:]
    return CottList(values=items)
