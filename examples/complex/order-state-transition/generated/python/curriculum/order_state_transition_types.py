from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class Pending:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Paid:
    receipt: str

OrderState: TypeAlias = Union[Pending, Paid]

@dataclass(frozen=True, slots=True, kw_only=True)
class NotPending:
    pass

TransitionError: TypeAlias = Union[NotPending]

__all__ = ["OrderState", "Pending", "Paid", "TransitionError", "NotPending"]
