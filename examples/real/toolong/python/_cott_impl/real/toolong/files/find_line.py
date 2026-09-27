from cott_runtime import CottList, I8, I64, Nothing, Some, U64

from real.toolong.files import read_span
from real.toolong.files_types import FindResult
from real.toolong.index import line_location
from real.toolong.model_types import FindQuery, LogSource, TabIndex
from real.toolong.text import line_matches


def _raw_line(sources: CottList[LogSource], index: TabIndex, line: U64) -> str:
    location = line_location(index, line)
    position = 0
    for source in sources:
        if position == location.file:
            return read_span(source, location.span).decode("utf-8", errors="replace")
        position += 1
    return ""


def find_line(sources: CottList[LogSource], index: TabIndex, line_count: U64, start: I64, direction: I8, query: FindQuery) -> FindResult:
    if start < 0 or start >= line_count:
        return FindResult(line=Nothing(), invalid_regex=False)
    lines = range(start, line_count) if direction > 0 else range(start, -1, -1)
    for line in lines:
        outcome = line_matches(_raw_line(sources, index, line), query)
        if outcome.matched:
            return FindResult(line=Some(value=line), invalid_regex=outcome.invalid_regex)
    return FindResult(line=Nothing(), invalid_regex=False)
