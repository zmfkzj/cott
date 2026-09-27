import datetime
import re
import warnings
from typing import Final

from cott_runtime import CottList, I32, Nothing, Option, Some, U8
from real.toolong.model_types import LogTimestamp, TimestampScan

_MAX_LINE: Final[int] = 10000
_FORMAT_COUNT: Final[int] = 17


def _pattern(index: int) -> str:
    patterns = (
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\s?(?:Z|[+-]\d{4})",
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}",
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\s?(?:Z|[+-]\d{4})",
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}",
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\s?(?:Z|[+-]\d{4})",
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}\s?(?:Z|[+-]\d{4})",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}\s?(?:Z|[+-]\d{4}Z?)",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\s?(?:Z|[+-]\d{4})",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        r"[JFMASOND][a-z]{2}\s(\s|\d)\d \d{2}:\d{2}:\d{2}",
        r"\d{2}\/\w+\/\d{4} \d{2}:\d{2}:\d{2}",
        r"\d{2}\/\w+\/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}",
        r"\d{10}\.\d+",
        r"\d{13}",
    )
    return patterns[index]


def _parse(index: int, text: str) -> datetime.datetime | None:
    try:
        if index <= 11:
            return datetime.datetime.fromisoformat(text)
        if index == 15:
            return datetime.datetime.fromtimestamp(float(text))
        if index == 16:
            return datetime.datetime.fromtimestamp(int(text))
        if index == 12:
            fmt = "%b %d %H:%M:%S"
        elif index == 13:
            fmt = "%d/%b/%Y %H:%M:%S"
        else:
            fmt = "%d/%b/%Y:%H:%M:%S %z"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return datetime.datetime.strptime(text, fmt)
    except Exception:
        return None


def _to_log_timestamp(value: datetime.datetime) -> LogTimestamp:
    offset = value.utcoffset()
    utc_offset: Option[I32] = Nothing() if offset is None else Some(value=int(offset.total_seconds()))
    return LogTimestamp(
        year=value.year,
        month=value.month,
        day=value.day,
        hour=value.hour,
        minute=value.minute,
        second=value.second,
        microsecond=value.microsecond,
        utc_offset_seconds=utc_offset,
    )


def scan_timestamp(line: str, order: CottList[U8]) -> TimestampScan:
    text = line[:_MAX_LINE]
    for position, element in enumerate(order):
        if element < 0 or element >= _FORMAT_COUNT:
            continue
        match = re.search(_pattern(element), text)
        if match is None:
            continue
        parsed = _parse(element, match.group(0))
        if parsed is None:
            continue
        if position == 0:
            next_order = order
        else:
            elements = [element]
            for current_position, current_element in enumerate(order):
                if current_position != position:
                    elements.append(current_element)
            next_order = CottList(values=elements)
        return TimestampScan(timestamp=Some(value=_to_log_timestamp(parsed)), order=next_order)
    return TimestampScan(timestamp=Nothing(), order=order)
