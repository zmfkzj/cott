from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationEvent_Upvote:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationEvent_Downvote:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationEvent_AcceptedAnswer:
    pass

ReputationEvent: TypeAlias = Union[ReputationEvent_Upvote, ReputationEvent_Downvote, ReputationEvent_AcceptedAnswer]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Reputation:
    __hash__ = None
    value: I32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationRequest:
    __hash__ = None
    starting: I32
    events: CottList[ReputationEvent]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationError_NegativeStarting:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationError_ReputationOverflow:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReputationError_WouldBecomeNegative:
    pass

ReputationError: TypeAlias = Union[ReputationError_NegativeStarting, ReputationError_ReputationOverflow, ReputationError_WouldBecomeNegative]

"""Return the fixed score change for one reputation event.

Upvotes add 10, downvotes subtract 2, and accepted answers add 15."""
"""Fold reputation events in request order from a non-negative starting score.

Reject a negative starting score before processing events. During the fold,
reject the first event that would overflow I32 or make the score negative."""
__all__ = ["Reputation", "ReputationError", "ReputationError_NegativeStarting", "ReputationError_ReputationOverflow", "ReputationError_WouldBecomeNegative", "ReputationEvent", "ReputationEvent_AcceptedAnswer", "ReputationEvent_Downvote", "ReputationEvent_Upvote", "ReputationRequest"]
