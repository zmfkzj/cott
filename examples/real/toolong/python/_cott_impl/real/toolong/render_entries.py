from cott_runtime import CottList
from real.toolong_types import LogEntry


def render_entries(entries: CottList[LogEntry]) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(f"{entry.source}:{entry.line} {entry.text}")
    return "\n".join(lines)
