from typing import Literal

from cott_runtime import U64, Opaque
from real.toolong.model_types import FileIndex


def start_file_index(size: U64) -> FileIndex:
    offsets: tuple[int, ...] = (size,) if size > 0 else ()
    breaks: Opaque[Literal["file_breaks"]] = Opaque(tag="file_breaks", value=offsets)
    return FileIndex(breaks=breaks, scan_start=size, scanned_size=0)
