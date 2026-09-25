# cta-row

## Purpose
Decodes a transit row into nominal values with a defined error priority and scenario-observed format boundaries.

## Key points
- `RideRow` combines `RouteCode`, `ServiceDate`, `RideCount`, and `DayType`. Formal success clauses preserve the route and date strings and map `U`, `A`, and `W` to Sunday/public-holiday, Saturday, and weekday variants.
- Conditional clauses require `InvalidDayType` before `InvalidRidership`; the route and date errors remain bare because the full ASCII-route and Gregorian-date predicates are not expressible by the contract intrinsics.
- Scenarios observe all four error-priority positions, route length/digit boundaries, leap-year and year-zero rejection, valid dates and day variants, and exact ride counts at zero, 42, and the signed maximum. They do not exhaustively establish route/date validity or ride-count preservation for every input.
