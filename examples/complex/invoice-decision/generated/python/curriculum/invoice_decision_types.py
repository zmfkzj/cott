from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class Approved:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Rejected:
    reason: str

InvoiceDecision: TypeAlias = Union[Approved, Rejected]

__all__ = ["InvoiceDecision", "Approved", "Rejected"]
