from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class High:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Normal:
    pass

Priority: TypeAlias = Union[High, Normal]

__all__ = ["Priority", "High", "Normal"]
