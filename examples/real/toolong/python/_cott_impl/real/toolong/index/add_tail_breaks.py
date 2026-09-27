import typing

from cott_runtime import Opaque, U64
from real.toolong.model_types import FileIndex


def add_tail_breaks(index: FileIndex, breaks: Opaque[typing.Literal["file_breaks"]], size: U64) -> FileIndex:
    existing = typing.cast(tuple[int, ...], index.breaks.unwrap())
    added = typing.cast(tuple[int, ...], breaks.unwrap())
    return FileIndex(
        breaks=Opaque(tag="file_breaks", value=existing + added),
        scan_start=index.scan_start,
        scanned_size=max(index.scanned_size, size),
    )
