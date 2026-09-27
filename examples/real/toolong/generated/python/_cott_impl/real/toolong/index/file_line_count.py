from typing import cast

from cott_runtime import U64
from real.toolong.model_types import FileIndex


def file_line_count(index: FileIndex) -> U64:
    breaks = cast(tuple[int, ...], index.breaks.unwrap())
    return max(len(breaks), 1)
