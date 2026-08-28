from __future__ import annotations

from cott_runtime import Dyn
from curriculum.trait_protocol import TaskView


def inspect_dyn(item: Dyn[TaskView]) -> str:
    return item.value.summary()
