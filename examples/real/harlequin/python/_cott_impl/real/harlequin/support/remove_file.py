from pathlib import Path

from cott_runtime import UNIT, Err, Ok, Result, Unit
from real.harlequin.support_types import CacheError, CacheError_Unwritable


def remove_file(path: Path) -> Result[Unit, CacheError]:
    try:
        path.unlink()
    except FileNotFoundError:
        return Ok(value=UNIT)
    except OSError as error:
        return Err(error=CacheError_Unwritable(path=path, message=str(error)))
    return Ok(value=UNIT)
