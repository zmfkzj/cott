from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class ProfileSummary:
    display_name: str
    tag_count: int
    has_nickname: bool

__all__ = ["ProfileSummary"]
