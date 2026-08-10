from cott_runtime import Err, Ok, Result, U32, Unit, UNIT
from curriculum.roast_analysis_types import RoastAnalysisError, RoastAnalysisError_EmptySamples, RoastAnalysisError_NonIncreasingTime, RoastProfile


def validate_roast_profile(profile: RoastProfile) -> Result[Unit, RoastAnalysisError]:
    if len(profile.samples) == 0:
        return Err(error=RoastAnalysisError_EmptySamples())

    samples_iterator = iter(profile.samples)
    first_sample = next(samples_iterator)
    previous_elapsed_s: U32 = first_sample.elapsed_s
    for sample in samples_iterator:
        if sample.elapsed_s <= previous_elapsed_s:
            return Err(error=RoastAnalysisError_NonIncreasingTime())
        previous_elapsed_s = sample.elapsed_s

    return Ok(value=UNIT)
