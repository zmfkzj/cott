# clip-ranges

## Purpose
Validate time ranges within a source length and calculate total clip duration.

## Key points
- Reject an empty range list first; each half-open range must start before its end and its end must not exceed the source length.
- Preserve valid ranges as given and accumulate `end_ms - start_ms` with checked `U64` addition; total overflow returns `TotalOverflow`.
