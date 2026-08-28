from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DayType_SundayHoliday:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DayType_Saturday:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DayType_Weekday:
    pass

DayType: TypeAlias = Union[DayType_SundayHoliday, DayType_Saturday, DayType_Weekday]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RouteCode:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ServiceDate:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RideCount:
    value: U64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, U64, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RideRow:
    __hash__ = None
    route: RouteCode
    date: ServiceDate
    day_type: DayType
    rides: RideCount

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RideRowError_InvalidDayType:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RideRowError_InvalidRidership:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RideRowError_InvalidRoute:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RideRowError_InvalidDate:
    pass

RideRowError: TypeAlias = Union[RideRowError_InvalidDayType, RideRowError_InvalidRidership, RideRowError_InvalidRoute, RideRowError_InvalidDate]

"""Purely decode and validate one transit ridership row. Validation is performed in day_type, rides, route, date order and returns the corresponding first error. day_type maps U to SundayHoliday, A to Saturday, and W to Weekday. A valid route contains one to four ASCII uppercase letters or digits and at least one digit. A valid date is a Gregorian date in canonical MM/DD/YYYY form with a year from 0001 through 9999. rides must be from 0 through 9223372036854775807.

Success returns a RideRow containing nominal RouteCode, ServiceDate, and RideCount values and the mapped DayType variant. The function has no external effects."""
__all__ = ["DayType", "DayType_Saturday", "DayType_SundayHoliday", "DayType_Weekday", "RideCount", "RideRow", "RideRowError", "RideRowError_InvalidDate", "RideRowError_InvalidDayType", "RideRowError_InvalidRidership", "RideRowError_InvalidRoute", "RouteCode", "ServiceDate"]
