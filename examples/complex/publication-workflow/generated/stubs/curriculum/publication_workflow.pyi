from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.publication_workflow_types import PublicationAction as PublicationAction, PublicationAction_Approve as PublicationAction_Approve, PublicationAction_Submit as PublicationAction_Submit, PublicationAction_Withdraw as PublicationAction_Withdraw, PublicationRequest as PublicationRequest, PublicationState as PublicationState, PublicationState_Draft as PublicationState_Draft, PublicationState_InReview as PublicationState_InReview, PublicationState_Published as PublicationState_Published, PublicationState_Withdrawn as PublicationState_Withdrawn, PublicationWorkflowError as PublicationWorkflowError, PublicationWorkflowError_ApprovalRequired as PublicationWorkflowError_ApprovalRequired, PublicationWorkflowError_InvalidTransition as PublicationWorkflowError_InvalidTransition
"""Return the publication state selected by the workflow transition table, or
Nothing when the state and action do not form a valid transition."""
def transition_target(current: PublicationState, action: PublicationAction) -> Option[PublicationState]: ...

"""Enforce approval and apply the publication workflow transition requested."""
def transition_publication(request: PublicationRequest) -> Result[PublicationState, PublicationWorkflowError]: ...

__all__ = ["PublicationAction", "PublicationAction_Approve", "PublicationAction_Submit", "PublicationAction_Withdraw", "PublicationRequest", "PublicationState", "PublicationState_Draft", "PublicationState_InReview", "PublicationState_Published", "PublicationState_Withdrawn", "PublicationWorkflowError", "PublicationWorkflowError_ApprovalRequired", "PublicationWorkflowError_InvalidTransition", "transition_publication", "transition_target"]
