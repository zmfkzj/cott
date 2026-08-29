from pathlib import Path

from cott_runtime import Option, Some


def resolve_state_path(platform_name: str, home: Path, app_data: Option[str], xdg_data_home: Option[str]) -> Path:
    if platform_name == "nt":
        root = Path(app_data.value) if isinstance(app_data, Some) else home / "AppData" / "Roaming"
        return root / "Frogmouth" / "state.json"
    if platform_name == "darwin":
        return home / "Library" / "Application Support" / "Frogmouth" / "state.json"
    root = Path(xdg_data_home.value) if isinstance(xdg_data_home, Some) else home / ".local" / "share"
    return root / "frogmouth" / "state.json"
