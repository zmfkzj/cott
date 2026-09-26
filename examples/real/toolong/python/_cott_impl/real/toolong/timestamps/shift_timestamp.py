from datetime import datetime, timedelta

from cott_runtime import I32, Nothing, Option, Some
from real.toolong.model_types import LogTimestamp, TimeUnit, TimeUnit_Hour, TimeUnit_Minute


def _unit_delta(amount: I32, unit: TimeUnit) -> timedelta:
    if isinstance(unit, TimeUnit_Minute):
        return timedelta(minutes=amount)
    elif isinstance(unit, TimeUnit_Hour):
        return timedelta(hours=amount)
    else:
        return timedelta(days=amount)


def shift_timestamp(timestamp: LogTimestamp, amount: I32, unit: TimeUnit) -> Option[LogTimestamp]:
    # Aware datetime + timedelta shifts wall-clock fields and keeps tzinfo,
    # so naive arithmetic on the fields is equivalent.
    base = datetime(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second,
        timestamp.microsecond,
    )
    try:
        result = base + _unit_delta(amount, unit)
    except OverflowError:
        return Nothing()
    return Some(
        value=LogTimestamp(
            year=result.year,
            month=result.month,
            day=result.day,
            hour=result.hour,
            minute=result.minute,
            second=result.second,
            microsecond=result.microsecond,
            utc_offset_seconds=timestamp.utc_offset_seconds,
        )
    )
