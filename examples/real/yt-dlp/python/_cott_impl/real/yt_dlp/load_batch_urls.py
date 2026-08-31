from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result, _cott_fixture_read
from real.yt_dlp import parse_batch_urls
from real.yt_dlp_types import MediaError, MediaError_BatchReadFailed


def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    batch: str = _cott_fixture_read(path).decode("utf-8-sig")
    match parse_batch_urls(batch, comment_prefixes):
        case Ok(value=urls):
            if len(urls) > 100000:
                return Err(
                    error=MediaError_BatchReadFailed(
                        path=path,
                        message="batch file contains more than 100000 URLs",
                    )
                )
            return Ok(value=urls)
        case Err(error=error):
            return Err(error=error)
