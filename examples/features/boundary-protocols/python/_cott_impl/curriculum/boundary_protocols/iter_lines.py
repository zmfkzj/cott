from collections.abc import Iterator

from curriculum.boundary_protocols_types import TextBuffer


def _strip_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\n", "\r")):
        return line[:-1]
    return line


def iter_lines(buffer: TextBuffer) -> Iterator[str]:
    return (_strip_ending(line) for line in buffer)
