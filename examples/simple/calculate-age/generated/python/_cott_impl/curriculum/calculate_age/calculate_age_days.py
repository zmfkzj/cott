from cott_runtime import Err, I64, Ok, Result
from curriculum.calculate_age_types import AgeError, AgeError_InvalidDate, AgeError_NegativeAge, AgeError_Overflow


def calculate_age_days(age_years: I64, today_year: I64, today_month: I64, today_day: I64) -> Result[I64, AgeError]:
    if age_years < 0:
        return Err(error=AgeError_NegativeAge())

    today_is_leap = today_year % 4 == 0 and (today_year % 100 != 0 or today_year % 400 == 0)
    if today_year < 1 or today_month < 1 or today_month > 12:
        return Err(error=AgeError_InvalidDate())
    if today_month == 2:
        days_in_month = 29 if today_is_leap else 28
    elif today_month == 4 or today_month == 6 or today_month == 9 or today_month == 11:
        days_in_month = 30
    else:
        days_in_month = 31
    if today_day < 1 or today_day > days_in_month:
        return Err(error=AgeError_InvalidDate())

    if age_years > today_year - 1:
        return Err(error=AgeError_Overflow())

    start_year = today_year - age_years
    start_is_leap = start_year % 4 == 0 and (start_year % 100 != 0 or start_year % 400 == 0)
    start_day = 28 if today_month == 2 and today_day == 29 and not start_is_leap else today_day
    month_offset = 31 * (today_month - 1) if today_month <= 2 else (153 * (today_month - 3) + 2) // 5 + 59
    today_days_before_year = 365 * (today_year - 1) + (today_year - 1) // 4 - (today_year - 1) // 100 + (today_year - 1) // 400
    start_days_before_year = 365 * (start_year - 1) + (start_year - 1) // 4 - (start_year - 1) // 100 + (start_year - 1) // 400
    elapsed_days = today_days_before_year + month_offset + (1 if today_is_leap and today_month > 2 else 0) + today_day - start_days_before_year - month_offset - (1 if start_is_leap and today_month > 2 else 0) - start_day
    if elapsed_days > 9_223_372_036_854_775_807:
        return Err(error=AgeError_Overflow())
    return Ok(value=elapsed_days)
