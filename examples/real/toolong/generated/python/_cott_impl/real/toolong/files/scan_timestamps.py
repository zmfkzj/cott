from typing import Final

from cott_runtime import U8, U64, CottList, Opaque, Some
from real.toolong.files import read_span
from real.toolong.files_types import TimestampBatch
from real.toolong.model_types import ByteSpan, LogSource, TimestampEntry
from real.toolong.timestamps import scan_timestamp, timestamp_seconds

_CHUNK: Final[int] = 65536


def scan_timestamps(source: LogSource, position: U64, first_line: U64, limit: U64, order: CottList[U8]) -> TimestampBatch:
    entries: list[TimestampEntry] = []
    current = order
    offset = position
    buffer = b""
    start = 0
    read_to = position
    size = source.size
    while len(entries) < limit and offset < size:
        newline = buffer.find(b"\n", start)
        if newline < 0 and read_to < size:
            chunk = read_span(source, ByteSpan(start=read_to, end=min(size, read_to + _CHUNK)))
            if not chunk:
                size = read_to
            else:
                buffer = buffer[start:] + chunk
                start = 0
                read_to += len(chunk)
            continue
        cut = len(buffer) if newline < 0 else newline + 1
        if cut <= start:
            break
        line = buffer[start:cut]
        start = cut
        offset += len(line)
        scan = scan_timestamp(line.decode("utf-8", errors="replace"), current)
        current = scan.order
        found = scan.timestamp
        if isinstance(found, Some):
            seconds = timestamp_seconds(found.value)
        else:
            seconds = 0.0
        entries.append(TimestampEntry(line=first_line + len(entries), end=offset, seconds=seconds))
    return TimestampBatch(entries=Opaque(tag="timestamp_entries", value=tuple(entries)), position=offset, order=current)
