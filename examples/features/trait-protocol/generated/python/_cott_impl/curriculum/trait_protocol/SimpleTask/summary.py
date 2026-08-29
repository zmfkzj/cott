from __future__ import annotations

from curriculum.trait_protocol import SimpleTask


async def _cott_impl_SimpleTask_summary(self: SimpleTask) -> str:
    return self.title
