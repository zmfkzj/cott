from typing import Literal

from cott_runtime import Opaque, U64
from real.toolong.model_types import FileIndex


def start_file_index(size: U64) -> FileIndex:
    breaks: Opaque[Literal["file_breaks"]] = Opaque(
        tag="file_breaks", value=(size,) if size > 0 else ()
    )
    return FileIndex(breaks=breaks, scan_start=size, scanned_size=0)
