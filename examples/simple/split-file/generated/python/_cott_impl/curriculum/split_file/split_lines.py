from cott_runtime import CottList, Err, I64, Ok, Result
from curriculum.split_file_types import SplitFileError, SplitFileError_InvalidChunkSize, SplitFileError_OutputLimitExceeded, SplitRequest


def split_lines(request: SplitRequest) -> Result[CottList[CottList[str]], SplitFileError]:
    chunk_size: I64 = request.chunk_size
    if chunk_size < 1 or chunk_size > 10_000:
        return Err(error=SplitFileError_InvalidChunkSize())

    lines: CottList[str] = request.lines
    if (len(lines) + chunk_size - 1) // chunk_size > 10_000:
        return Err(error=SplitFileError_OutputLimitExceeded())

    chunks: list[CottList[str]] = []
    for start in range(0, len(lines), chunk_size):
        chunks.append(CottList(values=lines[start : start + chunk_size]))
    return Ok(value=CottList(values=chunks))
