import itertools
import typing

from cott_runtime import Opaque, U64
from real.toolong.model_types import FileIndex


def add_scanned_breaks(index: FileIndex, breaks: Opaque[typing.Literal["file_breaks"]], position: U64) -> FileIndex:
    existing = typing.cast(tuple[int, ...], index.breaks.unwrap())
    added = typing.cast(tuple[int, ...], breaks.unwrap())
    combined = tuple(sorted(itertools.chain(existing, added)))
    return FileIndex(breaks=Opaque(tag="file_breaks", value=combined), scan_start=position, scanned_size=index.scanned_size)
