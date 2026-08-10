from cott_runtime import I32
from curriculum.reputation_types import ReputationEvent, ReputationEvent_Downvote, ReputationEvent_Upvote


def reputation_delta(event: ReputationEvent) -> I32:
    if isinstance(event, ReputationEvent_Upvote):
        return 10
    if isinstance(event, ReputationEvent_Downvote):
        return -2
    return 15
