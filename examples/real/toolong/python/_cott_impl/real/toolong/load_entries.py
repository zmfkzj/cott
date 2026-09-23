from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from real.toolong_types import LogEntry, ToolongError, ToolongError_InvalidArguments, ToolongError_ReadFailed


def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]:
    if len(sources) == 0:
        return Err(error=ToolongError_InvalidArguments(message="at least one source is required"))
    entries: list[LogEntry] = []
    for source in sources:
        try:
            with open(source, "r", encoding="utf-8", newline="") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            return Err(error=ToolongError_ReadFailed(path=source, message=str(exc)))
        line = 1
        for raw in text.splitlines():
            entries.append(LogEntry(source=source, line=line, text=raw))
            line += 1
    return Ok(value=CottList(values=entries))
