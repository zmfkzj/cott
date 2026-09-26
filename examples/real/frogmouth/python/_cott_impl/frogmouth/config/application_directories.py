from typing import Final

from cott_runtime import Nothing, Some

from frogmouth.config_types import AppDirectories

_SUFFIX: Final[str] = "/textualize/frogmouth"


def _directory(home: str, xdg: Some[str] | Nothing, fallback: str) -> str:
    base = home + fallback
    if isinstance(xdg, Some) and xdg.value.startswith("/"):
        base = xdg.value
    stripped = base.rstrip("/")
    return (stripped if stripped else "/") + _SUFFIX


def application_directories(home: str, xdg_config_home: Some[str] | Nothing, xdg_data_home: Some[str] | Nothing) -> AppDirectories:
    return AppDirectories(
        config_directory=_directory(home, xdg_config_home, "/.config"),
        data_directory=_directory(home, xdg_data_home, "/.local/share"),
    )
