from pathlib import Path

from cott_runtime import FrozenMap

from real.harlequin.history_types import HarlequinPaths


def _xdg(environment: FrozenMap[str, str], name: str, default: Path) -> Path:
    value = environment.get(name)
    if value is None or value.strip() == "":
        return default
    return Path(value)


def harlequin_paths(platform: str, home: Path, environment: FrozenMap[str, str]) -> HarlequinPaths:
    if platform == "darwin":
        support = home / "Library" / "Application Support" / "harlequin"
        config_dir = support
        cache_dir = home / "Library" / "Caches" / "harlequin"
        state_dir = support
        data_dir = support
        log_dir = home / "Library" / "Logs" / "harlequin"
    else:
        config_dir = _xdg(environment, "XDG_CONFIG_HOME", home / ".config") / "harlequin"
        cache_dir = _xdg(environment, "XDG_CACHE_HOME", home / ".cache") / "harlequin"
        state_dir = _xdg(environment, "XDG_STATE_HOME", home / ".local" / "state") / "harlequin"
        data_dir = _xdg(environment, "XDG_DATA_HOME", home / ".local" / "share") / "harlequin"
        log_dir = state_dir / "log"
    return HarlequinPaths(
        config_dir=config_dir,
        cache_dir=cache_dir,
        state_dir=state_dir,
        log_dir=log_dir,
        data_dir=data_dir,
        query_log=state_dir / "history.db",
        buffer_cache=cache_dir / "buffers-1.json",
        crash_dir=log_dir,
    )
