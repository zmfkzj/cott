from cott_runtime import CottList
from real.toolong_types import LogEntry


def render_entries(entries: CottList[LogEntry]) -> str:
    return "\n".join(f"{entry.source}:{entry.line} {entry.text}" for entry in entries)
