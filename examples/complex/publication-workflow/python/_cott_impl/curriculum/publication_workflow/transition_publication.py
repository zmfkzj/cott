from cott_runtime import Err, Ok, Result
from curriculum.publication_workflow_types import PublicationAction_Approve, PublicationAction_Submit, PublicationRequest, PublicationState, PublicationState_Draft, PublicationState_InReview, PublicationState_Published, PublicationState_Withdrawn, PublicationWorkflowError, PublicationWorkflowError_ApprovalRequired, PublicationWorkflowError_InvalidTransition


def transition_publication(request: PublicationRequest) -> Result[PublicationState, PublicationWorkflowError]:
    if isinstance(request.current, PublicationState_Draft):
        if isinstance(request.action, PublicationAction_Submit):
            return Ok(value=PublicationState_InReview())
    elif isinstance(request.current, PublicationState_InReview):
        if isinstance(request.action, PublicationAction_Approve):
            if not request.has_editor_approval:
                return Err(error=PublicationWorkflowError_ApprovalRequired())
            return Ok(value=PublicationState_Published())
    elif isinstance(request.current, PublicationState_Published):
        if isinstance(request.action, PublicationAction_Submit):
            return Err(error=PublicationWorkflowError_InvalidTransition())
        elif isinstance(request.action, PublicationAction_Approve):
            return Err(error=PublicationWorkflowError_InvalidTransition())
        else:
            return Ok(value=PublicationState_Withdrawn())
    else:
        return Err(error=PublicationWorkflowError_InvalidTransition())
    return Err(error=PublicationWorkflowError_InvalidTransition())
