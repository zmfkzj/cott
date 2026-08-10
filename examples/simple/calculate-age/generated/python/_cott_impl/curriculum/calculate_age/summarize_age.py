from cott_runtime import Err, I64, Ok, Result
from curriculum.calculate_age import calculate_age_days
from curriculum.calculate_age_types import AgeError, AgeSummary


def summarize_age(name: str, age_years: I64, today_year: I64, today_month: I64, today_day: I64) -> Result[AgeSummary, AgeError]:
    days_result = calculate_age_days(age_years, today_year, today_month, today_day)
    if isinstance(days_result, Err):
        return Err(error=days_result.error)
    return Ok(value=AgeSummary(name=name, years=age_years, months=age_years * 12, days=days_result.value))
