from __future__ import annotations

from cott_runtime import I32
from curriculum.trait_protocol import SimpleTask


async def _cott_impl_SimpleTask_priority_level(self: SimpleTask) -> I32:
    return self.urgency
