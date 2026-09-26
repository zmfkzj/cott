import os

from real.toolong.model_types import Compression, Compression_Bzip2, Compression_Gzip, Compression_Uncompressed


def _suffix_replacement(ext: str) -> str:
    lowered = ext.lower()
    if lowered == ".svgz":
        return ".svg.gz"
    if lowered == ".tgz" or lowered == ".taz" or lowered == ".tz":
        return ".tar.gz"
    if lowered == ".tbz2":
        return ".tar.bz2"
    if lowered == ".txz":
        return ".tar.xz"
    return ""


def detect_compression(name: str) -> Compression:
    base, ext = os.path.splitext(name)
    replacement = _suffix_replacement(ext)
    while replacement != "":
        base, ext = os.path.splitext(base + replacement)
        replacement = _suffix_replacement(ext)
    if ext == ".gz":
        return Compression_Gzip()
    if ext == ".bz2":
        return Compression_Bzip2()
    return Compression_Uncompressed()
