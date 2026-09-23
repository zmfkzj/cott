from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_BatchReadFailed, MediaError_InvalidInput

_MAX_URLS: Final[int] = 100000


def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    prefixes: list[str] = []
    for prefix in comment_prefixes:
        if len(prefix) == 0:
            return Err(error=MediaError_InvalidInput(message="comment prefix must be non-empty"))
        prefixes.append(prefix)
    try:
        raw: bytes = Path(path).read_bytes()
    except FileNotFoundError:
        return Err(error=MediaError_BatchReadFailed(path=path, message="batch file not found"))
    except PermissionError:
        return Err(error=MediaError_BatchReadFailed(path=path, message="permission denied reading batch file"))
    except IsADirectoryError:
        return Err(error=MediaError_BatchReadFailed(path=path, message="batch path is a directory"))
    except OSError:
        return Err(error=MediaError_BatchReadFailed(path=path, message="cannot read batch file"))
    try:
        text: str = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return Err(error=MediaError_BatchReadFailed(path=path, message="batch file is not valid UTF-8"))
    prefix_tuple: tuple[str, ...] = tuple(prefixes)
    urls: list[str] = []
    for line in text.splitlines():
        entry: str = line.strip()
        if len(entry) == 0 or entry.startswith(prefix_tuple):
            continue
        if len(urls) >= _MAX_URLS:
            return Err(error=MediaError_InvalidInput(message="batch file exceeds 100000 URLs"))
        urls.append(entry)
    return Ok(value=CottList(values=urls))
