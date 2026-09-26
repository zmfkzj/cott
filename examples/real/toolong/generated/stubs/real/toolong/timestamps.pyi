from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit
from real.toolong.model_types import LogTimestamp, TimeUnit, TimestampScan
"""The timestamp scanner's initial format order: List(0, 1, 2, ..., 16), the
indexes of the format table documented on
real.toolong.timestamps.scan_timestamp in table order."""
def default_timestamp_order() -> CottList[U8]: ...

"""Toolong's TimestampScanner.scan for one line. When line is longer than
10000 code points only its first 10000 code points are scanned. The format
table (index: Python regular expression -> parser) is:

0: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2},\\d{3}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
1: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2},\\d{3} -> datetime.fromisoformat
2: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
3: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3} -> datetime.fromisoformat
4: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
5: \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2} -> datetime.fromisoformat
6: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2},\\d{3}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
7: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2},\\d{3} -> datetime.fromisoformat
8: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\s?(?:Z|[+-]\\d{4}Z?) -> datetime.fromisoformat
9: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3} -> datetime.fromisoformat
10: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\s?(?:Z|[+-]\\d{4}) -> datetime.fromisoformat
11: \\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2} -> datetime.fromisoformat
12: [JFMASOND][a-z]{2}\\s(\\s|\\d)\\d \\d{2}:\\d{2}:\\d{2} -> datetime.strptime(text, "%b %d %H:%M:%S")
13: \\d{2}\\/\\w+\\/\\d{4} \\d{2}:\\d{2}:\\d{2} -> datetime.strptime(text, "%d/%b/%Y %H:%M:%S")
14: \\d{2}\\/\\w+\\/\\d{4}:\\d{2}:\\d{2}:\\d{2} [+-]\\d{4} -> datetime.strptime(text, "%d/%b/%Y:%H:%M:%S %z")
15: \\d{10}\\.\\d+ -> datetime.fromtimestamp(float(text))
16: \\d{13} -> datetime.fromtimestamp(int(text))

Visit the formats in the given order (each element is a table index; an
element that is not a table index is skipped). For a format, find the
first match of its regular expression anywhere in the line (re.search) and
give the whole matched text to its parser, as CPython 3.14 does (the
fromtimestamp parsers use the host local time zone; strptime month names
follow the current LC_TIME locale and never emit a warning to the user). A
format with no match, or whose parser raises or returns nothing, is
skipped. For the first format that yields a datetime, return it as a
LogTimestamp (utc_offset_seconds is the whole seconds of its utcoffset()
when it is aware) together with the order changed so that this format's
element moves to the front (the order is unchanged when it is already
first). When no format yields a datetime, timestamp is Nothing and the
order is returned unchanged."""
def scan_timestamp(line: str, order: CottList[U8]) -> TimestampScan: ...

"""Add amount minutes, hours or days (a day is 24 hours) to the timestamp as
CPython datetime + timedelta does, keeping utc_offset_seconds. amount may be
negative. Nothing when the result falls outside years 1-9999."""
def shift_timestamp(timestamp: LogTimestamp, amount: I32, unit: TimeUnit) -> Option[LogTimestamp]: ...

"""Compare two timestamps like CPython datetimes. When both are naive, compare
their fields (year, month, day, hour, minute, second, microsecond)
lexicographically. When both are aware, compare the UTC instants they
denote. Return Some(-1), Some(0) or Some(1) when left is earlier than,
equal to or later than right. Mixing a naive and an aware timestamp is not
comparable and returns Nothing."""
def compare_timestamps(left: LogTimestamp, right: LogTimestamp) -> Option[I8]: ...

"""POSIX seconds of the timestamp, as CPython datetime.timestamp() returns
them: an aware timestamp denotes an exact instant; a naive timestamp is
interpreted in the host local time zone."""
def timestamp_seconds(timestamp: LogTimestamp) -> F64: ...

"""The footer rendering of a timestamp: CPython strftime("%x %X") of the
datetime (with its UTC offset when aware), using the process's current
LC_TIME locale. In the C/POSIX locale this is "MM/DD/YY HH:MM:SS"."""
def format_local_timestamp(timestamp: LogTimestamp) -> str: ...

__all__ = ["compare_timestamps", "default_timestamp_order", "format_local_timestamp", "scan_timestamp", "shift_timestamp", "timestamp_seconds"]
