from cott_runtime import Nothing, Option, Some
from curriculum.publication_workflow_types import PublicationAction, PublicationAction_Approve, PublicationAction_Submit, PublicationAction_Withdraw, PublicationState, PublicationState_Draft, PublicationState_InReview, PublicationState_Published, PublicationState_Withdrawn


def transition_target(current: PublicationState, action: PublicationAction) -> Option[PublicationState]:
    if isinstance(current, PublicationState_Draft):
        if isinstance(action, PublicationAction_Submit):
            return Some(value=PublicationState_InReview())
    elif isinstance(current, PublicationState_InReview):
        if isinstance(action, PublicationAction_Approve):
            return Some(value=PublicationState_Published())
    elif isinstance(current, PublicationState_Published):
        if isinstance(action, PublicationAction_Withdraw):
            return Some(value=PublicationState_Withdrawn())
    return Nothing()
