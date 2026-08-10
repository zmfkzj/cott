from cott_runtime import Err, I64, Ok, Result
from curriculum.cta_row_types import (
    DayType_Saturday,
    DayType_SundayHoliday,
    DayType_Weekday,
    RideCount,
    RideRow,
    RideRowError,
    RideRowError_InvalidDate,
    RideRowError_InvalidDayType,
    RideRowError_InvalidRidership,
    RideRowError_InvalidRoute,
    RouteCode,
    ServiceDate,
)


def decode_row(route: str, date: str, day_type: str, rides: I64) -> Result[RideRow, RideRowError]:
    if day_type == "U":
        mapped_day_type = DayType_SundayHoliday()
    elif day_type == "A":
        mapped_day_type = DayType_Saturday()
    elif day_type == "W":
        mapped_day_type = DayType_Weekday()
    else:
        return Err(error=RideRowError_InvalidDayType())

    if rides < 0 or rides > 9_223_372_036_854_775_807:
        return Err(error=RideRowError_InvalidRidership())

    has_digit = False
    if not 1 <= len(route) <= 4:
        return Err(error=RideRowError_InvalidRoute())
    for character in route:
        if "0" <= character <= "9":
            has_digit = True
        elif not "A" <= character <= "Z":
            return Err(error=RideRowError_InvalidRoute())
    if not has_digit:
        return Err(error=RideRowError_InvalidRoute())

    if len(date) != 10 or date[2] != "/" or date[5] != "/":
        return Err(error=RideRowError_InvalidDate())
    for index in (0, 1, 3, 4, 6, 7, 8, 9):
        if not "0" <= date[index] <= "9":
            return Err(error=RideRowError_InvalidDate())

    month = (ord(date[0]) - ord("0")) * 10 + ord(date[1]) - ord("0")
    day = (ord(date[3]) - ord("0")) * 10 + ord(date[4]) - ord("0")
    year = (
        (ord(date[6]) - ord("0")) * 1000
        + (ord(date[7]) - ord("0")) * 100
        + (ord(date[8]) - ord("0")) * 10
        + ord(date[9])
        - ord("0")
    )
    if not 1 <= month <= 12 or year == 0:
        return Err(error=RideRowError_InvalidDate())

    days_in_month = 31
    if month == 2:
        days_in_month = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
    elif month in (4, 6, 9, 11):
        days_in_month = 30
    if not 1 <= day <= days_in_month:
        return Err(error=RideRowError_InvalidDate())

    return Ok(
        value=RideRow(
            route=RouteCode(value=route),
            date=ServiceDate(value=date),
            day_type=mapped_day_type,
            rides=RideCount(value=rides),
        )
    )
