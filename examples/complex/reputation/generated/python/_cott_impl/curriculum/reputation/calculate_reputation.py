from cott_runtime import Err, I32, Ok, Result
from curriculum.reputation import reputation_delta
from curriculum.reputation_types import Reputation, ReputationError, ReputationError_NegativeStarting, ReputationError_ReputationOverflow, ReputationError_WouldBecomeNegative, ReputationRequest


def calculate_reputation(request: ReputationRequest) -> Result[Reputation, ReputationError]:
    if request.starting < 0:
        return Err(error=ReputationError_NegativeStarting())

    score: I32 = request.starting
    for event in request.events:
        next_score: I32 = score + reputation_delta(event)
        if next_score > 2_147_483_647:
            return Err(error=ReputationError_ReputationOverflow())
        if next_score < 0:
            return Err(error=ReputationError_WouldBecomeNegative())
        score = next_score

    return Ok(value=Reputation(value=score))
