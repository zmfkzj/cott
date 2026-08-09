from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class Underflow:
    pass

CountError: TypeAlias = Union[Underflow]

__all__ = ["CountError", "Underflow"]
