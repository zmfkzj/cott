from __future__ import annotations

from collections.abc import AsyncIterator


async def async_lines(values: AsyncIterator[str]) -> AsyncIterator[str]:
    return values
