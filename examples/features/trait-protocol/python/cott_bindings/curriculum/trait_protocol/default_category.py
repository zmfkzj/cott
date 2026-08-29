from __future__ import annotations

from typing import TypeVar

from curriculum.trait_protocol_types import TaskView


T = TypeVar("T")


async def default_category(receiver: TaskView[T]) -> str:
    return "default"
