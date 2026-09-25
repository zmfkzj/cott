from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput

_MAX_URLS: Final[int] = 100000


def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    prefixes: list[str] = []
    for prefix in comment_prefixes:
        if len(prefix) == 0:
            return Err(error=MediaError_InvalidInput(message="comment prefix must be non-empty"))
        prefixes.append(prefix)
    text: str = batch[1:] if batch.startswith("\ufeff") else batch
    normalized: str = text.replace("\r\n", "\n").replace("\r", "\n")
    urls: list[str] = []
    for raw_line in normalized.split("\n"):
        line: str = raw_line.strip()
        if len(line) == 0:
            continue
        if any(line.startswith(p) for p in prefixes):
            continue
        if len(urls) >= _MAX_URLS:
            return Err(error=MediaError_InvalidInput(message="batch file contains more than 100000 URLs"))
        urls.append(line)
    return Ok(value=CottList(values=urls))
