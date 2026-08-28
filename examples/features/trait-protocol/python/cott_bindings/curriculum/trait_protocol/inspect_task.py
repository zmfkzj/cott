from __future__ import annotations

from typing import TypeVar
from curriculum.trait_protocol_types import TaskView

T = TypeVar("T", bound=TaskView)

def inspect_task(item: T) -> str:
    return f"[{item.priority_level()}] {item.summary()}"
