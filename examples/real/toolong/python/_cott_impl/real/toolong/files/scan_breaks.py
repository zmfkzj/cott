import os
from typing import Final, Literal

from cott_runtime import CottContractViolation, Ok, Opaque, Some, U64, _cott_fixture_read
from real.toolong.files import decompress
from real.toolong.model_types import Compression_Uncompressed, LogSource

_CHUNK: Final[int] = 65536


def _find_breaks(data: bytes, start: int, stop: int, chunk_offset: int, found: list[int]) -> None:
    # find returns indexes into data; chunk_offset is the source offset of data[0].
    index = data.find(b"\n", start, stop)
    while index != -1:
        found.append(chunk_offset + index)
        index = data.find(b"\n", index + 1, stop)


def _fixture_content(source: LogSource) -> bytes:
    try:
        content = _cott_fixture_read(source.path)
    except (CottContractViolation, OSError):
        return b""
    if isinstance(source.compression, Compression_Uncompressed):
        return content
    # A failed fixture read/decompression yields no content, as in read_span.
    try:
        result = decompress(content, source.compression)
    except Exception:
        return b""
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
            position = start
            while position < stop:
                try:
                    data = os.pread(descriptor.value, min(_CHUNK, stop - position), position)
                except OSError:
                    break
                if not data:
                    break
                _find_breaks(data, 0, len(data), position, found)
                position += len(data)
        else:
            content = _fixture_content(source)
            _find_breaks(content, start, stop, 0, found)
    return Opaque(tag="file_breaks", value=tuple(found))
