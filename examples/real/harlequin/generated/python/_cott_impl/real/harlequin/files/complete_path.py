import os
from pathlib import Path

from cott_runtime import CottList

from real.harlequin.files import expand_path


def complete_path(text: str, home: Path, cwd: Path) -> CottList[str]:
    slash = text.rfind("/")
    dir_part = text[: slash + 1] if slash >= 0 else ""
    prefix = text[slash + 1 :]
    directory = expand_path(dir_part, home, cwd)
    try:
        entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
    except OSError:
        return CottList(values=[])
    show_hidden = prefix.startswith(".")
    results: list[str] = []
    for entry in entries:
        name = entry.name
        if not name.startswith(prefix):
            continue
        if name.startswith(".") and not show_hidden:
            continue
        try:
            is_dir = entry.is_dir()
        except OSError:
            is_dir = False
        results.append(dir_part + name + ("/" if is_dir else ""))
    return CottList(values=results)
