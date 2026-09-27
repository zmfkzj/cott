from typing import cast

from cott_runtime import U64
from real.toolong.model_types import ByteSpan, LineLocation, MergedLine, TabIndex, TabIndex_Single


def _span(breaks: tuple[int, ...], scan_start: U64, scanned_size: U64, line: U64) -> ByteSpan:
    count = len(breaks)
    if count == 0:
        return ByteSpan(start=scan_start, end=scan_start)
    position = min(line, count)
    if position == 0:
        return ByteSpan(start=scan_start, end=breaks[0])
    start = breaks[position - 1]
    end = breaks[position] if position < count else max(scanned_size - 1, 0)
    return ByteSpan(start=start, end=end)


def line_location(index: TabIndex, line: U64) -> LineLocation:
    if isinstance(index, TabIndex_Single):
        single = index.index
        breaks = cast(tuple[int, ...], single.breaks.unwrap())
        return LineLocation(file=0, span=_span(breaks, single.scan_start, single.scanned_size, line))
    else:
        merged = index.index
        lines = cast(tuple[MergedLine, ...], merged.lines.unwrap())
        file = 0
        own_line = line
        if line < len(lines):
            entry = lines[line]
            file = entry.file
            own_line = entry.line
        all_breaks = cast(tuple[tuple[int, ...], ...], merged.breaks.unwrap())
        breaks = all_breaks[file] if file < len(all_breaks) else ()
        return LineLocation(file=file, span=_span(breaks, 0, merged.scanned_size, own_line))
