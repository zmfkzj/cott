# calculate-age

## Purpose
Calculate Gregorian elapsed days and an age summary from a reference date and full age in years.

## Key points
- `calculate_age_days` returns negative age, invalid date, and overflow as `AgeError` in priority order.
- For a February 29 reference date, it adjusts the anniversary to February 28 in a non-leap start year to handle leap-year boundaries.
- `summarize_age` propagates helper errors unchanged and bundles the name, years, months (`years * 12`), and elapsed days in `AgeSummary`.
