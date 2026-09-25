from pathlib import Path

from cott_runtime import CottList
from real.toolong_types import LogEntry


def parse_log(source: Path, text: str) -> CottList[LogEntry]:
    pieces: list[str] = text.split("\n")
    if pieces[-1] == "":
        pieces.pop()
    entries: list[LogEntry] = []
    for index, piece in enumerate(pieces, start=1):
        if piece.endswith("\r"):
            piece = piece[:-1]
        entries.append(LogEntry(source=source, line=index, text=piece))
    return CottList(values=entries)
