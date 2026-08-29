from __future__ import annotations

from cott_runtime import Dyn
from curriculum.trait_protocol import TaskView


async def inspect_dyn(item: Dyn[TaskView[str]]) -> str:
    return await item.value.summary()
