from pathlib import Path

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Result
from real.toolong import parse_log
from real.toolong_types import LogEntry, ToolongError, ToolongError_ReadFailed


def _read_source(source: Path) -> bytes:
    try:
        return cott_runtime._cott_fixture_read(source)
    except CottContractViolation as exc:
        if exc.message == "fixture adapters are inactive":
            return source.read_bytes()
        if isinstance(exc.__cause__, OSError):
            raise exc.__cause__ from exc
        raise


def load_entries(sources: CottList[Path]) -> Result[CottList[LogEntry], ToolongError]:
    entries: list[LogEntry] = []
    for source in sources:
        try:
            text = _read_source(source).decode("utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as exc:
            return cott_runtime.Err(error=ToolongError_ReadFailed(path=source, message=str(exc)))
        for entry in parse_log(source, text):
            entries.append(entry)
    return cott_runtime.Ok(value=CottList(values=entries))
