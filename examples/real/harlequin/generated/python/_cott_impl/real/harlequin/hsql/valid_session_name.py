from typing import Final

_ALLOWED: Final[str] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"


def valid_session_name(name: str) -> bool:
    if len(name) < 1 or len(name) > 64:
        return False
    for ch in name:
        if ch not in _ALLOWED:
            return False
    return True
