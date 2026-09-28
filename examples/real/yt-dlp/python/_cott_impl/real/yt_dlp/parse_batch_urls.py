from typing import Final

import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput

_MAX_URLS: Final[int] = 100000


def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    for prefix in comment_prefixes:
        if prefix == "":
            return cott_runtime.Err(error=MediaError_InvalidInput(message="comment prefix must be non-empty"))

    text: str = batch[1:] if batch.startswith("\ufeff") else batch
    normalized: str = text.replace("\r\n", "\n").replace("\r", "\n")
    urls: list[str] = []
    for raw_line in normalized.split("\n"):
        line: str = raw_line.strip()
        if not line or any(line.startswith(prefix) for prefix in comment_prefixes):
            continue
        if len(urls) >= _MAX_URLS:
            return cott_runtime.Err(error=MediaError_InvalidInput(message="batch file contains more than 100000 URLs"))
        urls.append(line)
    return cott_runtime.Ok(value=CottList(values=urls))
