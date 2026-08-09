from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class ZeroDivisor:
    pass

DivideError: TypeAlias = Union[ZeroDivisor]

__all__ = ["DivideError", "ZeroDivisor"]
