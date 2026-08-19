# cta-row

## Purpose
Decodes string and integer input into a public-transit row with an enum and nominal types in a defined order.

## Key points
- The `DayType` enum maps `U`, `A`, and `W` to Sunday/public-holiday, Saturday, and weekday variants, respectively; successful values are stored in `RideRow`.
- `RideRow` combines the `RouteCode`, `ServiceDate`, and `RideCount` nominal types with `DayType` to represent a validated row.
- The implementation returns the first error in this order: day type, ride count, route, date. A route is 1–4 ASCII uppercase letters or digits containing at least one digit, and a date must be a valid `MM/DD/YYYY` Gregorian-calendar date.
