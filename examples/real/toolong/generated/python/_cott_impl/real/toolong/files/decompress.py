import bz2
import gzip

import cott_runtime
from real.toolong.files_types import DecompressError, DecompressError_Corrupt
from real.toolong.model_types import Compression, Compression_Bzip2, Compression_Gzip


def decompress(data: bytes, compression: Compression) -> cott_runtime.Result[bytes, DecompressError]:
    try:
        if isinstance(compression, Compression_Gzip):
            content = gzip.decompress(data)
        elif isinstance(compression, Compression_Bzip2):
            content = bz2.decompress(data)
        else:
            content = data
    except Exception as error:
        return cott_runtime.Err(error=DecompressError_Corrupt(message=str(error)))
    return cott_runtime.Ok(value=content)
