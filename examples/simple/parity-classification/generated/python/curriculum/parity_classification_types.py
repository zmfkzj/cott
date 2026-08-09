from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class Even:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Odd:
    pass

Parity: TypeAlias = Union[Even, Odd]

__all__ = ["Parity", "Even", "Odd"]
