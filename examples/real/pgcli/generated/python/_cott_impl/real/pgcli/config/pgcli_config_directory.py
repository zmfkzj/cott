from cott_runtime import Option, Some


def _expand_home(value: str, home: str) -> str:
    if not value.startswith("~"):
        return value
    slash = value.find("/", 1)
    end = len(value) if slash < 0 else slash
    if end != 1:
        return value
    return (home.rstrip("/") + value[end:]) or "/"


def pgcli_config_directory(xdg_config_home: Option[str], home: str) -> str:
    if isinstance(xdg_config_home, Some):
        return _expand_home(xdg_config_home.value, home) + "/pgcli/"
    return home + "/.config/pgcli/"
