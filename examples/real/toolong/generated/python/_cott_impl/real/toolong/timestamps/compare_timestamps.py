from datetime import datetime, timedelta, timezone

from cott_runtime import I8, Nothing, Option, Some
from real.toolong.model_types import LogTimestamp


def _to_datetime(timestamp: LogTimestamp) -> datetime:
    offset = timestamp.utc_offset_seconds
    if isinstance(offset, Some):
        tz: timezone | None = timezone(timedelta(seconds=offset.value))
    else:
        tz = None
    return datetime(timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second, timestamp.microsecond, tzinfo=tz)


def compare_timestamps(left: LogTimestamp, right: LogTimestamp) -> Option[I8]:
    left_aware = isinstance(left.utc_offset_seconds, Some)
    right_aware = isinstance(right.utc_offset_seconds, Some)
    if left_aware != right_aware:
        return Nothing()
    a = _to_datetime(left)
    b = _to_datetime(right)
    if a < b:
        return Some(value=-1)
    if a > b:
        return Some(value=1)
    return Some(value=0)
