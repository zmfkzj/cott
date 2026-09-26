from datetime import datetime, timedelta, timezone

from cott_runtime import Some
from real.toolong.model_types import LogTimestamp


def format_local_timestamp(timestamp: LogTimestamp) -> str:
    offset = timestamp.utc_offset_seconds
    if isinstance(offset, Some):
        tzinfo: timezone | None = timezone(timedelta(seconds=offset.value))
    else:
        tzinfo = None
    moment = datetime(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second,
        timestamp.microsecond,
        tzinfo=tzinfo,
    )
    return moment.strftime("%x %X")
