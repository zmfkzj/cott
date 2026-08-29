from cott_runtime import CottList, Err, Ok, Result, U64
from real.toolong_types import LogEntry, ToolongError, ToolongError_InvalidLimit


def search_entries(entries: CottList[LogEntry], needle: str, limit: U64) -> Result[CottList[LogEntry], ToolongError]:
    if limit == 0:
        return Err(error=ToolongError_InvalidLimit())
    folded_needle = needle.casefold()
    found: list[LogEntry] = []
    for entry in entries:
        if folded_needle in entry.text.casefold():
            found.append(entry)
            if len(found) == limit:
                break
    return Ok(value=CottList(values=tuple(found)))
