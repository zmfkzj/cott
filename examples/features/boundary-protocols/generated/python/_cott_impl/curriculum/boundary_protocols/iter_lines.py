from __future__ import annotations

from collections.abc import Iterator

from curriculum.boundary_protocols_types import TextBuffer


def iter_lines(buffer: TextBuffer) -> Iterator[str]:
    return (line.rstrip("\r\n") for line in buffer)
