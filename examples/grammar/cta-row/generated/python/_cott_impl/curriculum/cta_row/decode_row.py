from cott_runtime import Err, I64, Ok, Result
from curriculum.cta_row_types import DayType, DayType_Saturday, DayType_SundayHoliday, DayType_Weekday, RideCount, RideRow, RideRowError, RideRowError_InvalidDate, RideRowError_InvalidDayType, RideRowError_InvalidRidership, RideRowError_InvalidRoute, RouteCode, ServiceDate


def _valid_route(value: str) -> bool:
    if not 1 <= len(value) <= 4:
        return False
    has_digit = False
    for char in value:
        if "0" <= char <= "9":
            has_digit = True
        elif not "A" <= char <= "Z":
            return False
    return has_digit


def _valid_date(value: str) -> bool:
    if len(value) != 10 or value[2] != "/" or value[5] != "/":
        return False
    digits = value[:2] + value[3:5] + value[6:]
    if not all("0" <= char <= "9" for char in digits):
        return False
    month = int(value[:2])
    day = int(value[3:5])
    year = int(value[6:])
    if year == 0 or not 1 <= month <= 12:
        return False
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        maximum = 29 if leap else 28
    elif month in (4, 6, 9, 11):
        maximum = 30
    else:
        maximum = 31
    return 1 <= day <= maximum


def decode_row(route: str, date: str, day_type: str, rides: I64) -> Result[RideRow, RideRowError]:
    mapped_day: DayType
    if day_type == "U":
        mapped_day = DayType_SundayHoliday()
    elif day_type == "A":
        mapped_day = DayType_Saturday()
    elif day_type == "W":
        mapped_day = DayType_Weekday()
    else:
        return Err(error=RideRowError_InvalidDayType())
    if not 0 <= rides <= 9223372036854775807:
        return Err(error=RideRowError_InvalidRidership())
    if not _valid_route(route):
        return Err(error=RideRowError_InvalidRoute())
    if not _valid_date(date):
        return Err(error=RideRowError_InvalidDate())
    return Ok(value=RideRow(route=RouteCode(value=route), date=ServiceDate(value=date), day_type=mapped_day, rides=RideCount(value=rides)))
