from __future__ import annotations

from curriculum.trait_protocol import SimpleTask
from curriculum.trait_protocol_types import TaskLifecycle_Completed


async def _cott_impl_SimpleTask_complete(self: SimpleTask) -> bool:
    self.lifecycle = TaskLifecycle_Completed()
    self.completion_count += 1
    return True
