from cott_runtime import Err, Ok, Result, U64
from curriculum.clip_ranges import range_duration_ms
from curriculum.clip_ranges_types import ClipPlan, ClipRangeError, ClipRangeError_EmptyRanges, ClipRangeError_PastDuration, ClipRangeError_StartNotBeforeEnd, ClipRangeError_TotalOverflow, ClipRequest


def plan_clip_ranges(request: ClipRequest) -> Result[ClipPlan, ClipRangeError]:
    if len(request.ranges) == 0:
        return Err(error=ClipRangeError_EmptyRanges())

    total_ms: U64 = 0
    max_u64: U64 = 18_446_744_073_709_551_615
    for time_range in request.ranges:
        if time_range.start_ms >= time_range.end_ms:
            return Err(error=ClipRangeError_StartNotBeforeEnd())
        if time_range.end_ms > request.duration_ms:
            return Err(error=ClipRangeError_PastDuration())

        duration_ms: U64 = range_duration_ms(time_range)
        if total_ms > max_u64 - duration_ms:
            return Err(error=ClipRangeError_TotalOverflow())
        total_ms += duration_ms

    return Ok(value=ClipPlan(ranges=request.ranges, total_ms=total_ms))
