from typing import Final

from cott_runtime import Opaque, U64
from real.toolong.files import read_span
from real.toolong.files_types import TailChunk
from real.toolong.model_types import ByteSpan, LogSource

_CHUNK: Final[int] = 65536
_MAX_U64: Final[int] = 18446744073709551615


def poll_source(source: LogSource, position: U64) -> TailChunk:
    data = read_span(source, ByteSpan(start=position, end=min(position + _CHUNK, _MAX_U64)))
    breaks: list[int] = []
    index = data.find(b"\n")
    while index != -1:
        breaks.append(position + index)
        index = data.find(b"\n", index + 1)
    return TailChunk(position=position + len(data), breaks=Opaque(tag="file_breaks", value=tuple(breaks)))
