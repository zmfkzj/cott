from cott_runtime import CottList, Err, Nothing, Ok, Result, Some, U64
from real.toolong_types import LogEntry, LogPage, ToolongError, ToolongError_InvalidLimit


def merge_pages(pages: CottList[LogPage], limit: U64) -> Result[CottList[LogEntry], ToolongError]:
    if limit == 0:
        return Err(error=ToolongError_InvalidLimit())
    ranked: list[tuple[int, str, int, U64, int, LogEntry]] = []
    sequence = 0
    for page_order, page in enumerate(pages):
        for entry in page.entries:
            match entry.timestamp:
                case Some(value=timestamp):
                    ranked.append((0, timestamp, page_order, entry.record, sequence, entry))
                case Nothing():
                    ranked.append((1, "", page_order, entry.record, sequence, entry))
            sequence += 1
    ranked.sort()
    entries: list[LogEntry] = []
    for item in ranked:
        if len(entries) == limit:
            break
        entries.append(item[5])
    return Ok(value=CottList(values=tuple(entries)))
