from typing import Final, cast

from cott_runtime import CottList, F64, Opaque, U64
from real.toolong.model_types import FileTimestamps, MergedIndex, MergedLine, TimestampEntry

_HEADER_WINDOW: Final[int] = 12


def _sort_key(item: MergedLine) -> tuple[F64, U64]:
    return (item.seconds, item.line)


def merge_timestamps(files: CottList[FileTimestamps], complete: bool) -> MergedIndex:
    lines: list[MergedLine] = []
    breaks: list[tuple[int, ...]] = []
    scanned_size = 0
    file_number = 0
    for file in files:
        scanned_size += file.size
        if file.opened:
            entries = cast(tuple[TimestampEntry, ...], file.entries.unwrap())
            if entries:
                ends = [entry.end for entry in entries]
                ends.append(file.size)
                breaks.append(tuple(ends))
            else:
                breaks.append(())

            fill = 0.0
            fill_until = 0
            for position in range(min(len(entries), _HEADER_WINDOW)):
                if entries[position].seconds != 0.0:
                    fill = entries[position].seconds
                    fill_until = position
                    break
            for position, entry in enumerate(entries):
                seconds = fill if position < fill_until else entry.seconds
                lines.append(MergedLine(seconds=seconds, line=entry.line, file=file_number))
        else:
            breaks.append(())
        file_number += 1

    if complete:
        lines.sort(key=lambda item: _sort_key(item))
    return MergedIndex(
        lines=Opaque(tag="merged_lines", value=tuple(lines)),
        breaks=Opaque(tag="merged_breaks", value=tuple(breaks)),
        scanned_size=scanned_size,
    )
