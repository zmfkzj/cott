from cott_runtime import Err, Ok, Result
from curriculum.website_connectivity_types import ConnectivityStatus_NotWorking, ConnectivityStatus_Working, WebsiteClassification, WebsiteObservation, WebsiteObservationError, WebsiteObservationError_EmptyUrl, WebsiteObservationError_InvalidStatusCode


def classify_observation(observation: WebsiteObservation) -> Result[WebsiteClassification, WebsiteObservationError]:
    if len(observation.url) == 0:
        return Err(error=WebsiteObservationError_EmptyUrl())
    if observation.status_code < 100 or observation.status_code > 599:
        return Err(error=WebsiteObservationError_InvalidStatusCode())
    if observation.status_code == 200:
        status = ConnectivityStatus_Working()
    else:
        status = ConnectivityStatus_NotWorking()
    return Ok(value=WebsiteClassification(url=observation.url, status=status))
