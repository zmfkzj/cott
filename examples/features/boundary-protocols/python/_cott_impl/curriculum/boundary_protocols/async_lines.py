from collections.abc import AsyncIterator


async def async_lines(values: AsyncIterator[str]) -> AsyncIterator[str]:
    return values
