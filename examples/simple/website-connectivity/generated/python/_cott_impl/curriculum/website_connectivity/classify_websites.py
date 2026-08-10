from cott_runtime import CottList, Err, Ok, Result
from curriculum.website_connectivity import classify_observation
from curriculum.website_connectivity_types import WebsiteClassification, WebsiteObservation, WebsiteObservationError


def classify_websites(observations: CottList[WebsiteObservation]) -> Result[CottList[WebsiteClassification], WebsiteObservationError]:
    classifications: list[WebsiteClassification] = []
    for observation in observations:
        result = classify_observation(observation)
        if isinstance(result, Err):
            return Err(error=result.error)
        classifications.append(result.value)
    return Ok(value=CottList(values=classifications))
