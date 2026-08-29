from __future__ import annotations

import asyncio
import io
from collections.abc import AsyncGenerator
from typing import Any

from cott_runtime import Ok
from curriculum.boundary_protocols import (
    adapt_unknown,
    async_lines,
    echo_async,
    echo_values,
    extract_handle_id,
    iter_lines,
    wrap_handle,
)
from curriculum.boundary_protocols_types import TextBuffer


class _ProtocolValues(AsyncGenerator[Any, object]):
    def __init__(self, values: tuple[Any, ...]) -> None:
        self._values = values
        self._position = 0
        self._closed = False

    async def __anext__(self) -> Any:
        if self._closed or self._position == len(self._values):
            raise StopAsyncIteration
        value = self._values[self._position]
        self._position += 1
        return value

    async def asend(self, value: object) -> Any:
        return await self.__anext__()

    async def athrow(
        self,
        typ: object,
        val: object | None = None,
        tb: object | None = None,
    ) -> Any:
        self._closed = True
        raise StopAsyncIteration

    async def aclose(self) -> None:
        self._closed = True

async def main() -> None:
    result = wrap_handle(raw_id=42)
    if isinstance(result, Ok):
        if result.value.raw_id != 42:
            raise RuntimeError("wrap_handle did not retain the raw ID")
        print(f"Wrapped raw id: {result.value.raw_id}")
        print(f"Extracted handle id: {extract_handle_id(bundle=result.value)}")

    unknown = adapt_unknown(value={"label": "explicit"})
    if not isinstance(unknown, dict):
        raise RuntimeError("expected a dictionary")
    label = unknown.get("label")
    if not isinstance(label, str):
        raise RuntimeError("expected a string label")
    print(f"Narrowed unknown: {label}")

    buffer: TextBuffer = io.StringIO("alpha\nbeta\n")
    print(f"Lines: {','.join(iter_lines(buffer=buffer))}")

    values = echo_values(values=iter(("first", 7)))
    generated = [next(values), values.send(object())]
    try:
        next(values)
    except StopIteration as complete:
        print(f"Generator return count: {complete.value}")
    print(f"Generated values: {','.join(map(str, generated))}")

    lines = await async_lines(values=_ProtocolValues(("gamma", "delta")))
    print(f"Async lines: {await lines.__anext__()},{await lines.__anext__()}")
    try:
        await lines.__anext__()
    except StopAsyncIteration:
        print("Async iterator completed")

    async_values = await echo_async(values=_ProtocolValues(("first", 7)))
    generated_async = [await async_values.__anext__(), await async_values.asend(object())]
    print(f"Async generated values: {','.join(map(str, generated_async))}")
    try:
        await async_values.__anext__()
    except StopAsyncIteration:
        print("Async generator completed")
    await async_values.aclose()
    await async_values.aclose()
    print("Async generator closed twice")


asyncio.run(main())
