from __future__ import annotations

from typing import TypeVar
from curriculum.trait_protocol_types import Summarizable

T = TypeVar("T", bound=Summarizable)

def format_summary(item: T) -> str:
    return item.summary()
