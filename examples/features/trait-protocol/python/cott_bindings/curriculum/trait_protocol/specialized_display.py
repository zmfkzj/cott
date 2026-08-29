from __future__ import annotations

from curriculum.trait_protocol import SimpleTask


async def specialized_display(receiver: SimpleTask) -> str:
    return f"specialized: {receiver.title}"
