from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationState_Draft:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationState_InReview:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationState_Published:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationState_Withdrawn:
    pass

PublicationState: TypeAlias = Union[PublicationState_Draft, PublicationState_InReview, PublicationState_Published, PublicationState_Withdrawn]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationAction_Submit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationAction_Approve:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationAction_Withdraw:
    pass

PublicationAction: TypeAlias = Union[PublicationAction_Submit, PublicationAction_Approve, PublicationAction_Withdraw]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationRequest:
    __hash__ = None
    current: PublicationState
    action: PublicationAction
    has_editor_approval: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationWorkflowError_InvalidTransition:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublicationWorkflowError_ApprovalRequired:
    pass

PublicationWorkflowError: TypeAlias = Union[PublicationWorkflowError_InvalidTransition, PublicationWorkflowError_ApprovalRequired]

"""Return the publication state selected by the workflow transition table, or
Nothing when the state and action do not form a valid transition."""
"""Enforce approval and apply the publication workflow transition requested."""
__all__ = ["PublicationAction", "PublicationAction_Approve", "PublicationAction_Submit", "PublicationAction_Withdraw", "PublicationRequest", "PublicationState", "PublicationState_Draft", "PublicationState_InReview", "PublicationState_Published", "PublicationState_Withdrawn", "PublicationWorkflowError", "PublicationWorkflowError_ApprovalRequired", "PublicationWorkflowError_InvalidTransition"]
