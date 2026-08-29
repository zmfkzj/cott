from cott_runtime import Err, I64, Ok, Result
from curriculum.cta_row_types import (
    DayType,
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
        decoded_day_type: DayType = DayType_SundayHoliday()
    elif day_type == "A":
        decoded_day_type = DayType_Saturday()
    elif day_type == "W":
        decoded_day_type = DayType_Weekday()
    else:
        return Err(error=RideRowError_InvalidDayType())

    if rides < 0 or rides > 9223372036854775807:
        return Err(error=RideRowError_InvalidRidership())

    route_length = len(route)
    if route_length < 1 or route_length > 4:
        return Err(error=RideRowError_InvalidRoute())
    route_has_digit = False
    for character in route:
        if "0" <= character <= "9":
            route_has_digit = True
        elif not "A" <= character <= "Z":
            return Err(error=RideRowError_InvalidRoute())
    if not route_has_digit:
        return Err(error=RideRowError_InvalidRoute())

    if len(date) != 10 or date[2] != "/" or date[5] != "/":
        return Err(error=RideRowError_InvalidDate())
    if not (
        "0" <= date[0] <= "9"
        and "0" <= date[1] <= "9"
        and "0" <= date[3] <= "9"
        and "0" <= date[4] <= "9"
        and "0" <= date[6] <= "9"
        and "0" <= date[7] <= "9"
        and "0" <= date[8] <= "9"
        and "0" <= date[9] <= "9"
    ):
        return Err(error=RideRowError_InvalidDate())

    month = (ord(date[0]) - 48) * 10 + ord(date[1]) - 48
    day = (ord(date[3]) - 48) * 10 + ord(date[4]) - 48
    year = (
        (ord(date[6]) - 48) * 1000
        + (ord(date[7]) - 48) * 100
        + (ord(date[8]) - 48) * 10
        + ord(date[9])
        - 48
    )
    if year < 1 or month < 1 or month > 12:
        return Err(error=RideRowError_InvalidDate())

    if month == 2:
        maximum_day = 29 if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0) else 28
    elif month == 4 or month == 6 or month == 9 or month == 11:
        maximum_day = 30
    else:
        maximum_day = 31
    if day < 1 or day > maximum_day:
        return Err(error=RideRowError_InvalidDate())

    return Ok(
        value=RideRow(
            route=RouteCode(value=route),
            date=ServiceDate(value=date),
            day_type=decoded_day_type,
            rides=RideCount(value=rides),
        )
    )
