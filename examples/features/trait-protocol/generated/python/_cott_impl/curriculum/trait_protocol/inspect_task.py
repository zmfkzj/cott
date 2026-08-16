from __future__ import annotations

from typing import TypeVar
from curriculum.trait_protocol_types import _cott__cott_inspect_task_T_Bounds

T = TypeVar("T", bound=_cott__cott_inspect_task_T_Bounds)

def inspect_task(item: T) -> str:
    return f"[{item.priority_level()}] {item.summary()}"
