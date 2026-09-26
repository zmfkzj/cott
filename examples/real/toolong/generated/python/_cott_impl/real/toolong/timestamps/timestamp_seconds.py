import datetime

from cott_runtime import F64, Some
from real.toolong.model_types import LogTimestamp


def timestamp_seconds(timestamp: LogTimestamp) -> F64:
    offset = timestamp.utc_offset_seconds
    if isinstance(offset, Some):
        tzinfo: datetime.tzinfo | None = datetime.timezone(datetime.timedelta(seconds=offset.value))
    else:
        tzinfo = None
    moment = datetime.datetime(timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second, timestamp.microsecond, tzinfo=tzinfo)
    return moment.timestamp()
