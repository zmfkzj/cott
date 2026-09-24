from collections.abc import AsyncGenerator
from typing import Any


async def echo_async(values: AsyncGenerator[Any, object]) -> AsyncGenerator[Any, object]:
    return values
