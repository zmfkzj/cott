from pathlib import Path

from cott_runtime import CottList, Option, Some


def config_search_paths(explicit: Option[Path], cwd: Path, user_config_dir: Path, home: Path) -> CottList[Path]:
    paths: list[Path] = []
    if isinstance(explicit, Some):
        paths.append(explicit.value)
    paths.extend([cwd / "harlequin.toml", cwd / ".harlequin.toml", cwd / "pyproject.toml"])
    paths.extend([user_config_dir / "harlequin.toml", user_config_dir / ".harlequin.toml", user_config_dir / "config.toml"])
    paths.extend([home / "harlequin.toml", home / ".harlequin.toml", home / "pyproject.toml"])
    return CottList(values=paths)
