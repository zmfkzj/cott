from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput


def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    prefixes: list[str] = []
    for prefix in comment_prefixes:
        if len(prefix) == 0:
            return Err(error=MediaError_InvalidInput(message="comment prefix must be non-empty"))
        prefixes.append(prefix)
    text: str = batch[1:] if batch.startswith("\ufeff") else batch
    urls: list[str] = []
    for raw_line in text.splitlines():
        line: str = raw_line.strip()
        if len(line) == 0:
            continue
        if any(line.startswith(p) for p in prefixes):
            continue
        urls.append(line)
    return Ok(value=CottList(values=urls))
