from typing import Final

from cott_runtime import CottList, Opaque, Some, U8, U64
from real.toolong.files import read_span
from real.toolong.files_types import TimestampBatch
from real.toolong.model_types import ByteSpan, LogSource, TimestampEntry
from real.toolong.timestamps import scan_timestamp, timestamp_seconds

_CHUNK: Final[int] = 65536


def scan_timestamps(source: LogSource, position: U64, first_line: U64, limit: U64, order: CottList[U8]) -> TimestampBatch:
    entries: list[TimestampEntry] = []
    current = order
    offset = position
    read_to = position
    size = source.size
    buffer = b""
    start = 0
    fragments: list[bytes] = []

    while len(entries) < limit and offset < size:
        if start == len(buffer) and read_to < size:
            buffer = read_span(source, ByteSpan(start=read_to, end=min(size, read_to + _CHUNK)))
            start = 0
            read_to += len(buffer)
            if not buffer:
                size = read_to

        newline = buffer.find(b"\n", start)
        if newline < 0:
            if start < len(buffer):
                fragments.append(buffer[start:])
                start = len(buffer)
            if read_to < size:
                continue
            if not fragments:
                break
            line = b"".join(fragments)
            fragments.clear()
        else:
            if fragments:
                fragments.append(buffer[start:newline + 1])
                line = b"".join(fragments)
                fragments.clear()
            else:
                line = buffer[start:newline + 1]
            start = newline + 1

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
