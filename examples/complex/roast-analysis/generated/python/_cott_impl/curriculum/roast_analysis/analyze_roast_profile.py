from cott_runtime import Err, Ok, Result
from curriculum.roast_analysis import summarize_roast_samples, validate_roast_profile
from curriculum.roast_analysis_types import RoastAnalysis, RoastAnalysisError, RoastProfile


def analyze_roast_profile(profile: RoastProfile) -> Result[RoastAnalysis, RoastAnalysisError]:
    validation = validate_roast_profile(profile)
    if isinstance(validation, Err):
        return Err(error=validation.error)
    return Ok(value=summarize_roast_samples(profile.samples))
