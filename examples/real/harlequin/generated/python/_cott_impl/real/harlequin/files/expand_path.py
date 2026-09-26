import os
from pathlib import Path


def expand_path(text: str, home: Path, cwd: Path) -> Path:
    stripped = text.strip()
    if stripped == "":
        return Path(os.path.normpath(cwd))
    if stripped == "~":
        candidate = home
    elif stripped.startswith("~/"):
        candidate = home / stripped[2:]
    else:
        candidate = Path(stripped)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return Path(os.path.normpath(candidate))
