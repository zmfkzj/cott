import os
from typing import Final, Literal

from cott_runtime import U64, Ok, Opaque, Some, _cott_fixture_read
from real.toolong.files import decompress
from real.toolong.model_types import Compression_Uncompressed, LogSource

_CHUNK: Final[int] = 65536


def _find_breaks(data: bytes, base: int, out: list[int]) -> None:
    index = data.find(b"\n")
    while index != -1:
        out.append(base + index)
        index = data.find(b"\n", index + 1)


def _fixture_content(source: LogSource) -> bytes:
    try:
        content = _cott_fixture_read(source.path)
    except Exception:
        return b""
    if isinstance(source.compression, Compression_Uncompressed):
        return content
    result = decompress(content, source.compression)
    if isinstance(result, Ok):
        return result.value
    else:
        return b""


def scan_breaks(source: LogSource, start: U64, end: U64) -> Opaque[Literal["file_breaks"]]:
    stop = min(end, source.size)
    found: list[int] = []
    if start < stop:
        descriptor = source.descriptor
        if isinstance(descriptor, Some):
            fd = descriptor.value
            position = start
            while position < stop:
                try:
                    data = os.pread(fd, min(_CHUNK, stop - position), position)
                except OSError:
                    break
                if not data:
                    break
                _find_breaks(data, position, found)
                position += len(data)
        else:
            content = _fixture_content(source)
            _find_breaks(content[start:stop], start, found)
    return Opaque(tag="file_breaks", value=tuple(found))
