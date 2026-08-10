from cott_runtime import U64
from curriculum.clip_ranges_types import TimeRange


def range_duration_ms(range: TimeRange) -> U64:
    return range.end_ms - range.start_ms
