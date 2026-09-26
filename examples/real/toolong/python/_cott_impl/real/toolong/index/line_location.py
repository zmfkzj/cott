from typing import cast

from cott_runtime import U32, U64
from real.toolong.model_types import ByteSpan, LineLocation, MergedLine, TabIndex, TabIndex_Single


def _span(breaks: tuple[int, ...], scan_start: U64, scanned_size: U64, line: U64) -> ByteSpan:
    n = len(breaks)
    if n == 0:
        return ByteSpan(start=scan_start, end=scan_start)
    i = line if line < n else n
    if i == 0:
        return ByteSpan(start=scan_start, end=breaks[0])
    start = breaks[i - 1]
    if i < n:
        return ByteSpan(start=start, end=breaks[i])
    end = scanned_size - 1 if scanned_size > 0 else 0
    return ByteSpan(start=start, end=end)


def line_location(index: TabIndex, line: U64) -> LineLocation:
    if isinstance(index, TabIndex_Single):
        single = index.index
        breaks = cast(tuple[int, ...], single.breaks.unwrap())
        return LineLocation(file=0, span=_span(breaks, single.scan_start, single.scanned_size, line))
    else:
        merged = index.index
        lines = cast(tuple[MergedLine, ...], merged.lines.unwrap())
        file: U32 = 0
        own: U64 = line
        if line < len(lines):
            entry = lines[line]
            file = entry.file
            own = entry.line
        all_breaks = cast(tuple[tuple[int, ...], ...], merged.breaks.unwrap())
        file_breaks: tuple[int, ...] = all_breaks[file] if file < len(all_breaks) else ()
        return LineLocation(file=file, span=_span(file_breaks, 0, merged.scanned_size, own))
