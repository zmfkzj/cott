import os

from real.toolong.model_types import Compression, Compression_Bzip2, Compression_Gzip, Compression_Uncompressed


def detect_compression(name: str) -> Compression:
    base, ext = os.path.splitext(name)
    while True:
        lowered = ext.lower()
        if lowered == ".svgz":
            replacement = ".svg.gz"
        elif lowered in (".tgz", ".taz", ".tz"):
            replacement = ".tar.gz"
        elif lowered == ".tbz2":
            replacement = ".tar.bz2"
        elif lowered == ".txz":
            replacement = ".tar.xz"
        else:
            break
        base, ext = os.path.splitext(base + replacement)
    if ext == ".gz":
        return Compression_Gzip()
    if ext == ".bz2":
        return Compression_Bzip2()
    return Compression_Uncompressed()
