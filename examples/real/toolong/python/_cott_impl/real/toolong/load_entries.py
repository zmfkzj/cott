from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from real.toolong_types import LogEntry, ToolongError, ToolongError_ReadFailed


def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]:
    if len(sources) == 0:
        return Err(
            error=ToolongError_ReadFailed(
                path=Path(),
                message="no sources were provided",
            )
        )
    for source in sources:
        if not source.is_file():
            return Err(
                error=ToolongError_ReadFailed(
                    path=source,
                    message="source is not a readable file",
                )
            )
    return Ok(
        value=CottList(
            values=tuple(
                LogEntry(source=source, line=line, text=text)
                for source in sources
                for line, text in enumerate(
                    source.read_text(encoding="utf-8").splitlines(),
                    start=1,
                )
            )
        )
    )
