import bz2
import gzip

from cott_runtime import Err, Ok, Result
from real.toolong.files_types import DecompressError, DecompressError_Corrupt
from real.toolong.model_types import Compression, Compression_Bzip2, Compression_Gzip


def decompress(data: bytes, compression: Compression) -> Result[bytes, DecompressError]:
    try:
        if isinstance(compression, Compression_Gzip):
            return Ok(value=gzip.decompress(data))
        elif isinstance(compression, Compression_Bzip2):
            return Ok(value=bz2.decompress(data))
        else:
            return Ok(value=data)
    except Exception as error:
        return Err(error=DecompressError_Corrupt(message=str(error)))
