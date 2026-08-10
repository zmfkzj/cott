from cott_runtime import CottList, Err, I64, Ok, Result, UNIT, Unit
from curriculum.split_file_types import SplitFileError, SplitFileError_InvalidChunkSize, SplitFileError_OutputLimitExceeded, SplitRequest


def validate_split_request(request: SplitRequest) -> Result[Unit, SplitFileError]:
    chunk_size: I64 = request.chunk_size
    if chunk_size < 1 or chunk_size > 10_000:
        return Err(error=SplitFileError_InvalidChunkSize())

    lines: CottList[str] = request.lines
    if (len(lines) + chunk_size - 1) // chunk_size > 10_000:
        return Err(error=SplitFileError_OutputLimitExceeded())

    return Ok(value=UNIT)
