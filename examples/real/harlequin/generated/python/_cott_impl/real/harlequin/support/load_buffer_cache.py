import json
from pathlib import Path
from typing import cast

from cott_runtime import CottContractViolation, CottList, Err, Nothing, Ok, Option, Result, Some, _cott_fixture_read
from real.harlequin.support_types import BufferCache, BufferState, CacheError, CacheError_Unreadable


def _parse_cache(data: bytes) -> Option[BufferCache]:
    try:
        raw = cast(object, json.loads(data.decode("utf-8")))
    except (UnicodeDecodeError, ValueError):
        return Nothing()
    if not isinstance(raw, dict):
        return Nothing()
    document = cast(dict[str, object], raw)
    version = document.get("version")
    focus = document.get("focus_index")
    items = document.get("buffers")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        return Nothing()
    if not isinstance(focus, int) or isinstance(focus, bool) or not isinstance(items, list):
        return Nothing()
    buffers: list[BufferState] = []
    for item in cast(list[object], items):
        if not isinstance(item, dict):
            return Nothing()
        entry = cast(dict[str, object], item)
        text = entry.get("text")
        selection = entry.get("selection")
        if not isinstance(text, str) or not isinstance(selection, list):
            return Nothing()
        pair = cast(list[object], selection)
        if len(pair) != 2:
            return Nothing()
        anchor = pair[0]
        cursor = pair[1]
        if not isinstance(anchor, int) or isinstance(anchor, bool):
            return Nothing()
        if not isinstance(cursor, int) or isinstance(cursor, bool):
            return Nothing()
        length = len(text)
        buffers.append(BufferState(text=text, anchor=max(0, min(anchor, length)), cursor=max(0, min(cursor, length))))
    return Some(value=BufferCache(focus_index=max(0, min(focus, len(buffers) - 1)), buffers=CottList(values=buffers)))


def load_buffer_cache(path: Path) -> Result[Option[BufferCache], CacheError]:
    """Load version-one caches, ignoring invalid shapes and clamping positions."""
    try:
        data = _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message == "fixture adapters are inactive":
            try:
                data = path.read_bytes()
            except FileNotFoundError:
                return Ok(value=Nothing())
            except OSError as error:
                return Err(error=CacheError_Unreadable(path=path, message=str(error)))
        else:
            cause = violation.__cause__
            if isinstance(cause, FileNotFoundError):
                return Ok(value=Nothing())
            if isinstance(cause, OSError):
                return Err(error=CacheError_Unreadable(path=path, message=str(cause)))
            raise
    except FileNotFoundError:
        return Ok(value=Nothing())
    except OSError as error:
        return Err(error=CacheError_Unreadable(path=path, message=str(error)))
    return Ok(value=_parse_cache(data))
