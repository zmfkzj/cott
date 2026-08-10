from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.calculate_age_types import AgeError as AgeError, AgeError_InvalidDate as AgeError_InvalidDate, AgeError_NegativeAge as AgeError_NegativeAge, AgeError_Overflow as AgeError_Overflow, AgeSummary as AgeSummary
"""Calculate the elapsed Gregorian days for an age in whole years ending on the supplied date.

A February 29 anniversary falls on February 28 in a non-leap start year. Validation returns NegativeAge before InvalidDate, and InvalidDate before Overflow."""
def calculate_age_days(age_years: I64, today_year: I64, today_month: I64, today_day: I64) -> Result[I64, AgeError]: ...

"""Build an age summary from the Gregorian day count calculated by calculate_age_days.

On success, name is unchanged, years is age_years, months is age_years * 12, and days is the helper result. Helper errors are propagated unchanged."""
def summarize_age(name: str, age_years: I64, today_year: I64, today_month: I64, today_day: I64) -> Result[AgeSummary, AgeError]: ...

__all__ = ["AgeError", "AgeError_InvalidDate", "AgeError_NegativeAge", "AgeError_Overflow", "AgeSummary", "calculate_age_days", "summarize_age"]
