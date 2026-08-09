from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class AccountId:
    value: int

@dataclass(frozen=True, slots=True, kw_only=True)
class Accepted:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Rejected:
    reason: str

TransferDecision: TypeAlias = Union[Accepted, Rejected]

@dataclass(frozen=True, slots=True, kw_only=True)
class InsufficientFunds:
    pass

TransferError: TypeAlias = Union[InsufficientFunds]

__all__ = ["AccountId", "TransferDecision", "Accepted", "Rejected", "TransferError", "InsufficientFunds"]
