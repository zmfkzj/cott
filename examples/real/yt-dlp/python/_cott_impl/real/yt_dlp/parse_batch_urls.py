from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidInput


def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    """Parse trimmed batch URLs while ignoring configured comment prefixes."""
    for prefix in comment_prefixes:
        if prefix == "":
            return Err(error=MediaError_InvalidInput(message="comment prefixes must be nonempty"))

    urls: list[str] = []
    for line in batch.splitlines():
        left_trimmed = line.lstrip()
        if left_trimmed == "":
            continue
        if any(left_trimmed.startswith(prefix) for prefix in comment_prefixes):
            continue
        urls.append(line.strip())

    return Ok(value=CottList(values=tuple(urls)))
