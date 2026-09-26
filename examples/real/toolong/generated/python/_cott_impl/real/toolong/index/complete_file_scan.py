from cott_runtime import U64
from real.toolong.model_types import FileIndex


def complete_file_scan(index: FileIndex, size: U64, position: U64) -> FileIndex:
    return FileIndex(breaks=index.breaks, scan_start=position, scanned_size=max(index.scanned_size, size))
