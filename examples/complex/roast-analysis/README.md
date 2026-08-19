# roast-analysis

## Purpose
Validate time-ordered roasting-temperature samples, then calculate the peak and total temperature increase.

## Key points
- Reject empty samples with `EmptySamples` first; then return `NonIncreasingTime` if elapsed time is not strictly increasing.
- After successful validation, make one pass through the samples to find the time of the first maximum temperature and the `I64` increase from the first temperature to the last.
