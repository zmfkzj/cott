from __future__ import annotations

from pathlib import Path
from cott_runtime import Ok, Result
from curriculum.system_effects_types import SystemError

def inspect_file_path(target: Path) -> Result[Path, SystemError]:
    return Ok(value=target)
