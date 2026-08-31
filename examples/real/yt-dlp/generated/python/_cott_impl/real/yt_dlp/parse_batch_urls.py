from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput


def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    prefix: str
    for prefix in comment_prefixes:
        if prefix == "":
            return Err(error=MediaError_InvalidInput(message="comment prefixes must not be empty"))

    urls: list[str] = []
    line: str
    for line in batch.splitlines():
        url: str = line.strip()
        if url == "":
            continue

        is_comment: bool = False
        for prefix in comment_prefixes:
            if url.startswith(prefix):
                is_comment = True
                break
        if is_comment:
            continue

        urls.append(url)

    return Ok(value=CottList(values=tuple(urls)))
