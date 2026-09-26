import os
import pathlib
from typing import Final

from cott_runtime import F64, Err, Nothing, Ok, Option, Result, Some
from real.harlequin.support import load_buffer_cache
from real.harlequin.support_types import BufferCache, CacheError, CacheError_Unreadable

_STALE_SECONDS: Final[float] = 180.0


def _unreadable(path: pathlib.Path, error: OSError) -> Err[CacheError]:
    return Err(error=CacheError_Unreadable(path=path, message=str(error)))


def _candidates(cache_dir: pathlib.Path, prefix: str) -> list[tuple[float, pathlib.Path]]:
    found: list[tuple[float, pathlib.Path]] = []
    for entry in cache_dir.iterdir():
        if not (entry.name.startswith(prefix) and entry.name.endswith(".json")):
            continue
        try:
            if entry.is_file():
                found.append((entry.stat().st_mtime, entry))
        except OSError:
            continue
    found.sort(key=lambda item: item[0], reverse=True)
    return found


def adopt_recovery(cache_dir: pathlib.Path, now_epoch_seconds: F64) -> Result[Option[BufferCache], CacheError]:
    """Claim the first eligible recovery before loading it; never retry corrupt caches."""
    try:
        recovered = _candidates(cache_dir, "recovered-")
        stale = [item for item in _candidates(cache_dir, "recovery-") if item[0] < now_epoch_seconds - _STALE_SECONDS]
    except (FileNotFoundError, NotADirectoryError):
        return Ok(value=Nothing())
    except OSError as error:
        return _unreadable(cache_dir, error)
    ordered = recovered + stale
    if not ordered:
        return Ok(value=Nothing())
    candidate = ordered[0][1]
    replayed = candidate.with_name(candidate.name + ".replayed")
    try:
        os.replace(candidate, replayed)
    except OSError as error:
        return _unreadable(candidate, error)
    loaded = load_buffer_cache(replayed)
    if isinstance(loaded, Ok):
        cache = loaded.value
        if isinstance(cache, Some):
            for buffer in cache.value.buffers:
                if buffer.text.strip():
                    return Ok(value=cache)
        return Ok(value=Nothing())
    else:
        return loaded
