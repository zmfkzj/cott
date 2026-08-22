from __future__ import annotations

from collections.abc import Generator, Iterator
from typing import Any

from cott_runtime import U64


def echo_values(values: Iterator[Any]) -> Generator[Any, object, U64]:
    count = 0
    for value in values:
        count += 1
        yield value
    return count
