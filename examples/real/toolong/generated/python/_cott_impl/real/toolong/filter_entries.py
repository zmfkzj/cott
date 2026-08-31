from cott_runtime import CottList, Option, Some
from real.toolong_types import LogEntry


def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]:
    if isinstance(contains, Some):
        needle = contains.value.casefold()
        return CottList(values=tuple(entry for entry in entries if needle in entry.text.casefold()))
    else:
        return entries
