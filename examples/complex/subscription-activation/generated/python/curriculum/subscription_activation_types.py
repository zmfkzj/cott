from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class SubscriptionId:
    value: int

@dataclass(frozen=True, slots=True, kw_only=True)
class Subscription:
    id: SubscriptionId
    active: bool

@dataclass(frozen=True, slots=True, kw_only=True)
class AlreadyActive:
    pass

SubscriptionError: TypeAlias = Union[AlreadyActive]

__all__ = ["SubscriptionId", "Subscription", "SubscriptionError", "AlreadyActive"]
