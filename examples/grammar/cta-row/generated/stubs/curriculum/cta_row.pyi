from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.cta_row_types import DayType as DayType, DayType_Saturday as DayType_Saturday, DayType_SundayHoliday as DayType_SundayHoliday, DayType_Weekday as DayType_Weekday, RideCount as RideCount, RideRow as RideRow, RideRowError as RideRowError, RideRowError_InvalidDate as RideRowError_InvalidDate, RideRowError_InvalidDayType as RideRowError_InvalidDayType, RideRowError_InvalidRidership as RideRowError_InvalidRidership, RideRowError_InvalidRoute as RideRowError_InvalidRoute, RouteCode as RouteCode, ServiceDate as ServiceDate
"""Purely decode and validate one transit ridership row. Validation is performed in day_type, rides, route, date order and returns the corresponding first error. day_type maps U to SundayHoliday, A to Saturday, and W to Weekday. A valid route contains one to four ASCII uppercase letters or digits and at least one digit. A valid date is a Gregorian date in canonical MM/DD/YYYY form with a year from 0001 through 9999. rides must be from 0 through 9223372036854775807.

Success returns a RideRow containing nominal RouteCode, ServiceDate, and RideCount values and the mapped DayType variant. The function has no external effects."""
def decode_row(route: str, date: str, day_type: str, rides: I64) -> Result[RideRow, RideRowError]: ...

__all__ = ["DayType", "DayType_Saturday", "DayType_SundayHoliday", "DayType_Weekday", "RideCount", "RideRow", "RideRowError", "RideRowError_InvalidDate", "RideRowError_InvalidDayType", "RideRowError_InvalidRidership", "RideRowError_InvalidRoute", "RouteCode", "ServiceDate", "decode_row"]
