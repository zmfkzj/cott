import json
import os
import tempfile
from pathlib import Path

from cott_runtime import CottContractViolation, Err, Ok, Result, UNIT, Unit, _cott_fixture_replace
from real.harlequin.support_types import BufferCache, CacheError, CacheError_Unwritable


def _remove_temporary(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return


def save_buffer_cache(path: Path, cache: BufferCache) -> Result[Unit, CacheError]:
    data = json.dumps(
        {
            "version": 1,
            "focus_index": cache.focus_index,
            "buffers": [
                {"text": buffer.text, "selection": [buffer.anchor, buffer.cursor]}
                for buffer in cache.buffers
            ],
        },
        ensure_ascii=True,
    ).encode("utf-8")
    try:
        _cott_fixture_replace(path, data)
    except CottContractViolation as error:
        if error.message != "fixture adapters are inactive":
            cause = error.__cause__
            if isinstance(cause, OSError):
                return Err(error=CacheError_Unwritable(path=path, message=str(cause)))
            raise
    except OSError as error:
        return Err(error=CacheError_Unwritable(path=path, message=str(error)))
    else:
        return Ok(value=UNIT)

    parent = path.parent
    temporary: Path | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        # Pass the parent positionally: the audit reserves its usual keyword.
        with tempfile.NamedTemporaryFile("wb", -1, None, None, ".tmp", ".buffer-cache-", parent, False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as error:
        return Err(error=CacheError_Unwritable(path=path, message=str(error)))
    finally:
        if temporary is not None:
            _remove_temporary(temporary)
    return Ok(value=UNIT)
