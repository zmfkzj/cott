from cott_runtime import CottList
from real.pgcli_types import HistoryEntry, HistoryPolicy


def remember_history(policy: HistoryPolicy, entries: CottList[HistoryEntry], entry: HistoryEntry) -> CottList[HistoryEntry]:
    remembered: list[HistoryEntry] = []
    for existing in entries:
        if not policy.unique or existing.sql != entry.sql:
            remembered.append(existing)
    remembered.append(entry)
    overflow = len(remembered) - policy.max_entries
    if overflow > 0:
        remembered = remembered[overflow:]
    return CottList(values=remembered)
